"""Testes adicionais de contexto, consenso, autorização e salas expiradas."""

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
        f"sqlite:///{tmp_path / 'pb06_qa.sqlite3'}",
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


def _authenticated_user(session_factory, spotify_id: str) -> str:
    raw_token = f"qa-session-for-{spotify_id}"
    db = session_factory()
    try:
        user = User(spotify_id=spotify_id, display_name=f"QA {spotify_id}")
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
        return raw_token
    finally:
        db.close()


def _act_as(client: TestClient, token: str) -> None:
    client.cookies.set(SESSION_COOKIE_NAME, token)


def _room_with_host(client, session_factory, suffix: str = "") -> tuple[dict, str]:
    host_token = _authenticated_user(session_factory, f"qa_pb06_host{suffix}")
    _act_as(client, host_token)
    response = client.post("/rooms")
    assert response.status_code == 201
    return response.json(), host_token


def _read_state(session_factory, code: str) -> tuple:
    db = session_factory()
    try:
        room = db.query(MusicSession).filter(MusicSession.code == code).one()
        return room.occasion, room.description, room.mode
    finally:
        db.close()


# --- Autorização -----------------------------------------------------------


def test_qa_outsider_who_never_joined_cannot_change_context_or_mode(
    client, session_factory
):
    """Não-membro (sequer entrou na sala) deve ser barrado, não só o membro comum."""
    room, host_token = _room_with_host(client, session_factory)
    _act_as(client, host_token)
    assert client.put(
        f"/rooms/{room['code']}/context", json={"occasion": "Original"}
    ).status_code == 200

    outsider_token = _authenticated_user(session_factory, "qa_pb06_outsider")
    _act_as(client, outsider_token)

    context_response = client.put(
        f"/rooms/{room['code']}/context", json={"occasion": "Invasão"}
    )
    mode_response = client.put(f"/rooms/{room['code']}/mode", json={"mode": "Festa Segura"})

    assert context_response.status_code == 403
    assert mode_response.status_code == 403
    assert _read_state(session_factory, room["code"]) == ("Original", None, None)


def test_qa_unauthenticated_request_is_rejected_without_touching_state(
    client, session_factory
):
    room, host_token = _room_with_host(client, session_factory)
    _act_as(client, host_token)
    assert client.put(
        f"/rooms/{room['code']}/context", json={"occasion": "Original"}
    ).status_code == 200

    client.cookies.clear()
    context_response = client.put(
        f"/rooms/{room['code']}/context", json={"occasion": "Anônimo"}
    )
    mode_response = client.put(f"/rooms/{room['code']}/mode", json={"mode": "Democrático"})

    assert context_response.status_code == 401
    assert mode_response.status_code == 401
    assert _read_state(session_factory, room["code"]) == ("Original", None, None)


def test_qa_unknown_room_returns_404_not_403(client, session_factory):
    host_token = _authenticated_user(session_factory, "qa_pb06_ghost")
    _act_as(client, host_token)

    assert client.put("/rooms/ZZZZ-9999/context", json={"occasion": "x"}).status_code == 404
    assert client.put("/rooms/ZZZZ-9999/mode", json={"mode": "Democrático"}).status_code == 404


def test_qa_host_of_one_room_cannot_edit_another_room(client, session_factory):
    """Ser host em algum lugar não concede poder sobre a sala alheia."""
    victim_room, victim_token = _room_with_host(client, session_factory, suffix="_victim")
    _act_as(client, victim_token)
    assert client.put(
        f"/rooms/{victim_room['code']}/mode", json={"mode": "Democrático"}
    ).status_code == 200

    _, attacker_token = _room_with_host(client, session_factory, suffix="_attacker")
    _act_as(client, attacker_token)

    response = client.put(f"/rooms/{victim_room['code']}/mode", json={"mode": "Festa Segura"})

    assert response.status_code == 403
    assert _read_state(session_factory, victim_room["code"])[2] == "Democrático"


# --- Entradas inválidas e limites -----------------------------------------


@pytest.mark.parametrize(
    "payload",
    [
        {"occasion": "   ", "description": "\t\n "},
        {"occasion": "", "description": ""},
        {"occasion": None, "description": None},
    ],
)
def test_qa_blank_only_context_is_rejected(client, session_factory, payload):
    """Espaços em branco não podem burlar a exigência de ao menos um valor."""
    room, host_token = _room_with_host(client, session_factory)
    _act_as(client, host_token)

    response = client.put(f"/rooms/{room['code']}/context", json=payload)

    assert response.status_code == 422
    assert _read_state(session_factory, room["code"]) == (None, None, None)


def test_qa_context_length_boundaries(client, session_factory):
    """100/1000 caracteres passam; 101/1001 são recusados."""
    room, host_token = _room_with_host(client, session_factory)
    _act_as(client, host_token)

    at_limit = client.put(
        f"/rooms/{room['code']}/context",
        json={"occasion": "o" * 100, "description": "d" * 1000},
    )
    assert at_limit.status_code == 200

    over_occasion = client.put(f"/rooms/{room['code']}/context", json={"occasion": "o" * 101})
    over_description = client.put(
        f"/rooms/{room['code']}/context", json={"description": "d" * 1001}
    )

    assert over_occasion.status_code == 422
    assert over_description.status_code == 422
    occasion, description, _ = _read_state(session_factory, room["code"])
    assert (len(occasion), len(description)) == (100, 1000)


def test_qa_whitespace_is_trimmed_before_persisting(client, session_factory):
    room, host_token = _room_with_host(client, session_factory)
    _act_as(client, host_token)

    response = client.put(
        f"/rooms/{room['code']}/context",
        json={"occasion": "  Festa  ", "description": "  Terraço  "},
    )

    assert response.status_code == 200
    assert _read_state(session_factory, room["code"])[:2] == ("Festa", "Terraço")


@pytest.mark.parametrize(
    "payload",
    [
        {"mode": "democrático"},
        {"mode": "DEMOCRÁTICO"},
        {"mode": "Democratico"},
        {"mode": "Descoberta"},
        {"mode": ""},
        {"mode": None},
        {},
        {"mode": 1},
    ],
)
def test_qa_mode_enum_is_closed(client, session_factory, payload):
    """Só os dois nomes públicos exatos do MVP entram; nada de variantes."""
    room, host_token = _room_with_host(client, session_factory)
    _act_as(client, host_token)
    assert client.put(
        f"/rooms/{room['code']}/mode", json={"mode": "Democrático"}
    ).status_code == 200

    response = client.put(f"/rooms/{room['code']}/mode", json=payload)

    assert response.status_code == 422
    assert _read_state(session_factory, room["code"])[2] == "Democrático"


# --- Semântica de substituição e propagação -------------------------------


def test_qa_context_put_replaces_instead_of_merging(client, session_factory):
    """Decisão documentada: PUT substitui o par. Enviar só ocasião limpa a descrição."""
    room, host_token = _room_with_host(client, session_factory)
    _act_as(client, host_token)
    assert client.put(
        f"/rooms/{room['code']}/context",
        json={"occasion": "Festa", "description": "Aniversário"},
    ).status_code == 200

    response = client.put(f"/rooms/{room['code']}/context", json={"occasion": "Estudo"})

    assert response.status_code == 200
    assert response.json()["description"] is None
    assert _read_state(session_factory, room["code"])[:2] == ("Estudo", None)


def test_qa_mode_change_does_not_disturb_context(client, session_factory):
    room, host_token = _room_with_host(client, session_factory)
    _act_as(client, host_token)
    client.put(
        f"/rooms/{room['code']}/context",
        json={"occasion": "Festa", "description": "Aniversário"},
    )

    assert client.put(
        f"/rooms/{room['code']}/mode", json={"mode": "Festa Segura"}
    ).status_code == 200

    assert _read_state(session_factory, room["code"]) == ("Festa", "Aniversário", "Festa Segura")


def test_qa_repeated_rapid_updates_converge_to_last_write(client, session_factory):
    room, host_token = _room_with_host(client, session_factory)
    _act_as(client, host_token)

    for index in range(10):
        assert client.put(
            f"/rooms/{room['code']}/context", json={"occasion": f"Ocasião {index}"}
        ).status_code == 200

    assert _read_state(session_factory, room["code"])[0] == "Ocasião 9"


def test_qa_context_response_exposes_no_sensitive_fields(client, session_factory):
    """A resposta do lobby não pode vazar tokens nem o host_user_id interno."""
    room, host_token = _room_with_host(client, session_factory)
    _act_as(client, host_token)

    body = client.put(f"/rooms/{room['code']}/context", json={"occasion": "Festa"}).json()

    assert set(body) == {
        "id",
        "code",
        "status",
        "occasion",
        "description",
        "mode",
        "created_at",
        "expires_at",
        "members",
    }
    serialized = str(body)
    assert "token" not in serialized.lower()
    assert "host_user_id" not in serialized


# --- Sala expirada ---------------------------------------------------------


def test_qa_expired_room_context_update(client, session_factory):
    """Documenta o comportamento do host editando uma sala já expirada."""
    room, host_token = _room_with_host(client, session_factory)
    db = session_factory()
    try:
        stored = db.query(MusicSession).filter(MusicSession.code == room["code"]).one()
        stored.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        db.commit()
    finally:
        db.close()

    _act_as(client, host_token)
    response = client.put(f"/rooms/{room['code']}/context", json={"occasion": "Tardia"})

    # Comportamento atual, herdado do GET do PB-05, que também não filtra expiração.
    assert response.status_code == 200
    assert _read_state(session_factory, room["code"])[0] == "Tardia"
