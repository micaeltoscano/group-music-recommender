"""Validação adversarial independente da PB-32."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.clients import spotify_client
from app.db.base import Base
from app.db.models import (
    User,
    UserMusicLibrarySnapshot,
    UserMusicSnapshot,
    UserPlaylistInventory,
)
from app.services.library_sync_service import sync_music_library
from app.services.music_library_service import rebuild_music_library


NOW = datetime(2026, 7, 31, 15, tzinfo=timezone.utc)


def _track(track_id: str) -> dict:
    return {
        "id": track_id,
        "uri": f"spotify:track:{track_id}",
        "name": track_id,
        "artists": [{"id": f"Artist{track_id}", "name": "QA"}],
    }


@pytest.fixture()
def database(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pb32-qa.sqlite3'}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
    try:
        yield factory
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


def _seed(factory, *, playlists: tuple[str, ...] = ("PlaylistA",)) -> tuple[int, object]:
    db = factory()
    try:
        user = User(spotify_id="PB32QA", display_name="QA")
        db.add(user)
        db.flush()
        for time_range in ("short_term", "medium_term", "long_term"):
            db.add(
                UserMusicSnapshot(
                    user_id=user.id,
                    time_range=time_range,
                    top_tracks_json=[_track(f"Top{len(time_range)}")],
                    top_artists_json=[],
                    fetched_at=NOW,
                )
            )
        for playlist_id in playlists:
            db.add(
                UserPlaylistInventory(
                    user_id=user.id,
                    spotify_playlist_id=playlist_id,
                    access_type="owned",
                    tracks_total=1,
                    snapshot_id=f"Old{playlist_id}",
                    verified_at=NOW - timedelta(days=8),
                )
            )
        db.commit()
        snapshot = rebuild_music_library(
            db,
            user.id,
            playlist_tracks_by_id={
                playlist_id: [_track(f"OldTrack{playlist_id}")]
                for playlist_id in playlists
            },
            built_at=NOW - timedelta(days=8),
        )
        return user.id, snapshot.id
    finally:
        db.close()


@pytest.mark.anyio
async def test_qa_429_na_segunda_playlist_nao_promove_primeira_parcial(
    database, monkeypatch
):
    user_id, original_id = _seed(database, playlists=("PlaylistA", "PlaylistB"))
    db = database()

    async def tops(*_args, **_kwargs):
        return None

    async def inventory(*_args, **_kwargs):
        rows = db.query(UserPlaylistInventory).order_by(
            UserPlaylistInventory.spotify_playlist_id
        ).all()
        for row in rows:
            row.snapshot_id = f"New{row.spotify_playlist_id}"
        db.commit()
        return SimpleNamespace(items=tuple(rows))

    calls = []

    async def tracks(_token, playlist_id, *, limit):
        calls.append((playlist_id, limit))
        if playlist_id == "PlaylistB":
            raise spotify_client.SpotifyRateLimited(41)
        return [_track("DownloadedA")]

    monkeypatch.setattr("app.services.library_sync_service.get_or_refresh_snapshot", tops)
    monkeypatch.setattr("app.services.library_sync_service.refresh_playlist_inventory", inventory)
    monkeypatch.setattr(
        spotify_client,
        "get_valid_access_token",
        lambda *_args, **_kwargs: asyncio.sleep(0, result="token"),
    )
    monkeypatch.setattr(spotify_client, "get_playlist_tracks", tracks)

    try:
        result = await sync_music_library(db, user_id, now=NOW)
        assert result.snapshot.id == original_id
        assert result.warning_code == "RATE_LIMITED"
        assert result.retry_after == 41
        assert calls == [("PlaylistA", 50), ("PlaylistB", 50)]
        assert "DownloadedA" not in {
            track.spotify_track_id for track in result.snapshot.tracks
        }
    finally:
        db.close()


@pytest.mark.anyio
async def test_qa_concorrencia_com_sessoes_independentes_converge(database, monkeypatch):
    user_id, original_id = _seed(database)
    first = database()
    second = database()
    inventory_calls = 0

    async def tops(*_args, **_kwargs):
        return None

    async def inventory(db, *_args, **_kwargs):
        nonlocal inventory_calls
        inventory_calls += 1
        await asyncio.sleep(0.02)
        return SimpleNamespace(items=tuple(db.query(UserPlaylistInventory).all()))

    monkeypatch.setattr("app.services.library_sync_service.get_or_refresh_snapshot", tops)
    monkeypatch.setattr("app.services.library_sync_service.refresh_playlist_inventory", inventory)
    try:
        results = await asyncio.gather(
            sync_music_library(first, user_id, now=NOW),
            sync_music_library(second, user_id, now=NOW),
        )
        first.expire_all()
        assert inventory_calls == 1
        assert results[0].snapshot.id == results[1].snapshot.id
        assert results[0].snapshot.id != original_id
        assert first.query(UserMusicLibrarySnapshot).filter_by(user_id=user_id).count() == 1
    finally:
        first.close()
        second.close()
