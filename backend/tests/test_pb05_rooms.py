"""Testes técnicos do implementador para o PB-05 (entrada e lobby)."""

from __future__ import annotations

import hashlib
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import sessionmaker

from app.api.auth import SESSION_COOKIE_NAME
from app.db.base import Base
from app.db.models import AppSession, MusicSessionMember, User
from app.db.session import get_db
from app.main import app
from app.services import room_service


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pb05.sqlite3'}",
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


def _create_authenticated_user(
    session_factory,
    spotify_id: str,
    *,
    display_name: str | None = None,
) -> tuple[int, str]:
    raw_token = f"session-for-{spotify_id}"
    db = session_factory()
    try:
        user = User(
            spotify_id=spotify_id,
            display_name=display_name or spotify_id.replace("_", " ").title(),
            image_url=f"https://images.invalid/{spotify_id}.png",
        )
        db.add(user)
        db.flush()
        db.add(
            AppSession(
                user_id=user.id,
                session_token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
        )
        db.commit()
        return user.id, raw_token
    finally:
        db.close()


def _act_as(client: TestClient, token: str) -> None:
    client.cookies.set(SESSION_COOKIE_NAME, token)


def _create_room_for_host(client, session_factory) -> tuple[dict, int, str]:
    host_id, host_token = _create_authenticated_user(
        session_factory,
        "demo_user_1",
        display_name="Demo Host",
    )
    _act_as(client, host_token)
    response = client.post("/rooms")
    assert response.status_code == 201
    return response.json(), host_id, host_token


def test_ct_pb05_01_valid_code_adds_guest_and_exposes_member_to_room(client, session_factory):
    room, host_id, _ = _create_room_for_host(client, session_factory)
    guest_id, guest_token = _create_authenticated_user(
        session_factory,
        "demo_user_2",
        display_name="Convidada",
    )

    _act_as(client, guest_token)
    join_response = client.post(f"/rooms/{room['code'].lower()}/join")

    assert join_response.status_code == 200
    assert [member["user_id"] for member in join_response.json()["members"]] == [
        host_id,
        guest_id,
    ]
    assert join_response.json()["members"][1]["role"] == "member"

    get_response = client.get(f"/rooms/{room['code']}")
    assert get_response.status_code == 200
    assert get_response.json()["members"] == join_response.json()["members"]


def test_ct_pb05_02_unknown_and_expired_rooms_reject_join_without_association(
    client,
    session_factory,
):
    room, host_id, _ = _create_room_for_host(client, session_factory)
    guest_id, guest_token = _create_authenticated_user(session_factory, "demo_user_2")

    db = session_factory()
    try:
        expired_room, _ = room_service.create_room(
            db,
            host_id,
            now=datetime.now(timezone.utc) - timedelta(hours=25),
        )
        expired_code = expired_room.code
    finally:
        db.close()

    _act_as(client, guest_token)
    missing_response = client.post("/rooms/ZZZZ-ZZZZ/join")
    expired_response = client.post(f"/rooms/{expired_code}/join")

    assert missing_response.status_code == 404
    assert missing_response.json() == {"detail": "Sala não encontrada."}
    assert expired_response.status_code == 410
    assert expired_response.json() == {"detail": "Esta sala expirou."}

    db = session_factory()
    try:
        assert (
            db.query(MusicSessionMember)
            .filter(MusicSessionMember.user_id == guest_id)
            .count()
            == 0
        )
        assert db.query(MusicSessionMember).count() == 2
        assert room["code"] != expired_code
    finally:
        db.close()


def test_ct_pb05_03_sixth_member_is_rejected_and_count_stays_at_five(client, session_factory):
    room, _, _ = _create_room_for_host(client, session_factory)

    for index in range(2, 6):
        _, token = _create_authenticated_user(session_factory, f"demo_user_{index}")
        _act_as(client, token)
        assert client.post(f"/rooms/{room['code']}/join").status_code == 200

    sixth_id, sixth_token = _create_authenticated_user(session_factory, "demo_user_6")
    _act_as(client, sixth_token)
    response = client.post(f"/rooms/{room['code']}/join")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "A sala já atingiu o limite de cinco integrantes."
    }
    db = session_factory()
    try:
        memberships = db.query(MusicSessionMember).all()
        assert len(memberships) == 5
        assert sixth_id not in {membership.user_id for membership in memberships}
    finally:
        db.close()


def test_ct_pb05_04_duplicate_join_is_idempotent_even_when_room_is_full(client, session_factory):
    room, _, _ = _create_room_for_host(client, session_factory)
    guest_id = None
    guest_token = None
    for index in range(2, 6):
        user_id, token = _create_authenticated_user(session_factory, f"demo_user_{index}")
        _act_as(client, token)
        assert client.post(f"/rooms/{room['code']}/join").status_code == 200
        if index == 2:
            guest_id, guest_token = user_id, token

    _act_as(client, guest_token)
    duplicate_response = client.post(f"/rooms/{room['code']}/join")

    assert duplicate_response.status_code == 200
    assert len(duplicate_response.json()["members"]) == 5
    db = session_factory()
    try:
        assert (
            db.query(MusicSessionMember)
            .filter(MusicSessionMember.user_id == guest_id)
            .count()
            == 1
        )
    finally:
        db.close()


def test_ct_pb05_05_non_member_gets_403_without_room_payload(client, session_factory):
    room, _, _ = _create_room_for_host(client, session_factory)
    _, outsider_token = _create_authenticated_user(
        session_factory,
        "private_outsider",
        display_name="Pessoa Externa",
    )
    _act_as(client, outsider_token)

    response = client.get(f"/rooms/{room['code']}")

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Apenas integrantes podem consultar esta sala."
    }
    serialized = response.text.lower()
    assert room["id"].lower() not in serialized
    assert "demo host" not in serialized


def test_ct_pb05_06_next_poll_reflects_member_who_joined(client, session_factory):
    room, _, host_token = _create_room_for_host(client, session_factory)
    _, guest_token = _create_authenticated_user(
        session_factory,
        "demo_user_2",
        display_name="Novo Membro",
    )

    first_poll = client.get(f"/rooms/{room['code']}")
    assert len(first_poll.json()["members"]) == 1

    _act_as(client, guest_token)
    assert client.post(f"/rooms/{room['code']}/join").status_code == 200

    _act_as(client, host_token)
    second_poll = client.get(f"/rooms/{room['code']}")
    assert second_poll.status_code == 200
    assert [member["display_name"] for member in second_poll.json()["members"]] == [
        "Demo Host",
        "Novo Membro",
    ]


def test_ct_pb05_07_room_state_is_consistent_across_reload(client, session_factory):
    room, _, host_token = _create_room_for_host(client, session_factory)
    _, guest_token = _create_authenticated_user(session_factory, "demo_user_2")
    _act_as(client, guest_token)
    assert client.post(f"/rooms/{room['code']}/join").status_code == 200

    _act_as(client, host_token)
    first_read = client.get(f"/rooms/{room['code']}")
    second_read = client.get(f"/rooms/{room['code']}")

    assert first_read.status_code == second_read.status_code == 200
    assert first_read.json() == second_read.json()


def test_join_requires_authentication(client, session_factory):
    room, _, _ = _create_room_for_host(client, session_factory)
    client.cookies.clear()

    response = client.post(f"/rooms/{room['code']}/join")

    assert response.status_code == 401


def test_join_query_locks_room_row_in_postgresql():
    statement = room_service._room_for_join_statement("abcd1234")

    sql = str(statement.compile(dialect=postgresql.dialect()))

    assert "FOR UPDATE" in sql
    assert statement.compile(dialect=postgresql.dialect()).params == {"code_1": "ABCD-1234"}


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL não configurada para o teste concorrente no PostgreSQL.",
)
def test_ct_pb05_03_concurrent_joins_never_exceed_five_members_in_postgresql():
    """Exercita no banco alvo a serialização garantida por SELECT FOR UPDATE."""
    engine = create_engine(os.environ["TEST_DATABASE_URL"], future=True)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    db = factory()
    try:
        run_id = uuid4().hex
        users = [
            User(
                spotify_id=f"pb05_parallel_{run_id}_{index}",
                display_name=f"Parallel {index}",
            )
            for index in range(6)
        ]
        db.add_all(users)
        db.flush()
        user_ids = [user.id for user in users]
        room, _ = room_service.create_room(db, user_ids[0])
        room_id = room.id
        room_code = room.code
    finally:
        db.close()

    def join_one(user_id: int) -> str:
        worker_db = factory()
        try:
            room_service.join_room(worker_db, room_code, user_id)
            return "joined"
        except room_service.RoomFullError:
            return "full"
        finally:
            worker_db.close()

    try:
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(join_one, user_ids[1:]))

        assert results.count("joined") == 4
        assert results.count("full") == 1
        db = factory()
        try:
            assert (
                db.query(MusicSessionMember)
                .filter(MusicSessionMember.session_id == room_id)
                .count()
                == 5
            )
        finally:
            db.close()
    finally:
        cleanup_db = factory()
        try:
            cleanup_db.query(User).filter(User.id.in_(user_ids)).delete(
                synchronize_session=False
            )
            cleanup_db.commit()
        finally:
            cleanup_db.close()
            engine.dispose()
