"""Testes adicionais de coleta, cache e isolamento dos dados musicais.

Todos os caminhos externos (Spotify) são mockados. Nenhuma credencial real.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.api.auth import SESSION_COOKIE_NAME
from app.clients import crypto, spotify_client
from app.config import settings
from app.db.base import Base
from app.db.models import AppSession, SpotifyToken, User, UserMusicSnapshot
from app.db.session import get_db
from app.services import music_service
from app.main import app

QA_TRACKS = [{"id": "qa-track", "name": "Faixa QA", "uri": "spotify:track:qa-track"}]
QA_ARTISTS = [{"id": "qa-artist", "name": "Artista QA", "genres": ["rock"]}]


@pytest.fixture(autouse=True)
def fernet_key(monkeypatch):
    monkeypatch.setattr(settings, "fernet_key", Fernet.generate_key().decode())
    crypto._fernet = None
    yield
    crypto._fernet = None


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pb08_qa.sqlite3'}",
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


def _make_user(session_factory, spotify_id: str) -> tuple[int, str]:
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
        return user.id, raw_token
    finally:
        db.close()


def _act_as(client: TestClient, token: str) -> None:
    client.cookies.set(SESSION_COOKIE_NAME, token)


def _seed_snapshot(session_factory, user_id, *, fetched_at, time_range="medium_term", tracks=None):
    db = session_factory()
    try:
        snapshot = UserMusicSnapshot(
            user_id=user_id,
            time_range=time_range,
            top_tracks_json=tracks if tracks is not None else QA_TRACKS,
            top_artists_json=QA_ARTISTS,
            fetched_at=fetched_at,
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        db.expunge(snapshot)
        return snapshot
    finally:
        db.close()


def _mock_spotify(monkeypatch, tracks=None, artists=None):
    async def valid_token(_db, _user_id):
        return "access-ficticio"

    async def top_tracks(_access_token, *, time_range, limit):
        return tracks if tracks is not None else QA_TRACKS

    async def top_artists(_access_token, *, time_range, limit):
        return artists if artists is not None else QA_ARTISTS

    monkeypatch.setattr(spotify_client, "get_valid_access_token", valid_token)
    monkeypatch.setattr(spotify_client, "get_top_tracks", top_tracks)
    monkeypatch.setattr(spotify_client, "get_top_artists", top_artists)


def _forbid_spotify(monkeypatch):
    async def forbidden(*_args, **_kwargs):
        raise AssertionError("O Spotify não deveria ser chamado neste cenário.")

    monkeypatch.setattr(spotify_client, "get_valid_access_token", forbidden)
    monkeypatch.setattr(spotify_client, "get_top_tracks", forbidden)
    monkeypatch.setattr(spotify_client, "get_top_artists", forbidden)


# --- Isolamento entre usuários --------------------------------------------


def test_qa_snapshot_of_one_user_never_leaks_to_another(client, session_factory, monkeypatch):
    """O snapshot é por usuário: B nunca enxerga os dados de A."""
    user_a, token_a = _make_user(session_factory, "qa_pb08_a")
    user_b, token_b = _make_user(session_factory, "qa_pb08_b")
    _seed_snapshot(
        session_factory,
        user_a,
        fetched_at=datetime.now(timezone.utc) - timedelta(hours=1),
        tracks=[{"id": "segredo-do-a", "name": "Só do A"}],
    )

    _mock_spotify(monkeypatch, tracks=[{"id": "track-do-b", "name": "Do B"}])
    _act_as(client, token_b)
    body = client.get("/me/top").json()

    assert body["user_id"] == user_b
    assert body["top_tracks"] == [{"id": "track-do-b", "name": "Do B"}]
    assert "segredo-do-a" not in str(body)

    db = session_factory()
    try:
        assert db.query(UserMusicSnapshot).count() == 2
        snapshot_a = db.query(UserMusicSnapshot).filter_by(user_id=user_a).one()
        assert snapshot_a.top_tracks_json == [{"id": "segredo-do-a", "name": "Só do A"}]
    finally:
        db.close()


def test_qa_fresh_snapshot_of_other_user_does_not_satisfy_cache(
    client, session_factory, monkeypatch
):
    """Cache fresco de A não pode ser reaproveitado como cache de B."""
    user_a, _ = _make_user(session_factory, "qa_pb08_owner")
    _, token_b = _make_user(session_factory, "qa_pb08_other")
    _seed_snapshot(session_factory, user_a, fetched_at=datetime.now(timezone.utc))

    _mock_spotify(monkeypatch)
    _act_as(client, token_b)
    body = client.get("/me/top").json()

    # Se o cache fosse global, viria cached=True sem chamar o Spotify.
    assert body["cached"] is False


# --- Fronteira exata do TTL ------------------------------------------------


@pytest.mark.parametrize(
    ("age", "expect_cached"),
    [
        (timedelta(days=6, hours=23, minutes=59), True),
        (timedelta(days=7, minutes=1), False),
        (timedelta(days=30), False),
    ],
)
def test_qa_ttl_boundary(client, session_factory, monkeypatch, age, expect_cached):
    """Decisão documentada: fresco somente com idade estritamente menor que 7 dias."""
    user_id, token = _make_user(session_factory, f"qa_pb08_ttl_{age.days}_{age.seconds}")
    _seed_snapshot(session_factory, user_id, fetched_at=datetime.now(timezone.utc) - age)
    if expect_cached:
        _forbid_spotify(monkeypatch)
    else:
        _mock_spotify(monkeypatch)

    _act_as(client, token)
    body = client.get("/me/top").json()

    assert body["cached"] is expect_cached


def test_qa_ttl_is_driven_by_configuration_not_hardcoded(client, session_factory, monkeypatch):
    """Com TTL de 1 dia, um snapshot de 2 dias precisa ser recoletado."""
    monkeypatch.setattr(settings, "music_snapshot_ttl_days", 1)
    user_id, token = _make_user(session_factory, "qa_pb08_ttl_cfg")
    _seed_snapshot(
        session_factory, user_id, fetched_at=datetime.now(timezone.utc) - timedelta(days=2)
    )
    _mock_spotify(monkeypatch)

    _act_as(client, token)

    assert client.get("/me/top").json()["cached"] is False


# --- Privacidade: nenhum token no snapshot ou na resposta ------------------


def test_qa_response_and_snapshot_never_contain_tokens(client, session_factory, monkeypatch):
    user_id, token = _make_user(session_factory, "qa_pb08_token")
    db = session_factory()
    try:
        db.add(
            SpotifyToken(
                user_id=user_id,
                access_token=crypto.encrypt("access-super-secreto"),
                refresh_token=crypto.encrypt("refresh-super-secreto"),
                token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
                scopes="user-top-read",
            )
        )
        db.commit()
    finally:
        db.close()

    _mock_spotify(monkeypatch)
    _act_as(client, token)
    body = client.post("/me/refresh-music-snapshot").json()

    serialized = str(body)
    for secret in ("access-super-secreto", "refresh-super-secreto", "access-ficticio"):
        assert secret not in serialized
    assert set(body) == {
        "snapshot_id",
        "user_id",
        "time_range",
        "top_tracks",
        "top_artists",
        "fetched_at",
        "cached",
        "stale",
        "warning",
    }

    db = session_factory()
    try:
        stored = db.query(UserMusicSnapshot).one()
        assert "secreto" not in str(stored.top_tracks_json) + str(stored.top_artists_json)
    finally:
        db.close()


# --- Reauth ----------------------------------------------------------------


def test_qa_reauth_flag_is_persisted_and_blocks_further_spotify_calls(
    client, session_factory, monkeypatch
):
    """Falha de refresh grava reauth_required_at; a chamada seguinte nem toca o Spotify."""
    user_id, token = _make_user(session_factory, "qa_pb08_reauth")
    db = session_factory()
    try:
        db.add(
            SpotifyToken(
                user_id=user_id,
                access_token=crypto.encrypt("expirado"),
                refresh_token=crypto.encrypt("refresh-ruim"),
                token_expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
                scopes="user-top-read",
            )
        )
        db.commit()
    finally:
        db.close()

    async def failed_refresh(_refresh_token):
        raise RuntimeError("refresh recusado pelo Spotify")

    monkeypatch.setattr(spotify_client, "refresh_access_token", failed_refresh)

    _act_as(client, token)
    first = client.get("/me/top")

    assert first.status_code == 401
    assert first.json()["detail"]["reauth_required"] is True

    db = session_factory()
    try:
        stored = db.query(SpotifyToken).filter_by(user_id=user_id).one()
        assert stored.reauth_required_at is not None
    finally:
        db.close()

    # Marcado para reauth: a rota deve barrar antes de qualquer chamada externa.
    async def forbidden_refresh(*_args, **_kwargs):
        raise AssertionError("Não deve tentar refresh depois de exigir reauth.")

    monkeypatch.setattr(spotify_client, "refresh_access_token", forbidden_refresh)
    second = client.get("/me/top")
    assert second.status_code == 401


def test_qa_user_without_spotify_token_gets_controlled_reauth_not_500(client, session_factory):
    """Sem token gravado, a resposta é 401 orientando novo login — nunca 500."""
    _, token = _make_user(session_factory, "qa_pb08_no_token")
    _act_as(client, token)

    response = client.get("/me/top")

    assert response.status_code == 401
    assert response.json()["detail"]["reauth_required"] is True


def test_qa_reauth_does_not_destroy_existing_fresh_snapshot(client, session_factory, monkeypatch):
    """Cache fresco continua servindo mesmo com reauth pendente (não chama o Spotify)."""
    user_id, token = _make_user(session_factory, "qa_pb08_reauth_cache")
    db = session_factory()
    try:
        db.add(
            SpotifyToken(
                user_id=user_id,
                access_token=crypto.encrypt("x"),
                refresh_token=crypto.encrypt("y"),
                token_expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
                scopes="user-top-read",
                reauth_required_at=datetime.now(timezone.utc),
            )
        )
        db.commit()
    finally:
        db.close()
    _seed_snapshot(session_factory, user_id, fetched_at=datetime.now(timezone.utc))
    _forbid_spotify(monkeypatch)

    _act_as(client, token)
    response = client.get("/me/top")

    assert response.status_code == 200
    assert response.json()["cached"] is True


# --- Entradas inválidas ----------------------------------------------------


@pytest.mark.parametrize("time_range", ["ontem", "", "MEDIUM_TERM", "1 year", "all_time"])
def test_qa_invalid_time_range_is_rejected(client, session_factory, monkeypatch, time_range):
    _, token = _make_user(session_factory, f"qa_pb08_tr_{abs(hash(time_range))}")
    _forbid_spotify(monkeypatch)
    _act_as(client, token)

    response = client.get("/me/top", params={"time_range": time_range})

    assert response.status_code == 422


def test_qa_time_ranges_do_not_overwrite_each_other(client, session_factory, monkeypatch):
    """Cada faixa temporal tem seu próprio snapshot; uma não sobrescreve a outra."""
    user_id, token = _make_user(session_factory, "qa_pb08_ranges")
    _mock_spotify(monkeypatch)
    _act_as(client, token)

    for time_range in ("short_term", "medium_term", "long_term"):
        assert client.get("/me/top", params={"time_range": time_range}).status_code == 200

    db = session_factory()
    try:
        assert db.query(UserMusicSnapshot).filter_by(user_id=user_id).count() == 3
    finally:
        db.close()


# --- Rate limit ------------------------------------------------------------


def test_qa_rate_limit_with_stale_cache_serves_stale_and_flags_it(
    client, session_factory, monkeypatch
):
    """429 com cache vencido: degrada servindo o vencido, mas sinaliza stale + aviso."""
    user_id, token = _make_user(session_factory, "qa_pb08_429_stale")
    _seed_snapshot(
        session_factory, user_id, fetched_at=datetime.now(timezone.utc) - timedelta(days=9)
    )

    async def valid_token(_db, _user_id):
        return "access-ficticio"

    async def rate_limited(*_args, **_kwargs):
        raise spotify_client.SpotifyRateLimited(42)

    monkeypatch.setattr(spotify_client, "get_valid_access_token", valid_token)
    monkeypatch.setattr(spotify_client, "get_top_tracks", rate_limited)

    _act_as(client, token)
    response = client.get("/me/top")

    assert response.status_code == 200
    body = response.json()
    assert body["stale"] is True
    assert body["cached"] is True
    assert body["warning"] is not None


def test_qa_rate_limit_without_cache_returns_429_with_retry_after(
    client, session_factory, monkeypatch
):
    _, token = _make_user(session_factory, "qa_pb08_429_bare")

    async def valid_token(_db, _user_id):
        return "access-ficticio"

    async def rate_limited(*_args, **_kwargs):
        raise spotify_client.SpotifyRateLimited(77)

    monkeypatch.setattr(spotify_client, "get_valid_access_token", valid_token)
    monkeypatch.setattr(spotify_client, "get_top_tracks", rate_limited)

    _act_as(client, token)
    response = client.get("/me/top")

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "77"


def test_qa_rate_limit_does_not_corrupt_existing_snapshot(client, session_factory, monkeypatch):
    """Um 429 no meio da coleta não pode gravar snapshot pela metade."""
    user_id, token = _make_user(session_factory, "qa_pb08_429_partial")
    _seed_snapshot(
        session_factory,
        user_id,
        fetched_at=datetime.now(timezone.utc) - timedelta(days=9),
        tracks=[{"id": "antigo"}],
    )

    async def valid_token(_db, _user_id):
        return "access-ficticio"

    async def ok_tracks(*_args, **_kwargs):
        return [{"id": "novo-parcial"}]

    async def rate_limited_artists(*_args, **_kwargs):
        raise spotify_client.SpotifyRateLimited(5)

    monkeypatch.setattr(spotify_client, "get_valid_access_token", valid_token)
    monkeypatch.setattr(spotify_client, "get_top_tracks", ok_tracks)
    monkeypatch.setattr(spotify_client, "get_top_artists", rate_limited_artists)

    _act_as(client, token)
    response = client.get("/me/top")

    assert response.status_code == 200
    db = session_factory()
    try:
        stored = db.query(UserMusicSnapshot).one()
        # As faixas antigas devem permanecer; nada de gravar só metade da coleta.
        assert stored.top_tracks_json == [{"id": "antigo"}]
    finally:
        db.close()


# --- Autenticação ----------------------------------------------------------


def test_qa_music_routes_reject_anonymous_and_bogus_session(client):
    assert client.get("/me/top").status_code == 401
    assert client.post("/me/refresh-music-snapshot").status_code == 401

    client.cookies.set(SESSION_COOKIE_NAME, "token-inventado")
    assert client.get("/me/top").status_code == 401


# --- Corrida na criação do snapshot (DEF-PB08-01) --------------------------


def test_qa_concurrent_first_collection_returns_500_instead_of_handling_conflict(
    client, session_factory, monkeypatch
):
    """DEF-PB08-01: duas coletas simultâneas violam a unicidade (user_id, time_range).

    Simula de forma determinística a janela real da corrida: ambas as requisições
    leem "não há snapshot" antes de qualquer commit, então ambas tentam inserir.
    Comprovado antes contra PostgreSQL real com duas sessões concorrentes.

    `create_room` e `join_room` tratam `IntegrityError`; `get_or_refresh_snapshot`
    não trata, e o conflito escapa como erro não controlado.
    """
    user_id, token = _make_user(session_factory, "qa_pb08_race")
    _seed_snapshot(session_factory, user_id, fetched_at=datetime.now(timezone.utc))
    _mock_spotify(monkeypatch)

    # O perdedor da corrida enxerga "sem snapshot" e segue para o INSERT.
    monkeypatch.setattr(music_service, "_find_snapshot", lambda *_args, **_kwargs: None)

    _act_as(client, token)
    with pytest.raises(IntegrityError):
        client.get("/me/top")
