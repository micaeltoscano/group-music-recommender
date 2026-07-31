"""PB-32 — sincronização incremental, concorrente e resiliente."""

from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import sqlalchemy as sa
from httpx import Response
from sqlalchemy import create_engine
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy.orm import sessionmaker

from app.clients import spotify_client
from app.db.base import Base
from app.db.models import (
    User,
    UserMusicLibraryPlaylistState,
    UserMusicLibrarySnapshot,
    UserMusicLibraryTrack,
    UserMusicSnapshot,
    UserPlaylistInventory,
)
from app.services.library_sync_service import (
    LibrarySyncRateLimited,
    _user_sync_lock,
    sync_music_library,
)
from app.services.music_library_service import rebuild_music_library


NOW = datetime(2026, 7, 31, 12, tzinfo=timezone.utc)


@pytest.fixture()
def db(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pb32.sqlite3'}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
    session = factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def _track(track_id: str) -> dict:
    track_id = "".join(character for character in track_id if character.isalnum())
    return {
        "id": track_id,
        "uri": f"spotify:track:{track_id}",
        "name": track_id,
        "artists": [{"id": f"artist-{track_id}", "name": "Artista"}],
    }


def _seed(db, *, built_at: datetime | None = None) -> tuple[int, UserMusicLibrarySnapshot | None]:
    user = User(spotify_id=f"user-{id(db)}", display_name="PB32")
    db.add(user)
    db.flush()
    for time_range in ("short_term", "medium_term", "long_term"):
        db.add(
            UserMusicSnapshot(
                user_id=user.id,
                time_range=time_range,
                top_tracks_json=[_track(f"top-{time_range}")],
                top_artists_json=[],
                fetched_at=NOW,
            )
        )
    db.commit()
    if built_at is None:
        return user.id, None
    db.add(
        UserPlaylistInventory(
            user_id=user.id,
            spotify_playlist_id="PlaylistA",
            access_type="owned",
            tracks_total=1,
            snapshot_id="snap-a",
            verified_at=built_at,
        )
    )
    db.commit()
    snapshot = rebuild_music_library(
        db,
        user.id,
        playlist_tracks_by_id={"PlaylistA": [_track("old-a")]},
        built_at=built_at,
    )
    return user.id, snapshot


def _no_external_calls(monkeypatch) -> None:
    async def fail(*_args, **_kwargs):
        raise AssertionError("cache fresco não pode chamar Spotify")

    monkeypatch.setattr("app.services.library_sync_service.get_or_refresh_snapshot", fail)
    monkeypatch.setattr("app.services.library_sync_service.refresh_playlist_inventory", fail)
    monkeypatch.setattr(spotify_client, "get_valid_access_token", fail)
    monkeypatch.setattr(spotify_client, "get_playlist_tracks", fail)


@pytest.mark.anyio
async def test_ct_pb32_01_cache_fresco_faz_zero_chamadas_spotify(db, monkeypatch):
    user_id, original = _seed(db, built_at=NOW - timedelta(days=1))
    _no_external_calls(monkeypatch)

    result = await sync_music_library(db, user_id, now=NOW)

    assert result.cached is True
    assert result.snapshot.id == original.id


@pytest.mark.anyio
async def test_ct_pb32_02_expiracao_baixa_so_playlist_com_snapshot_alterado(db, monkeypatch):
    user_id, _original = _seed(db, built_at=NOW - timedelta(days=8))
    db.add(
        UserPlaylistInventory(
            user_id=user_id,
            spotify_playlist_id="PlaylistB",
            access_type="owned",
            tracks_total=1,
            snapshot_id="snap-b",
            verified_at=NOW - timedelta(days=8),
        )
    )
    db.commit()
    rebuild_music_library(
        db,
        user_id,
        playlist_tracks_by_id={"PlaylistA": [_track("old-a")], "PlaylistB": [_track("old-b")]},
        built_at=NOW - timedelta(days=8),
    )

    async def top(*_args, **_kwargs):
        return None

    async def inventory(*_args, **_kwargs):
        a = db.query(UserPlaylistInventory).filter_by(spotify_playlist_id="PlaylistA").one()
        b = db.query(UserPlaylistInventory).filter_by(spotify_playlist_id="PlaylistB").one()
        b.snapshot_id = "snap-b-new"
        db.commit()
        return SimpleNamespace(items=(a, b))

    downloaded = []

    async def tracks(_token, playlist_id, *, limit):
        downloaded.append((playlist_id, limit))
        return [_track("new-b")]

    monkeypatch.setattr("app.services.library_sync_service.get_or_refresh_snapshot", top)
    monkeypatch.setattr("app.services.library_sync_service.refresh_playlist_inventory", inventory)
    monkeypatch.setattr(
        spotify_client,
        "get_valid_access_token",
        lambda *_a, **_k: asyncio.sleep(0, result="token"),
    )
    monkeypatch.setattr(spotify_client, "get_playlist_tracks", tracks)

    result = await sync_music_library(db, user_id, now=NOW)

    ids = {row.spotify_track_id for row in result.snapshot.tracks}
    assert downloaded == [("PlaylistB", 50)]
    assert {"olda", "newb"} <= ids
    states = {
        state.spotify_playlist_id: state.playlist_snapshot_id
        for state in result.snapshot.playlist_states
    }
    assert states == {"PlaylistA": "snap-a", "PlaylistB": "snap-b-new"}


@pytest.mark.anyio
async def test_ct_pb32_03_downloads_sao_paginados_sem_n_mais_um_e_concorrencia_um(monkeypatch):
    active = 0
    maximum = 0
    calls = []

    async def page(_token, playlist_id, *, limit, offset):
        nonlocal active, maximum
        active += 1
        maximum = max(maximum, active)
        calls.append((playlist_id, limit, offset))
        await asyncio.sleep(0)
        active -= 1
        count = 50 if offset < 100 else 1
        next_page = f"page-{offset + count}" if offset < 100 else None
        return {
            "items": [
                {"track": _track(f"{playlist_id}-{offset + i}")} for i in range(count)
            ],
            "next": next_page,
        }

    monkeypatch.setattr(spotify_client, "get_playlist_items_page", page)
    from app.services.library_sync_service import _download_changed_playlists

    downloaded, _ = await _download_changed_playlists("token", ["A", "B"])

    assert maximum == 1
    assert len(downloaded["A"]) == len(downloaded["B"]) == 101
    assert calls == [
        ("A", 50, 0),
        ("A", 50, 50),
        ("A", 50, 100),
        ("B", 50, 0),
        ("B", 50, 50),
        ("B", 50, 100),
    ]


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("error", "code", "retry_after"),
    [
        (spotify_client.SpotifyRateLimited(37), "RATE_LIMITED", 37),
        (spotify_client.SpotifyQuotaExceeded(), "QUOTA_EXCEEDED", None),
    ],
)
async def test_ct_pb32_04_falha_preserva_cache_pronto_e_distingue_quota(
    db, monkeypatch, error, code, retry_after
):
    user_id, original = _seed(db, built_at=NOW - timedelta(days=8))

    async def top(*_args, **_kwargs):
        raise error

    monkeypatch.setattr("app.services.library_sync_service.get_or_refresh_snapshot", top)
    result = await sync_music_library(db, user_id, now=NOW)

    assert result.snapshot.id == original.id
    assert result.warning_code == code
    assert result.retry_after == retry_after
    assert db.query(UserMusicLibrarySnapshot).count() == 1
    assert {t.spotify_track_id for t in result.snapshot.tracks} >= {"olda"}


def test_ct_pb32_04_cliente_identifica_payload_de_quota_sem_confundir_403_comum():
    with pytest.raises(spotify_client.SpotifyQuotaExceeded):
        spotify_client._raise_playlist_access_error(
            Response(403, json={"error": {"reason": "QUOTA_EXCEEDED"}})
        )
    with pytest.raises(spotify_client.SpotifyAccessForbidden):
        spotify_client._raise_playlist_access_error(
            Response(403, json={"error": {"message": "Forbidden"}})
        )


@pytest.mark.anyio
async def test_ct_pb32_05_postgres_advisory_lock_e_sempre_liberado():
    statements = []

    class FakePostgresSession:
        def get_bind(self):
            return SimpleNamespace(dialect=SimpleNamespace(name="postgresql"))

        def execute(self, statement, parameters):
            statements.append((str(statement), parameters))

    with pytest.raises(RuntimeError, match="falha controlada"):
        async with _user_sync_lock(FakePostgresSession(), 7):
            raise RuntimeError("falha controlada")

    assert [statement for statement, _parameters in statements] == [
        "SELECT pg_advisory_lock(:namespace, :user_id)",
        "SELECT pg_advisory_unlock(:namespace, :user_id)",
    ]
    assert all(parameters["user_id"] == 7 for _statement, parameters in statements)


@pytest.mark.anyio
async def test_ct_pb32_05_sincronizacoes_concorrentes_convergem_sem_duplicar(db, monkeypatch):
    user_id, original = _seed(db, built_at=NOW - timedelta(days=8))
    calls = 0

    async def top(*_args, **_kwargs):
        return None

    async def inventory(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        await asyncio.sleep(0.02)
        return SimpleNamespace(items=tuple(db.query(UserPlaylistInventory).all()))

    monkeypatch.setattr("app.services.library_sync_service.get_or_refresh_snapshot", top)
    monkeypatch.setattr("app.services.library_sync_service.refresh_playlist_inventory", inventory)
    results = await asyncio.gather(
        sync_music_library(db, user_id, now=NOW),
        sync_music_library(db, user_id, now=NOW),
    )

    assert calls == 1
    assert results[0].snapshot.id == results[1].snapshot.id
    assert results[0].snapshot.id != original.id
    assert db.query(UserMusicLibrarySnapshot).count() == 1


@pytest.mark.anyio
async def test_ct_pb32_06_sem_cache_falha_explicita_e_tops_permanecem(db, monkeypatch):
    user_id, _ = _seed(db)

    async def top(*_args, **_kwargs):
        return None

    async def inventory(*_args, **_kwargs):
        raise spotify_client.SpotifyRateLimited(19)

    monkeypatch.setattr("app.services.library_sync_service.get_or_refresh_snapshot", top)
    monkeypatch.setattr("app.services.library_sync_service.refresh_playlist_inventory", inventory)

    with pytest.raises(LibrarySyncRateLimited) as caught:
        await sync_music_library(db, user_id, now=NOW)

    assert caught.value.retry_after == 19
    assert db.query(UserMusicSnapshot).filter_by(user_id=user_id).count() == 3
    assert db.query(UserMusicLibrarySnapshot).count() == 0
    assert db.query(UserMusicLibraryTrack).count() == 0


def test_pb32_migration_upgrade_e_downgrade_reversiveis(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'pb32-migration.sqlite3'}", future=True)
    metadata = Base.metadata
    users = metadata.tables["users"]
    users.create(engine)

    versions = Path(__file__).parents[1] / "alembic" / "versions"

    def load(filename: str, module_name: str):
        spec = importlib.util.spec_from_file_location(module_name, versions / filename)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    pb31 = load("0020_pb31_music_library.py", "pb31_for_pb32")
    pb32 = load("0021_pb32_library_sync.py", "pb32_migration")
    with engine.begin() as connection:
        operations = Operations(MigrationContext.configure(connection))
        with patch.object(pb31, "op", operations):
            pb31.upgrade()
        with patch.object(pb32, "op", operations):
            pb32.upgrade()

        inspector = sa.inspect(connection)
        assert "user_music_library_playlist_states" in inspector.get_table_names()
        assert {"last_sync_attempt_at", "last_sync_error_code", "last_sync_retry_after"} <= {
            column["name"]
            for column in inspector.get_columns("user_music_library_snapshots")
        }

        with patch.object(pb32, "op", operations):
            pb32.downgrade()
        inspector = sa.inspect(connection)
        assert "user_music_library_playlist_states" not in inspector.get_table_names()
        assert "last_sync_attempt_at" not in {
            column["name"]
            for column in inspector.get_columns("user_music_library_snapshots")
        }

    engine.dispose()
