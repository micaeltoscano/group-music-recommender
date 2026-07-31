"""PB-31 — biblioteca pessoal deduplicada, justa e limitada a 500 faixas."""

from __future__ import annotations

import importlib.util
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import (
    User,
    UserMusicLibrarySnapshot,
    UserMusicLibrarySource,
    UserMusicLibraryTrack,
    UserMusicSnapshot,
    UserPlaylistInventory,
)
from app.engine.music_library import (
    PlaylistTrackSignal,
    TopTrackSignal,
    compose_music_library,
)
from app.services.music_library_service import rebuild_music_library
from app.services.privacy_service import remove_personal_data


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pb31.sqlite3'}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    try:
        yield factory
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


def _track(index: int, *, prefix: str = "Track", secret: bool = False) -> dict:
    track_id = f"{prefix}{index:05d}"
    return {
        "id": track_id,
        "uri": f"spotify:track:{track_id}",
        "name": f"Faixa {index}",
        "artists": [{"id": f"Artist{index:05d}", "name": f"Artista {index}"}],
        "album": {"images": [{"url": "https://private.invalid/image.jpg"}]},
        "private_payload": "segredo" if secret else None,
    }


def _seed_user(session_factory, spotify_id: str = "pb31-user") -> int:
    db = session_factory()
    try:
        user = User(spotify_id=spotify_id, display_name="PB31")
        db.add(user)
        db.commit()
        return user.id
    finally:
        db.close()


def _seed_inventory(
    session_factory,
    user_id: int,
    playlist_id: str,
    *,
    access_type: str = "owned",
) -> None:
    db = session_factory()
    try:
        db.add(
            UserPlaylistInventory(
                user_id=user_id,
                spotify_playlist_id=playlist_id,
                access_type=access_type,
                tracks_total=1000,
                snapshot_id=f"snapshot-{playlist_id}",
                verified_at=datetime.now(timezone.utc),
            )
        )
        db.commit()
    finally:
        db.close()


def test_ct_pb31_01_tops_ocupam_primeiras_vagas_e_artistas_nao_contam(
    session_factory,
):
    user_id = _seed_user(session_factory)
    _seed_inventory(session_factory, user_id, "Playlist01")
    db = session_factory()
    try:
        for range_index, time_range in enumerate(
            ("short_term", "medium_term", "long_term")
        ):
            db.add(
                UserMusicSnapshot(
                    user_id=user_id,
                    time_range=time_range,
                    top_tracks_json=[
                        _track(index + (range_index * 50), prefix="Top")
                        for index in range(50)
                    ],
                    top_artists_json=[{"id": f"ArtistOnly{index}"} for index in range(1000)],
                    fetched_at=datetime.now(timezone.utc),
                )
            )
        db.commit()

        snapshot = rebuild_music_library(
            db,
            user_id,
            playlist_tracks_by_id={
                "Playlist01": [
                    *[_track(index, prefix="Playlist") for index in range(499)],
                    _track(0, prefix="Top"),
                ]
            },
        )

        tracks = (
            db.query(UserMusicLibraryTrack)
            .filter_by(snapshot_id=snapshot.id)
            .order_by(UserMusicLibraryTrack.position)
            .all()
        )
        assert snapshot.track_count == len(tracks) == 500
        assert all(
            any(origin.source_type == "top" for origin in track.origins)
            for track in tracks[:150]
        )
        assert all(
            {origin.source_type for origin in track.origins} == {"playlist"}
            for track in tracks[150:]
        )
        assert db.query(UserMusicLibrarySource).filter_by(source_type="top").count() == 150
        top_zero = next(track for track in tracks if track.spotify_track_id == "Top00000")
        assert {
            (origin.source_type, origin.source_ref, origin.source_rank)
            for origin in top_zero.origins
        } == {
            ("top", "short_term", 1),
            ("playlist", "Playlist01", 500),
        }
    finally:
        db.close()


@pytest.mark.parametrize("requested", [0, 499, 500, 501, 2000])
def test_ct_pb31_02_limite_absoluto_persistido(
    session_factory,
    requested,
):
    user_id = _seed_user(session_factory, spotify_id=f"pb31-limit-{requested}")
    _seed_inventory(session_factory, user_id, "PlaylistLimit")
    db = session_factory()
    try:
        snapshot = rebuild_music_library(
            db,
            user_id,
            playlist_tracks_by_id={
                "PlaylistLimit": [_track(index, prefix="Limit") for index in range(requested)]
            },
        )

        expected = min(requested, 500)
        assert snapshot.track_count == expected
        assert db.query(UserMusicLibraryTrack).filter_by(user_id=user_id).count() == expected
        assert db.query(UserMusicLibraryTrack.position).filter_by(user_id=user_id).all() == [
            (position,) for position in range(1, expected + 1)
        ]
    finally:
        db.close()


def test_ct_pb31_03_dedupe_preserva_todas_as_origens_e_ranks(session_factory):
    user_id = _seed_user(session_factory)
    _seed_inventory(session_factory, user_id, "Owned01", access_type="owned")
    _seed_inventory(
        session_factory,
        user_id,
        "Collab01",
        access_type="collaborative",
    )
    shared = _track(1, prefix="Shared")
    db = session_factory()
    try:
        db.add_all(
            [
                UserMusicSnapshot(
                    user_id=user_id,
                    time_range="short_term",
                    top_tracks_json=[shared],
                    top_artists_json=[],
                    fetched_at=datetime.now(timezone.utc),
                ),
                UserMusicSnapshot(
                    user_id=user_id,
                    time_range="long_term",
                    top_tracks_json=[shared],
                    top_artists_json=[],
                    fetched_at=datetime.now(timezone.utc),
                ),
            ]
        )
        db.commit()

        rebuild_music_library(
            db,
            user_id,
            playlist_tracks_by_id={
                "Owned01": [_track(20), shared],
                "Collab01": [shared],
                "FollowedNotInventoried": [_track(999)],
            },
        )

        stored = db.query(UserMusicLibraryTrack).filter_by(
            user_id=user_id,
            spotify_track_id=shared["id"],
        ).one()
        assert db.query(UserMusicLibraryTrack).filter_by(
            user_id=user_id,
            spotify_track_id=shared["id"],
        ).count() == 1
        assert {
            (origin.source_type, origin.source_ref, origin.source_rank, origin.access_type)
            for origin in stored.origins
        } == {
            ("top", "short_term", 1, None),
            ("top", "long_term", 1, None),
            ("playlist", "Owned01", 2, "owned"),
            ("playlist", "Collab01", 1, "collaborative"),
        }
        assert db.query(UserMusicLibraryTrack).filter_by(
            spotify_track_id="Track00999"
        ).count() == 0
    finally:
        db.close()


def test_ct_pb31_04_round_robin_e_deterministico_entre_playlists():
    playlist_signals = [
        PlaylistTrackSignal(_track(3, prefix="B"), "PlaylistB", "owned", 2),
        PlaylistTrackSignal(_track(1, prefix="A"), "PlaylistA", "owned", 1),
        PlaylistTrackSignal(_track(2, prefix="B"), "PlaylistB", "owned", 1),
        PlaylistTrackSignal(_track(4, prefix="A"), "PlaylistA", "owned", 2),
    ]

    first = compose_music_library([], playlist_signals, limit=4)
    second = compose_music_library([], reversed(playlist_signals), limit=4)

    expected = ("A00001", "B00002", "A00004", "B00003")
    assert tuple(item.track.spotify_track_id for item in first) == expected
    assert tuple(item.track.spotify_track_id for item in second) == expected


def test_ct_pb31_05_metadados_minimos_e_remocao_isolada(session_factory):
    owner_id = _seed_user(session_factory, "pb31-owner")
    other_id = _seed_user(session_factory, "pb31-other")
    _seed_inventory(session_factory, owner_id, "OwnerList")
    _seed_inventory(session_factory, other_id, "OtherList")
    db = session_factory()
    try:
        rebuild_music_library(
            db,
            owner_id,
            playlist_tracks_by_id={"OwnerList": [_track(1, secret=True)]},
        )
        rebuild_music_library(
            db,
            other_id,
            playlist_tracks_by_id={"OtherList": [_track(2)]},
        )

        assert {column.name for column in UserMusicLibraryTrack.__table__.columns} == {
            "id",
            "snapshot_id",
            "user_id",
            "spotify_track_id",
            "spotify_uri",
            "track_name",
            "artist_id",
            "artist_name",
            "position",
        }
        persisted = str(db.query(UserMusicLibraryTrack).filter_by(user_id=owner_id).one().__dict__)
        assert "private_payload" not in persisted
        assert "segredo" not in persisted
        assert "images" not in persisted

        remove_personal_data(db, owner_id)

        assert db.query(UserMusicLibrarySnapshot).filter_by(user_id=owner_id).count() == 0
        assert db.query(UserMusicLibraryTrack).filter_by(user_id=owner_id).count() == 0
        assert db.query(UserMusicLibrarySource).count() == 1
        assert db.query(UserPlaylistInventory).filter_by(user_id=owner_id).count() == 0
        assert db.query(UserMusicLibraryTrack).filter_by(user_id=other_id).count() == 1
    finally:
        db.close()


def test_rebuild_substitui_snapshot_e_vinculos_antigos(session_factory):
    user_id = _seed_user(session_factory)
    _seed_inventory(session_factory, user_id, "ReplaceList")
    db = session_factory()
    try:
        first = rebuild_music_library(
            db,
            user_id,
            playlist_tracks_by_id={
                "ReplaceList": [_track(index, prefix="Old") for index in range(3)]
            },
        )
        first_id = first.id

        second = rebuild_music_library(
            db,
            user_id,
            playlist_tracks_by_id={"ReplaceList": [_track(1, prefix="New")]},
        )

        assert second.id != first_id
        assert db.query(UserMusicLibrarySnapshot).filter_by(user_id=user_id).count() == 1
        assert [
            track.spotify_track_id
            for track in db.query(UserMusicLibraryTrack).filter_by(user_id=user_id).all()
        ] == ["New00001"]
        assert db.query(UserMusicLibrarySource).count() == 1
    finally:
        db.close()


def test_ct_pb31_06_migration_reversivel_e_unicidade(tmp_path):
    database_path = tmp_path / "pb31-migration.sqlite3"
    engine = create_engine(f"sqlite:///{database_path}", future=True)
    metadata = sa.MetaData()
    sa.Table("users", metadata, sa.Column("id", sa.Integer(), primary_key=True))
    metadata.create_all(engine)

    migration_path = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "0020_pb31_music_library.py"
    )
    spec = importlib.util.spec_from_file_location("pb31_migration", migration_path)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    with engine.begin() as connection:
        operations = Operations(MigrationContext.configure(connection))
        with patch.object(migration, "op", operations):
            migration.upgrade()
        inspector = sa.inspect(connection)
        assert {
            "user_music_library_snapshots",
            "user_music_library_tracks",
            "user_music_library_sources",
        }.issubset(inspector.get_table_names())

        snapshot_id = uuid.uuid4()
        track_id = uuid.uuid4()
        connection.execute(sa.text("INSERT INTO users (id) VALUES (1)"))
        connection.execute(
            sa.text(
                "INSERT INTO user_music_library_snapshots "
                "(id, user_id, track_count, built_at) "
                "VALUES (:id, 1, 1, :built_at)"
            ),
            {"id": snapshot_id.hex, "built_at": datetime.now(timezone.utc)},
        )
        connection.execute(
            sa.text(
                "INSERT INTO user_music_library_tracks "
                "(id, snapshot_id, user_id, spotify_track_id, spotify_uri, position) "
                "VALUES (:id, :snapshot_id, 1, 'Unique01', "
                "'spotify:track:Unique01', 1)"
            ),
            {"id": track_id.hex, "snapshot_id": snapshot_id.hex},
        )
        savepoint = connection.begin_nested()
        try:
            with pytest.raises(IntegrityError):
                connection.execute(
                    sa.text(
                        "INSERT INTO user_music_library_tracks "
                        "(id, snapshot_id, user_id, spotify_track_id, spotify_uri, position) "
                        "VALUES (:id, :snapshot_id, 1, 'Unique01', "
                        "'spotify:track:Unique01', 2)"
                    ),
                    {"id": uuid.uuid4().hex, "snapshot_id": snapshot_id.hex},
                )
        finally:
            savepoint.rollback()

        with patch.object(migration, "op", operations):
            migration.downgrade()
        assert "user_music_library_tracks" not in sa.inspect(connection).get_table_names()
        with patch.object(migration, "op", operations):
            migration.upgrade()
        assert "user_music_library_tracks" in sa.inspect(connection).get_table_names()

    engine.dispose()
