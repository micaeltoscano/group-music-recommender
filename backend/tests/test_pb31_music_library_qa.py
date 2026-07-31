"""Testes adversariais independentes de QA para o PB-31."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import (
    User,
    UserMusicLibraryTrack,
    UserPlaylistInventory,
)
from app.engine.music_library import (
    ComposedLibraryTrack,
    LibraryOrigin,
    MinimalTrack,
    PlaylistTrackSignal,
    TopTrackSignal,
    compose_music_library,
)
from app.services import music_library_service


def _track(track_id: str) -> dict:
    return {
        "id": track_id,
        "uri": f"spotify:track:{track_id}",
        "name": track_id,
        "artists": [{"id": f"Artist{track_id}", "name": "QA"}],
    }


def test_qa_pb31_round_robin_preserva_playlist_pequena_em_biblioteca_assimetrica():
    signals = [
        *[
            PlaylistTrackSignal(_track(f"Large{index:03d}"), "LargeList", "owned", index + 1)
            for index in range(100)
        ],
        PlaylistTrackSignal(_track("Small001"), "SmallList", "collaborative", 1),
        PlaylistTrackSignal(_track("Small002"), "SmallList", "collaborative", 2),
    ]

    result = compose_music_library([], reversed(signals), limit=6)

    assert [item.track.spotify_track_id for item in result] == [
        "Large000",
        "Small001",
        "Large001",
        "Small002",
        "Large002",
        "Large003",
    ]


def test_qa_pb31_origem_encontrada_apos_cap_e_preservada_sem_criar_501a_faixa():
    shared = _track("Shared001")
    tops = [TopTrackSignal(shared, "short_term", 1)]
    playlists = [
        *[
            PlaylistTrackSignal(_track(f"Fresh{index:03d}"), "Playlist01", "owned", index + 1)
            for index in range(500)
        ],
        PlaylistTrackSignal(shared, "Playlist01", "owned", 501),
    ]

    result = compose_music_library(tops, playlists)

    assert len(result) == 500
    stored = next(item for item in result if item.track.spotify_track_id == "Shared001")
    assert {(origin.source_type, origin.source_ref, origin.rank) for origin in stored.origins} == {
        ("top", "short_term", 1),
        ("playlist", "Playlist01", 501),
    }


def test_qa_pb31_falha_de_persistencia_restaura_snapshot_anterior(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'pb31-qa.sqlite3'}", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = factory()
    try:
        user = User(spotify_id="pb31-qa-user")
        db.add(user)
        db.flush()
        db.add(
            UserPlaylistInventory(
                user_id=user.id,
                spotify_playlist_id="Playlist01",
                access_type="owned",
                tracks_total=1,
                snapshot_id="inventory-snapshot",
                verified_at=datetime.now(timezone.utc),
            )
        )
        db.commit()
        first = music_library_service.rebuild_music_library(
            db,
            user.id,
            playlist_tracks_by_id={"Playlist01": [_track("Stable001")]},
        )
        first_id = first.id

        invalid = (
            ComposedLibraryTrack(
                track=MinimalTrack(
                    spotify_track_id="Invalid501",
                    spotify_uri="spotify:track:Invalid501",
                    track_name="Inválida",
                    artist_id=None,
                    artist_name=None,
                ),
                position=501,
                origins=(LibraryOrigin("top", "short_term", 1),),
            ),
        )
        monkeypatch.setattr(music_library_service, "compose_music_library", lambda *_args: invalid)

        with pytest.raises(IntegrityError):
            music_library_service.rebuild_music_library(
                db,
                user.id,
                playlist_tracks_by_id={},
            )

        restored = db.query(UserMusicLibraryTrack).filter_by(user_id=user.id).one()
        assert restored.snapshot_id == first_id
        assert restored.spotify_track_id == "Stable001"
    finally:
        db.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
