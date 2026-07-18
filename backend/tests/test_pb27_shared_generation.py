"""PB-27 — progresso compartilhado e recuperação host-only."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.auth import SESSION_COOKIE_NAME
from app.db.base import Base
from app.db.models import AppSession, MusicSession, MusicSessionMember, PlaylistRun, User
from app.db.session import get_db
from app.main import app
from app.services.generation_service import update_generation_progress


def test_progress_is_persisted_and_never_moves_backwards(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'progress.sqlite3'}", future=True)
    factory = sessionmaker(bind=engine, future=True)
    Base.metadata.create_all(engine)
    db = factory()
    host = User(spotify_id="progress-host")
    db.add(host)
    db.flush()
    room = MusicSession(
        code="PROG-RESS",
        host_user_id=host.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.add(room)
    db.flush()
    run = PlaylistRun(session_id=room.id)
    db.add(run)
    db.commit()

    update_generation_progress(db, run.id, "ranking")
    update_generation_progress(db, run.id, "collecting_tastes")
    db.refresh(run)

    assert run.progress_stage == "ranking"
    assert run.progress_percent == 55
    with pytest.raises(ValueError, match="desconhecido"):
        update_generation_progress(db, run.id, "private_user_scores")
    db.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_member_poll_receives_latest_public_generation_state(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'shared.sqlite3'}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(engine)
    db = factory()
    host = User(spotify_id="shared-host", display_name="Host")
    member = User(spotify_id="shared-member", display_name="Member")
    outsider = User(spotify_id="shared-outsider", display_name="Outsider")
    db.add_all([host, member, outsider])
    db.flush()
    room = MusicSession(
        code="SHAR-ED27",
        host_user_id=host.id,
        status="generating",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.add(room)
    db.flush()
    db.add_all(
        [
            MusicSessionMember(session_id=room.id, user_id=host.id, role="host"),
            MusicSessionMember(session_id=room.id, user_id=member.id, role="member"),
        ]
    )
    now = datetime.now(timezone.utc)
    run = PlaylistRun(
        session_id=room.id,
        status="running",
        progress_stage="ranking",
        progress_percent=55,
        created_at=now,
    )
    db.add(run)
    for user, token in ((member, "member-token"), (outsider, "outsider-token")):
        db.add(
            AppSession(
                user_id=user.id,
                session_token_hash=hashlib.sha256(token.encode()).hexdigest(),
                expires_at=now + timedelta(hours=1),
            )
        )
    db.commit()
    room_code = room.code

    def _override_get_db():
        request_db = factory()
        try:
            yield request_db
        finally:
            request_db.close()

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as client:
            client.cookies.set(SESSION_COOKIE_NAME, "member-token")
            response = client.get(f"/rooms/{room_code}")
            assert response.status_code == 200
            generation = response.json()["generation"]
            assert generation == {
                "run_id": str(run.id),
                "status": "running",
                "stage": "ranking",
                "progress_percent": 55,
                "error_message": None,
                "playlist_url": None,
                "updated_at": generation["updated_at"],
            }
            assert "tracks" not in generation
            assert "llm_context" not in generation

            client.cookies.set(SESSION_COOKIE_NAME, "outsider-token")
            assert client.get(f"/rooms/{room_code}").status_code == 403

        db.refresh(run)
        run.status = "failed"
        run.progress_stage = "failed"
        run.error_message = "Spotify temporariamente limitado."
        room.status = "open"
        db.commit()

        with TestClient(app) as client:
            client.cookies.set(SESSION_COOKIE_NAME, "member-token")
            failed = client.get(f"/rooms/{room_code}").json()["generation"]
            assert failed["status"] == "failed"
            assert failed["error_message"] == "Spotify temporariamente limitado."
    finally:
        app.dependency_overrides.clear()
        db.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
