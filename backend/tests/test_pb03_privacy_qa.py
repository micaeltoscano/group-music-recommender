"""QA (validador independente) — PB-03 (logout e remoção de dados).

Sondagem adversarial escrita pela autoridade de QA, não pelo implementador.
Cobre ângulos além dos testes do Dev:

- CT-PB03-01: logout invalida SÓ a sessão atual — outras sessões (outro
  dispositivo) do mesmo usuário sobrevivem; a remoção de conta, sim, mata todas.
- CT-PB03-02: `DELETE /auth/me` sem sessão → 401 (não dá pra apagar anônimo).
- CT-PB03-03: privacidade — resposta 204 do logout/delete não expõe token nem
  corpo; todos os artefatos pessoais somem.
- CT-PB03-04: apagar o **host** de uma sala com outros membros não destrói a
  sala nem os dados de terceiros (o cenário mais perigoso do `ON DELETE CASCADE`).
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.auth import SESSION_COOKIE_NAME
from app.db.base import Base
from app.db.models import (
    AppSession,
    MusicSession,
    MusicSessionMember,
    SpotifyToken,
    User,
    UserMusicSnapshot,
    VibeCheckAnswer,
)
from app.db.session import get_db
from app.main import app
from app.services.privacy_service import ANONYMIZED_DISPLAY_NAME


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pb03-qa.sqlite3'}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(engine)
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


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _add_session(db, user_id: int, token: str) -> None:
    db.add(
        AppSession(
            user_id=user_id,
            session_token_hash=_hash(token),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
    )


# ---------------------------------------------------------------------------
# CT-PB03-01 — logout invalida SÓ a sessão atual
# ---------------------------------------------------------------------------

def test_logout_preserva_outra_sessao_do_mesmo_usuario(client, session_factory):
    """Dois dispositivos: logout em um não deve derrubar o outro."""
    db = session_factory()
    try:
        user = User(spotify_id="qa_multi", display_name="Multi")
        db.add(user)
        db.flush()
        _add_session(db, user.id, "device-A")
        _add_session(db, user.id, "device-B")
        db.commit()
        uid = user.id
    finally:
        db.close()

    client.cookies.set(SESSION_COOKIE_NAME, "device-A")
    assert client.post("/auth/logout").status_code == 204

    db = session_factory()
    try:
        remaining = {s.session_token_hash for s in db.query(AppSession).filter_by(user_id=uid)}
        assert _hash("device-A") not in remaining, "sessão atual deveria ter sido invalidada"
        assert _hash("device-B") in remaining, "logout não pode derrubar outra sessão do usuário"
    finally:
        db.close()


# ---------------------------------------------------------------------------
# CT-PB03-02 — DELETE /me exige autenticação
# ---------------------------------------------------------------------------

def test_delete_me_sem_sessao_retorna_401(client):
    resp = client.delete("/auth/me")
    assert resp.status_code == 401


def test_delete_me_com_sessao_invalida_retorna_401(client):
    client.cookies.set(SESSION_COOKIE_NAME, "inexistente")
    assert client.delete("/auth/me").status_code == 401


# ---------------------------------------------------------------------------
# CT-PB03-03 — privacidade: respostas não expõem token; artefatos somem
# ---------------------------------------------------------------------------

def test_logout_e_delete_nao_expoem_token_no_corpo_nem_headers(client, session_factory):
    db = session_factory()
    try:
        user = User(spotify_id="qa_priv", display_name="Priv")
        db.add(user)
        db.flush()
        db.add(
            SpotifyToken(
                user_id=user.id,
                access_token="SEGREDO-ACCESS",
                refresh_token="SEGREDO-REFRESH",
                token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
        )
        _add_session(db, user.id, "priv-session")
        db.commit()
    finally:
        db.close()

    client.cookies.set(SESSION_COOKIE_NAME, "priv-session")
    resp = client.delete("/auth/me")
    assert resp.status_code == 204
    assert resp.content == b""  # 204 sem corpo
    blob = (resp.text + str(dict(resp.headers))).upper()
    assert "SEGREDO" not in blob
    assert "ACCESS" not in blob or "ACCESS-CONTROL" in blob  # não vaza o token


def test_delete_remove_todos_os_artefatos_pessoais(client, session_factory):
    db = session_factory()
    try:
        user = User(spotify_id="qa_wipe", display_name="Wipe", image_url="http://img/x.png")
        db.add(user)
        db.flush()
        uid = user.id
        db.add(
            SpotifyToken(
                user_id=uid,
                access_token="a",
                refresh_token="r",
                token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
        )
        _add_session(db, uid, "wipe-session")
        _add_session(db, uid, "wipe-session-2")
        room = MusicSession(
            code="QAWIPE01",
            host_user_id=uid,
            status="open",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
        db.add(room)
        db.flush()
        db.add(
            UserMusicSnapshot(
                user_id=uid,
                time_range="medium_term",
                top_tracks_json=[],
                top_artists_json=[],
                fetched_at=datetime.now(timezone.utc),
            )
        )
        db.add(VibeCheckAnswer(session_id=room.id, user_id=uid, energy=0.5, valence=0.5, popularity=0.5))
        db.commit()
    finally:
        db.close()

    client.cookies.set(SESSION_COOKIE_NAME, "wipe-session")
    assert client.delete("/auth/me").status_code == 204

    db = session_factory()
    try:
        assert db.query(SpotifyToken).filter_by(user_id=uid).count() == 0
        assert db.query(AppSession).filter_by(user_id=uid).count() == 0, "todas as sessões devem sumir"
        assert db.query(UserMusicSnapshot).filter_by(user_id=uid).count() == 0
        assert db.query(VibeCheckAnswer).filter_by(user_id=uid).count() == 0
        user = db.get(User, uid)
        assert user is not None  # linha preservada como sujeito anônimo
        assert user.display_name == ANONYMIZED_DISPLAY_NAME
        assert user.image_url is None
        assert user.spotify_id != "qa_wipe" and user.spotify_id.startswith("deleted-")
    finally:
        db.close()


# ---------------------------------------------------------------------------
# CT-PB03-04 — apagar o HOST não destrói a sala nem os dados de terceiros
# ---------------------------------------------------------------------------

def test_delete_do_host_preserva_sala_e_membros(client, session_factory):
    db = session_factory()
    try:
        host = User(spotify_id="qa_host", display_name="Host")
        guest = User(spotify_id="qa_guest", display_name="Guest", image_url="http://img/g.png")
        db.add_all([host, guest])
        db.flush()
        host_id, guest_id = host.id, guest.id
        db.add(
            SpotifyToken(
                user_id=guest_id, access_token="g-a", refresh_token="g-r",
                token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
        )
        _add_session(db, host_id, "host-session")
        _add_session(db, guest_id, "guest-session")
        room = MusicSession(
            code="QAHOST01", host_user_id=host_id, status="open",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
        db.add(room)
        db.flush()
        room_id = room.id
        db.add(MusicSessionMember(session_id=room_id, user_id=host_id, role="host"))
        db.add(MusicSessionMember(session_id=room_id, user_id=guest_id, role="member"))
        db.commit()
    finally:
        db.close()

    client.cookies.set(SESSION_COOKIE_NAME, "host-session")
    assert client.delete("/auth/me").status_code == 204

    db = session_factory()
    try:
        # sala preservada
        room = db.get(MusicSession, room_id)
        assert room is not None, "apagar o host NÃO pode destruir a sala"
        # convidado 100% intacto
        guest = db.get(User, guest_id)
        assert guest.display_name == "Guest"
        assert guest.image_url == "http://img/g.png"
        assert db.query(SpotifyToken).filter_by(user_id=guest_id).count() == 1
        assert db.query(AppSession).filter_by(user_id=guest_id).count() == 1
        # membership do convidado preservada
        assert (
            db.query(MusicSessionMember).filter_by(session_id=room_id, user_id=guest_id).count()
            == 1
        )
        # host anonimizado, mas ainda referenciável pela sala
        host = db.get(User, host_id)
        assert host.display_name == ANONYMIZED_DISPLAY_NAME
    finally:
        db.close()
