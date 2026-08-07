"""Testes técnicos do implementador para o PB-06 (contexto e consenso)."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.auth import SESSION_COOKIE_NAME
from app.db.base import Base
from app.db.models import AppSession, MusicSession, User
from app.db.session import get_db
from app.main import app


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pb06.sqlite3'}",
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
    display_name: str,
) -> tuple[int, str]:
    raw_token = f"session-for-{spotify_id}"
    db = session_factory()
    try:
        user = User(spotify_id=spotify_id, display_name=display_name)
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


def _create_room_with_member(client, session_factory) -> tuple[dict, int, str, int, str]:
    host_id, host_token = _create_authenticated_user(
        session_factory,
        "pb06_host",
        display_name="Host PB06",
    )
    member_id, member_token = _create_authenticated_user(
        session_factory,
        "pb06_member",
        display_name="Membro PB06",
    )
    _act_as(client, host_token)
    room_response = client.post("/rooms")
    assert room_response.status_code == 201
    room = room_response.json()

    _act_as(client, member_token)
    assert client.post(f"/rooms/{room['code']}/join").status_code == 200
    return room, host_id, host_token, member_id, member_token


def test_ct_pb06_01_only_host_changes_context_and_mode(client, session_factory):
    room, _, host_token, _, member_token = _create_room_with_member(client, session_factory)

    _act_as(client, host_token)
    context_response = client.put(
        f"/rooms/{room['code']}/context",
        json={"occasion": "Festa", "description": "Aniversário no terraço"},
    )
    mode_response = client.put(
        f"/rooms/{room['code']}/mode",
        json={"mode": "Democrático"},
    )
    assert context_response.status_code == mode_response.status_code == 200

    _act_as(client, member_token)
    denied_context = client.put(
        f"/rooms/{room['code']}/context",
        json={"occasion": "Estudo"},
    )
    denied_mode = client.put(
        f"/rooms/{room['code']}/mode",
        json={"mode": "Festa Segura"},
    )

    assert denied_context.status_code == denied_mode.status_code == 403
    assert denied_context.json() == denied_mode.json() == {
        "detail": "Somente o host pode alterar esta sala."
    }
    persisted = client.get(f"/rooms/{room['code']}").json()
    assert persisted["occasion"] == "Festa"
    assert persisted["description"] == "Aniversário no terraço"
    assert persisted["mode"] == "Democrático"


@pytest.mark.parametrize(
    ("payload", "expected_occasion", "expected_description"),
    [
        ({"occasion": "Festa"}, "Festa", None),
        ({"description": "Clima descontraído"}, None, "Clima descontraído"),
        (
            {"occasion": "Viagem", "description": "Estrada ao pôr do sol"},
            "Viagem",
            "Estrada ao pôr do sol",
        ),
    ],
)
def test_ct_pb06_02_accepts_occasion_description_or_both(
    client,
    session_factory,
    payload,
    expected_occasion,
    expected_description,
):
    room, _, host_token, _, _ = _create_room_with_member(client, session_factory)
    _act_as(client, host_token)

    response = client.put(f"/rooms/{room['code']}/context", json=payload)

    assert response.status_code == 200
    assert response.json()["occasion"] == expected_occasion
    assert response.json()["description"] == expected_description

    db = session_factory()
    try:
        persisted = db.query(MusicSession).filter(MusicSession.code == room["code"]).one()
        assert persisted.occasion == expected_occasion
        assert persisted.description == expected_description
    finally:
        db.close()


def test_context_rejects_empty_or_oversized_values_without_changing_room(client, session_factory):
    room, _, host_token, _, _ = _create_room_with_member(client, session_factory)
    _act_as(client, host_token)
    assert client.put(
        f"/rooms/{room['code']}/context",
        json={"occasion": "Churrasco"},
    ).status_code == 200

    empty_response = client.put(f"/rooms/{room['code']}/context", json={})
    oversized_response = client.put(
        f"/rooms/{room['code']}/context",
        json={"description": "x" * 1001},
    )

    assert empty_response.status_code == oversized_response.status_code == 422
    assert client.get(f"/rooms/{room['code']}").json()["occasion"] == "Churrasco"


@pytest.mark.parametrize("mode", ["Democrático", "Festa Segura"])
def test_valid_consensus_modes_are_persisted(client, session_factory, mode):
    room, _, host_token, _, _ = _create_room_with_member(client, session_factory)
    _act_as(client, host_token)

    response = client.put(f"/rooms/{room['code']}/mode", json={"mode": mode})

    assert response.status_code == 200
    assert response.json()["mode"] == mode
    db = session_factory()
    try:
        assert db.query(MusicSession).filter(MusicSession.code == room["code"]).one().mode == mode
    finally:
        db.close()


def test_ct_pb06_03_invalid_mode_is_rejected_without_changing_current_mode(
    client,
    session_factory,
):
    room, _, host_token, _, _ = _create_room_with_member(client, session_factory)
    _act_as(client, host_token)
    assert client.put(
        f"/rooms/{room['code']}/mode",
        json={"mode": "Democrático"},
    ).status_code == 200

    response = client.put(
        f"/rooms/{room['code']}/mode",
        json={"mode": "qualquer"},
    )

    assert response.status_code == 422
    assert client.get(f"/rooms/{room['code']}").json()["mode"] == "Democrático"


def test_ct_pb06_04_member_poll_sees_context_and_mode_updated_by_host(
    client,
    session_factory,
):
    room, _, host_token, _, member_token = _create_room_with_member(client, session_factory)
    _act_as(client, member_token)
    before = client.get(f"/rooms/{room['code']}").json()
    assert before["occasion"] is before["description"] is before["mode"] is None

    _act_as(client, host_token)
    assert client.put(
        f"/rooms/{room['code']}/context",
        json={"occasion": "Academia", "description": "Treino intenso"},
    ).status_code == 200
    assert client.put(
        f"/rooms/{room['code']}/mode",
        json={"mode": "Festa Segura"},
    ).status_code == 200

    _act_as(client, member_token)
    next_poll = client.get(f"/rooms/{room['code']}")
    assert next_poll.status_code == 200
    assert next_poll.json()["occasion"] == "Academia"
    assert next_poll.json()["description"] == "Treino intenso"
    assert next_poll.json()["mode"] == "Festa Segura"


def test_ct_pb06_05_context_survives_repeated_reads_and_database_reload(
    client,
    session_factory,
):
    room, _, host_token, _, _ = _create_room_with_member(client, session_factory)
    _act_as(client, host_token)
    assert client.put(
        f"/rooms/{room['code']}/context",
        json={"occasion": "Estudo", "description": "Sem letras, foco total"},
    ).status_code == 200
    assert client.put(
        f"/rooms/{room['code']}/mode",
        json={"mode": "Democrático"},
    ).status_code == 200

    first_reload = client.get(f"/rooms/{room['code']}")
    second_reload = client.get(f"/rooms/{room['code']}")
    assert first_reload.status_code == second_reload.status_code == 200
    assert first_reload.json() == second_reload.json()

    db = session_factory()
    try:
        persisted = db.query(MusicSession).filter(MusicSession.code == room["code"]).one()
        assert (persisted.occasion, persisted.description, persisted.mode) == (
            "Estudo",
            "Sem letras, foco total",
            "Democrático",
        )
    finally:
        db.close()
