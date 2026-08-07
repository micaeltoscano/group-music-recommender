"""Testes adversariais independentes da PB-34."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import User, UserMusicLibrarySnapshot, UserMusicSnapshot
from app.services.library_application_service import (
    load_library_generation_data,
    music_library_status,
)


def _top(track_id: str) -> dict:
    return {
        "id": track_id,
        "uri": f"spotify:track:{track_id}",
        "name": track_id,
        "artists": [{"id": f"Artist{track_id}", "name": "QA"}],
    }


def test_qa_ct_pb34_04_biblioteca_vazia_com_tops_aciona_fallback(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'pb34-qa.sqlite3'}", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    db = factory()
    try:
        user = User(spotify_id="PB34Empty", display_name="QA")
        db.add(user)
        db.flush()
        db.add(
            UserMusicSnapshot(
                user_id=user.id,
                time_range="medium_term",
                top_tracks_json=[_top("FallbackTop01")],
                top_artists_json=[],
                fetched_at=datetime.now(timezone.utc),
            )
        )
        db.add(
            UserMusicLibrarySnapshot(
                user_id=user.id,
                track_count=0,
                built_at=datetime.now(timezone.utc),
            )
        )
        db.commit()

        status = music_library_status(db, user.id)
        data = load_library_generation_data(db, [user.id])

        assert status.track_count == 0
        assert data is None, "biblioteca sem candidatas deve cair para o Top PB-08"
    finally:
        db.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
