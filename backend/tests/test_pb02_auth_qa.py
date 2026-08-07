"""Testes adicionais de autenticação, segurança e sessão do Spotify.

As chamadas externas são simuladas e nenhuma credencial real é utilizada.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.clients import crypto, spotify_client
from app.config import settings
from app.db.base import Base
from app.db.models import AppSession, SpotifyToken, User
from app.db.session import get_db
from app.main import app

# --- Fixtures de ambiente de teste ------------------------------------------

FAKE_ACCESS = "ACCESS_TOKEN_FAKE_do_teste"
FAKE_REFRESH = "REFRESH_TOKEN_FAKE_do_teste"

# O caminho de sessão do PB-02 usa colunas DateTime(timezone=True). Em SQLite o
# valor volta "naive" e a comparação com datetime aware quebra (ver DEF-PB02).
# O alvo real do produto é Postgres; se DATABASE_URL apontar para ele, validamos
# contra o alvo real. Caso contrário, os casos dependentes de sessão são pulados.
_DB_URL = os.environ.get("DATABASE_URL")
_USE_PG = bool(_DB_URL and _DB_URL.startswith("postgresql"))


@pytest.fixture()
def db_session():
    """Sessão de teste. Usa Postgres real quando DATABASE_URL está definido
    (alvo do produto); senão SQLite em memória (limitado para o path de sessão)."""
    if _USE_PG:
        engine = create_engine(_DB_URL, future=True)
        Base.metadata.create_all(engine)
        TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
        # limpeza antes e depois (isolamento entre testes)
        _wipe(TestingSession)
        yield TestingSession
        _wipe(TestingSession)
    else:
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            future=True,
        )
        Base.metadata.create_all(engine)
        TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
        yield TestingSession
        Base.metadata.drop_all(engine)


def _wipe(SessionFactory) -> None:
    s = SessionFactory()
    try:
        s.query(AppSession).delete()
        s.query(SpotifyToken).delete()
        s.query(User).delete()
        s.commit()
    finally:
        s.close()


@pytest.fixture()
def client(db_session, monkeypatch) -> Iterator[TestClient]:
    # get_db aponta para o SQLite de teste
    def _override_get_db():
        db = db_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db

    # Chave Fernet determinística para o teste (nunca é um segredo real)
    monkeypatch.setattr(settings, "fernet_key", Fernet.generate_key().decode())
    crypto._fernet = None  # força recriar com a chave do teste

    # Config do Spotify para /login (valores fictícios)
    monkeypatch.setattr(settings, "spotify_client_id", "fake_client_id")
    monkeypatch.setattr(settings, "spotify_client_secret", "fake_client_secret")
    monkeypatch.setattr(settings, "spotify_redirect_uri", "http://localhost:8000/auth/callback")

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    crypto._fernet = None


def _mock_spotify_ok(monkeypatch, spotify_id="demo_user_1", display_name="Demo User"):
    async def _exchange(code: str):
        return {
            "access_token": FAKE_ACCESS,
            "refresh_token": FAKE_REFRESH,
            "expires_in": 3600,
            "scope": "user-top-read playlist-modify-private user-read-private",
        }

    async def _profile(access_token: str):
        return {
            "id": spotify_id,
            "display_name": display_name,
            "images": [{"url": "http://img/x.png"}],
        }

    monkeypatch.setattr(spotify_client, "exchange_code_for_token", _exchange)
    monkeypatch.setattr(spotify_client, "get_current_user_profile", _profile)


# --- CT-PB02-01 -------------------------------------------------------------

def test_ct_pb02_01_login_redirects_to_spotify(client):
    resp = client.get("/auth/login", follow_redirects=False)
    assert resp.status_code in (302, 307), f"esperado redirect, veio {resp.status_code}"
    loc = resp.headers["location"]
    assert loc.startswith("https://accounts.spotify.com/authorize")
    assert "state=" in loc
    assert "user-top-read" in loc and "playlist-modify-private" in loc
    # state deve ser guardado em cookie httpOnly
    set_cookie = resp.headers.get("set-cookie", "")
    assert "spotify_auth_state=" in set_cookie
    assert "httponly" in set_cookie.lower()


# --- CT-PB02-02 (CSRF) ------------------------------------------------------

def test_ct_pb02_02_callback_rejects_bad_state(client, monkeypatch, db_session):
    _mock_spotify_ok(monkeypatch)
    # state divergente do cookie
    client.cookies.set("spotify_auth_state", "STATE_A")
    resp = client.get("/auth/callback?code=abc&state=STATE_B", follow_redirects=False)
    assert resp.status_code == 400
    # nenhuma sessão/usuário criado
    s = db_session()
    try:
        assert s.query(User).count() == 0
        assert s.query(AppSession).count() == 0
    finally:
        s.close()


def test_ct_pb02_02b_callback_rejects_missing_state_cookie(client, monkeypatch):
    _mock_spotify_ok(monkeypatch)
    client.cookies.clear()
    resp = client.get("/auth/callback?code=abc&state=STATE_X", follow_redirects=False)
    assert resp.status_code == 400


# --- CT-PB02-03 (cria/atualiza usuário e sessão; idempotência) --------------

def test_ct_pb02_03_valid_callback_creates_user_and_session(client, monkeypatch, db_session):
    _mock_spotify_ok(monkeypatch, display_name="Primeiro Nome")
    client.cookies.set("spotify_auth_state", "S1")
    r1 = client.get("/auth/callback?code=code1&state=S1", follow_redirects=False)
    assert r1.status_code in (302, 307)

    # segunda autorização do MESMO spotify_id (nome atualizado) — não deve duplicar user
    _mock_spotify_ok(monkeypatch, display_name="Nome Atualizado")
    client.cookies.set("spotify_auth_state", "S2")
    r2 = client.get("/auth/callback?code=code2&state=S2", follow_redirects=False)
    assert r2.status_code in (302, 307)

    s = db_session()
    try:
        users = s.query(User).all()
        assert len(users) == 1, "usuário duplicado para o mesmo spotify_id"
        assert users[0].display_name == "Nome Atualizado", "perfil não foi atualizado no 2º login"
        # /auth/me deve reconhecer a sessão via cookie
    finally:
        s.close()

    me = client.get("/auth/me")
    assert me.status_code == 200
    body = me.json()
    assert body["spotify_id"] == "demo_user_1"


def test_ct_pb02_03b_me_without_session_is_401(client):
    client.cookies.clear()
    resp = client.get("/auth/me")
    assert resp.status_code == 401


# --- CT-PB02-04 (token nunca no frontend/resposta) --------------------------

def test_ct_pb02_04_tokens_never_in_responses(client, monkeypatch):
    _mock_spotify_ok(monkeypatch)
    client.cookies.set("spotify_auth_state", "S1")
    cb = client.get("/auth/callback?code=code1&state=S1", follow_redirects=False)
    # corpo do callback e Set-Cookie não podem conter o access/refresh token
    blob = cb.text + " " + cb.headers.get("set-cookie", "")
    assert FAKE_ACCESS not in blob
    assert FAKE_REFRESH not in blob

    me = client.get("/auth/me")
    assert FAKE_ACCESS not in me.text
    assert FAKE_REFRESH not in me.text
    # o cookie de sessão não é o token do Spotify
    assert "access_token" not in me.text and "refresh_token" not in me.text


# --- CT-PB02-05 (tokens criptografados em repouso) --------------------------

def test_ct_pb02_05_tokens_encrypted_at_rest(client, monkeypatch, db_session):
    _mock_spotify_ok(monkeypatch)
    client.cookies.set("spotify_auth_state", "S1")
    client.get("/auth/callback?code=code1&state=S1", follow_redirects=False)

    s = db_session()
    try:
        tok = s.query(SpotifyToken).one()
        # valor persistido NÃO pode ser o token em claro
        assert tok.access_token != FAKE_ACCESS
        assert tok.refresh_token != FAKE_REFRESH
        # e deve ser recuperável apenas via a chave (Fernet)
        assert crypto.decrypt(tok.access_token) == FAKE_ACCESS
        assert crypto.decrypt(tok.refresh_token) == FAKE_REFRESH
    finally:
        s.close()


# --- CT-PB02-06 (refresh e reauth) — validação de COMPORTAMENTO -------------

import asyncio


def _seed_token(SessionFactory, *, expired: bool, reauth: bool = False):
    """Cria user + SpotifyToken num estado controlado; devolve user_id."""
    s = SessionFactory()
    try:
        u = User(spotify_id="refresh_user")
        s.add(u)
        s.flush()
        delta = timedelta(minutes=-1) if expired else timedelta(hours=1)
        tok = SpotifyToken(
            user_id=u.id,
            access_token=crypto.encrypt("access_atual"),
            refresh_token=crypto.encrypt("refresh_valido"),
            token_expires_at=datetime.now(timezone.utc) + delta,
            reauth_required_at=datetime.now(timezone.utc) if reauth else None,
        )
        s.add(tok)
        s.commit()
        return u.id
    finally:
        s.close()


@pytest.fixture()
def _fernet(monkeypatch):
    monkeypatch.setattr(settings, "fernet_key", Fernet.generate_key().decode())
    crypto._fernet = None
    yield
    crypto._fernet = None


def test_ct_pb02_06a_valid_token_is_reused_without_refresh(db_session, _fernet, monkeypatch):
    uid = _seed_token(db_session, expired=False)

    async def _must_not_call(_r):  # refresh não deve ser chamado com token válido
        raise AssertionError("refresh_access_token não deveria ser chamado")

    monkeypatch.setattr(spotify_client, "refresh_access_token", _must_not_call)
    s = db_session()
    try:
        token = asyncio.run(spotify_client.get_valid_access_token(s, uid))
        assert token == "access_atual"
    finally:
        s.close()


def test_ct_pb02_06b_expired_token_is_refreshed_and_persisted(db_session, _fernet, monkeypatch):
    uid = _seed_token(db_session, expired=True)

    async def _refresh(_r):
        return {"access_token": "access_novo", "expires_in": 3600, "scope": "user-top-read"}

    monkeypatch.setattr(spotify_client, "refresh_access_token", _refresh)
    s = db_session()
    try:
        token = asyncio.run(spotify_client.get_valid_access_token(s, uid))
        assert token == "access_novo"
    finally:
        s.close()
    # persistido cifrado e reauth limpo
    s2 = db_session()
    try:
        tok = s2.query(SpotifyToken).filter(SpotifyToken.user_id == uid).one()
        assert crypto.decrypt(tok.access_token) == "access_novo"
        assert tok.reauth_required_at is None
    finally:
        s2.close()


def test_ct_pb02_06c_failed_refresh_marks_reauth(db_session, _fernet, monkeypatch):
    uid = _seed_token(db_session, expired=True)

    async def _boom(_r):
        raise RuntimeError("falha externa")

    monkeypatch.setattr(spotify_client, "refresh_access_token", _boom)
    s = db_session()
    try:
        with pytest.raises(spotify_client.ReauthenticationRequired):
            asyncio.run(spotify_client.get_valid_access_token(s, uid))
    finally:
        s.close()
    s2 = db_session()
    try:
        tok = s2.query(SpotifyToken).filter(SpotifyToken.user_id == uid).one()
        assert tok.reauth_required_at is not None
    finally:
        s2.close()


def test_ct_pb02_06d_reauth_flagged_token_raises(db_session, _fernet):
    uid = _seed_token(db_session, expired=False, reauth=True)
    s = db_session()
    try:
        with pytest.raises(spotify_client.ReauthenticationRequired):
            asyncio.run(spotify_client.get_valid_access_token(s, uid))
    finally:
        s.close()
