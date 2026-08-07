"""PB-29 — status público e valores privados do Vibe Check."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.auth import SESSION_COOKIE_NAME
from app.db.base import Base
from app.db.models import AppSession, MusicSession, MusicSessionMember, User, VibeCheckAnswer
from app.db.session import get_db
from app.engine.vibe_scoring import VibePreferences
from app.main import app
from app.services.generation_service import load_vibe_preferences


def test_room_shares_only_status_and_skip_is_neutral_and_editable(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'vibe-status.sqlite3'}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(engine)
    db = factory()
    users = [
        User(spotify_id="vibe-host", display_name="Host"),
        User(spotify_id="vibe-skipped", display_name="Skipped"),
        User(spotify_id="vibe-pending", display_name="Pending"),
    ]
    db.add_all(users)
    db.flush()
    room = MusicSession(
        code="VIBE-S629",
        host_user_id=users[0].id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.add(room)
    db.flush()
    for index, user in enumerate(users):
        db.add(
            MusicSessionMember(
                session_id=room.id,
                user_id=user.id,
                role="host" if index == 0 else "member",
            )
        )
        token = f"vibe-token-{index}"
        db.add(
            AppSession(
                user_id=user.id,
                session_token_hash=hashlib.sha256(token.encode()).hexdigest(),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
        )
    db.add_all(
        [
            VibeCheckAnswer(
                session_id=room.id,
                user_id=users[0].id,
                status="answered",
                energy=0.8,
                valence=0.4,
                popularity=1.0,
            ),
            VibeCheckAnswer(
                session_id=room.id,
                user_id=users[1].id,
                status="skipped",
            ),
        ]
    )
    db.commit()
    room_code = room.code
    member_ids = [user.id for user in users]

    def _override_get_db():
        request_db = factory()
        try:
            yield request_db
        finally:
            request_db.close()

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as client:
            client.cookies.set(SESSION_COOKIE_NAME, "vibe-token-2")
            payload = client.get(f"/rooms/{room_code}").json()
            assert payload["vibe_summary"] == {
                "total": 3,
                "pending": 1,
                "answered": 1,
                "skipped": 1,
            }
            assert [member["vibe_status"] for member in payload["members"]] == [
                "answered",
                "skipped",
                "pending",
            ]
            serialized = str(payload)
            assert "energy" not in serialized
            assert "valence" not in serialized
            assert "popularity" not in serialized

            own_pending = client.get(f"/rooms/{room_code}/vibe-check").json()
            assert own_pending["status"] == "pending"
            assert own_pending["answer"] is None

            assert client.post(f"/rooms/{room_code}/vibe-check/skip").status_code == 200
            own_skipped = client.get(f"/rooms/{room_code}/vibe-check").json()
            assert own_skipped["status"] == "skipped"
            assert own_skipped["answer"] is None

            submitted = client.post(
                f"/rooms/{room_code}/vibe-check",
                json={"energy": 0.2, "valence": 0.3, "popularity": 0.4},
            )
            assert submitted.status_code == 200
            edited = client.get(f"/rooms/{room_code}/vibe-check").json()
            assert edited["status"] == "answered"
            assert edited["answer"] == {"energy": 0.2, "valence": 0.3, "popularity": 0.4}

            client.cookies.set(SESSION_COOKIE_NAME, "vibe-token-0")
            own_host = client.get(f"/rooms/{room_code}/vibe-check").json()
            assert own_host["answer"] == {"energy": 0.8, "valence": 0.4, "popularity": 1.0}

        preferences = load_vibe_preferences(db, room.id, member_ids)
        assert preferences == VibePreferences(energy=0.5, valence=0.4, popularity=0.6333)
        skipped = db.query(VibeCheckAnswer).filter_by(user_id=users[1].id).one()
        assert skipped.status == "skipped"
        assert skipped.energy is None
        assert skipped.valence is None
        assert skipped.popularity is None
    finally:
        app.dependency_overrides.clear()
        db.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
