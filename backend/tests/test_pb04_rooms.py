"""Testes técnicos do implementador para o PB-04 (criação de sala)."""

from __future__ import annotations

import hashlib
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.auth import SESSION_COOKIE_NAME
from app.db.base import Base
from app.db.models import AppSession, MusicSession, MusicSessionMember, User
from app.db.session import get_db
from app.main import app
from app.services import room_service


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pb04.sqlite3'}",
        connect_args={"check_same_thread": False, "timeout": 30},
        future=True,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    try:
        yield factory
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def client(session_factory):
    def _override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _authenticate(client: TestClient, session_factory, *, spotify_id: str = "demo_user_1") -> int:
    raw_token = f"session-for-{spotify_id}"
    db = session_factory()
    try:
        user = User(
            spotify_id=spotify_id,
            display_name="Demo Host",
            image_url="https://images.invalid/host.png",
        )
        db.add(user)
        db.flush()
        user_id = user.id
        db.add(
            AppSession(
                user_id=user_id,
                session_token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
        )
        db.commit()
    finally:
        db.close()
    client.cookies.set(SESSION_COOKIE_NAME, raw_token)
    return user_id


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def test_ct_pb04_01_authenticated_user_creates_persisted_room(client, session_factory):
    host_id = _authenticate(client, session_factory)

    response = client.post("/rooms")

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "open"
    assert re.fullmatch(r"[A-HJ-NP-Z2-9]{4}-[A-HJ-NP-Z2-9]{4}", body["code"])
    assert body["members"] == [
        {
            "user_id": host_id,
            "display_name": "Demo Host",
            "image_url": "https://images.invalid/host.png",
            "role": "host",
            "joined_at": body["members"][0]["joined_at"],
        }
    ]

    db = session_factory()
    try:
        assert db.query(MusicSession).count() == 1
        assert db.query(MusicSessionMember).count() == 1
    finally:
        db.close()


@pytest.mark.parametrize("cookie", [None, "invalid-session"])
def test_ct_pb04_02_unauthenticated_creation_is_blocked(
    client,
    session_factory,
    cookie,
):
    if cookie is not None:
        client.cookies.set(SESSION_COOKIE_NAME, cookie)

    response = client.post("/rooms")

    assert response.status_code == 401
    db = session_factory()
    try:
        assert db.query(MusicSession).count() == 0
        assert db.query(MusicSessionMember).count() == 0
    finally:
        db.close()


def test_ct_pb04_03_codes_remain_unique_under_parallel_creation(session_factory):
    db = session_factory()
    try:
        host = User(spotify_id="parallel-host", display_name="Parallel Host")
        db.add(host)
        db.commit()
        host_id = host.id
    finally:
        db.close()

    def create_one() -> str:
        worker_db = session_factory()
        try:
            room, _ = room_service.create_room(worker_db, host_id)
            return room.code
        finally:
            worker_db.close()

    with ThreadPoolExecutor(max_workers=6) as executor:
        codes = list(executor.map(lambda _: create_one(), range(12)))

    assert len(codes) == len(set(codes)) == 12
    db = session_factory()
    try:
        assert db.query(MusicSession).count() == 12
    finally:
        db.close()


def test_ct_pb04_03_collision_retries_without_partial_state(session_factory, monkeypatch):
    db = session_factory()
    try:
        host = User(spotify_id="collision-host")
        db.add(host)
        db.commit()
        host_id = host.id

        generated_codes = iter(["ABCD-EFGH", "ABCD-EFGH", "JKLM-NPQR"])
        monkeypatch.setattr(room_service, "_generate_room_code", lambda: next(generated_codes))

        first_room, _ = room_service.create_room(db, host_id)
        second_room, _ = room_service.create_room(db, host_id)

        assert first_room.code == "ABCD-EFGH"
        assert second_room.code == "JKLM-NPQR"
        assert db.query(MusicSession).count() == 2
        assert db.query(MusicSessionMember).count() == 2
    finally:
        db.close()


def test_ct_pb04_04_creator_is_the_only_first_member_and_host(client, session_factory):
    host_id = _authenticate(client, session_factory)

    response = client.post("/rooms")

    room_id = UUID(response.json()["id"])
    db = session_factory()
    try:
        memberships = (
            db.query(MusicSessionMember)
            .filter(MusicSessionMember.session_id == room_id)
            .all()
        )
        assert len(memberships) == 1
        assert memberships[0].user_id == host_id
        assert memberships[0].role == "host"
        room = db.query(MusicSession).filter(MusicSession.id == room_id).one()
        assert room.host_user_id == host_id
    finally:
        db.close()


def test_ct_pb04_05_room_expires_exactly_24_hours_after_creation(client, session_factory):
    _authenticate(client, session_factory)

    response = client.post("/rooms")

    body = response.json()
    created_at = datetime.fromisoformat(body["created_at"].replace("Z", "+00:00"))
    expires_at = datetime.fromisoformat(body["expires_at"].replace("Z", "+00:00"))
    assert expires_at - created_at == timedelta(hours=24)

    db = session_factory()
    try:
        room = db.query(MusicSession).one()
        assert _as_utc(room.expires_at) - _as_utc(room.created_at) == timedelta(hours=24)
    finally:
        db.close()


def test_ct_pb04_06_response_contains_only_room_and_host_public_data(client, session_factory):
    _authenticate(client, session_factory)
    db = session_factory()
    try:
        db.add(User(spotify_id="private-outsider", display_name="Private Outsider"))
        db.commit()
    finally:
        db.close()

    response = client.post("/rooms")

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"id", "code", "status", "created_at", "expires_at", "members"}
    assert set(body["members"][0]) == {
        "user_id",
        "display_name",
        "image_url",
        "role",
        "joined_at",
    }
    serialized = response.text.lower()
    assert "token" not in serialized
    assert "session" not in serialized
    assert "private outsider" not in serialized
