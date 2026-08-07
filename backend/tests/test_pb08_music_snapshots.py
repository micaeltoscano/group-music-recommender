"""Testes técnicos do implementador para o PB-08 (snapshots musicais)."""

from __future__ import annotations

import asyncio
import hashlib
from datetime import datetime, timedelta, timezone

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.auth import SESSION_COOKIE_NAME
from app.clients import crypto, spotify_client
from app.config import settings
from app.db.base import Base
from app.db.models import AppSession, SpotifyToken, User, UserMusicSnapshot
from app.db.session import get_db
from app.main import app

TRACKS = [
    {
        "id": "track-1",
        "name": "Faixa Um",
        "uri": "spotify:track:track-1",
        "artists": [{"id": "artist-1", "name": "Artista Um"}],
    }
]
ARTISTS = [
    {
        "id": "artist-1",
        "name": "Artista Um",
        "uri": "spotify:artist:artist-1",
        "genres": ["pop"],
    }
]


@pytest.fixture(autouse=True)
def fernet_key(monkeypatch):
    monkeypatch.setattr(settings, "fernet_key", Fernet.generate_key().decode())
    crypto._fernet = None
    yield
    crypto._fernet = None


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pb08.sqlite3'}",
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


def _authenticated_user(
    client: TestClient,
    session_factory,
    *,
    spotify_id: str = "pb08-user",
) -> tuple[int, str]:
    raw_token = f"session-for-{spotify_id}"
    db = session_factory()
    try:
        user = User(spotify_id=spotify_id, display_name="Usuário PB08")
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
        user_id = user.id
    finally:
        db.close()
    client.cookies.set(SESSION_COOKIE_NAME, raw_token)
    return user_id, raw_token


def _seed_snapshot(
    session_factory,
    user_id: int,
    *,
    fetched_at: datetime,
    time_range: str = "medium_term",
    tracks: list[dict] | None = None,
    artists: list[dict] | None = None,
) -> UserMusicSnapshot:
    db = session_factory()
    try:
        snapshot = UserMusicSnapshot(
            user_id=user_id,
            time_range=time_range,
            top_tracks_json=tracks if tracks is not None else TRACKS,
            top_artists_json=artists if artists is not None else ARTISTS,
            fetched_at=fetched_at,
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        db.expunge(snapshot)
        return snapshot
    finally:
        db.close()


def _mock_success(monkeypatch, calls: list[tuple] | None = None) -> None:
    async def valid_token(_db, user_id):
        if calls is not None:
            calls.append(("token", user_id))
        return "access-ficticio"

    async def top_tracks(access_token, *, time_range, limit):
        if calls is not None:
            calls.append(("tracks", access_token, time_range, limit))
        return TRACKS

    async def top_artists(access_token, *, time_range, limit):
        if calls is not None:
            calls.append(("artists", access_token, time_range, limit))
        return ARTISTS

    monkeypatch.setattr(spotify_client, "get_valid_access_token", valid_token)
    monkeypatch.setattr(spotify_client, "get_top_tracks", top_tracks)
    monkeypatch.setattr(spotify_client, "get_top_artists", top_artists)


def test_ct_pb08_01_refresh_collects_and_associates_snapshot(
    client,
    session_factory,
    monkeypatch,
):
    user_id, _ = _authenticated_user(client, session_factory)
    calls: list[tuple] = []
    _mock_success(monkeypatch, calls)

    response = client.post("/me/refresh-music-snapshot")

    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == user_id
    assert body["time_range"] == "medium_term"
    assert body["top_tracks"] == TRACKS
    assert body["top_artists"] == ARTISTS
    assert body["cached"] is body["stale"] is False
    assert [call[0] for call in calls] == ["token", "tracks", "artists"]

    db = session_factory()
    try:
        snapshot = db.query(UserMusicSnapshot).one()
        assert snapshot.user_id == user_id
        assert snapshot.top_tracks_json == TRACKS
        assert snapshot.top_artists_json == ARTISTS
    finally:
        db.close()


def test_ct_pb08_02_fresh_snapshot_is_reused_without_spotify_call(
    client,
    session_factory,
    monkeypatch,
):
    user_id, _ = _authenticated_user(client, session_factory)
    original = _seed_snapshot(
        session_factory,
        user_id,
        fetched_at=datetime.now(timezone.utc) - timedelta(days=6, hours=23),
    )

    async def forbidden(*_args, **_kwargs):
        raise AssertionError("Spotify não deve ser chamado para snapshot fresco.")

    monkeypatch.setattr(spotify_client, "get_valid_access_token", forbidden)
    monkeypatch.setattr(spotify_client, "get_top_tracks", forbidden)
    monkeypatch.setattr(spotify_client, "get_top_artists", forbidden)

    response = client.get("/me/top")

    assert response.status_code == 200
    assert response.json()["snapshot_id"] == str(original.id)
    assert response.json()["cached"] is True
    assert response.json()["stale"] is False


def test_ct_pb08_03_expired_snapshot_is_refetched_and_updated(
    client,
    session_factory,
    monkeypatch,
):
    user_id, _ = _authenticated_user(client, session_factory)
    old_time = datetime.now(timezone.utc) - timedelta(days=8)
    original = _seed_snapshot(
        session_factory,
        user_id,
        fetched_at=old_time,
        tracks=[{"id": "old-track"}],
        artists=[{"id": "old-artist"}],
    )
    _mock_success(monkeypatch)

    response = client.get("/me/top")

    assert response.status_code == 200
    assert response.json()["snapshot_id"] == str(original.id)
    assert response.json()["top_tracks"] == TRACKS
    assert response.json()["cached"] is False
    db = session_factory()
    try:
        assert db.query(UserMusicSnapshot).count() == 1
        refreshed = db.query(UserMusicSnapshot).one()
        assert refreshed.fetched_at.replace(tzinfo=timezone.utc) > old_time
    finally:
        db.close()


def test_post_forces_refresh_even_when_snapshot_is_fresh(
    client,
    session_factory,
    monkeypatch,
):
    user_id, _ = _authenticated_user(client, session_factory)
    original = _seed_snapshot(
        session_factory,
        user_id,
        fetched_at=datetime.now(timezone.utc) - timedelta(hours=1),
        tracks=[{"id": "old-track"}],
    )
    calls: list[tuple] = []
    _mock_success(monkeypatch, calls)

    response = client.post("/me/refresh-music-snapshot")

    assert response.status_code == 200
    assert response.json()["snapshot_id"] == str(original.id)
    assert response.json()["top_tracks"] == TRACKS
    assert [call[0] for call in calls] == ["token", "tracks", "artists"]


def test_ct_pb08_04_failed_token_refresh_marks_reauth_and_returns_controlled_401(
    client,
    session_factory,
    monkeypatch,
):
    user_id, _ = _authenticated_user(client, session_factory)
    db = session_factory()
    try:
        db.add(
            SpotifyToken(
                user_id=user_id,
                access_token=crypto.encrypt("access-expirado"),
                refresh_token=crypto.encrypt("refresh-invalido"),
                token_expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
            )
        )
        db.commit()
    finally:
        db.close()

    async def failed_refresh(_refresh_token):
        raise RuntimeError("falha externa simulada")

    async def forbidden(*_args, **_kwargs):
        raise AssertionError("Top items não devem ser chamados sem token válido.")

    monkeypatch.setattr(spotify_client, "refresh_access_token", failed_refresh)
    monkeypatch.setattr(spotify_client, "get_top_tracks", forbidden)
    monkeypatch.setattr(spotify_client, "get_top_artists", forbidden)

    response = client.get("/me/top")

    assert response.status_code == 401
    assert response.json()["detail"]["reauth_required"] is True
    assert response.json()["detail"]["login_url"] == "/auth/login"
    db = session_factory()
    try:
        stored = db.query(SpotifyToken).filter(SpotifyToken.user_id == user_id).one()
        assert stored.reauth_required_at is not None
        assert db.query(UserMusicSnapshot).count() == 0
    finally:
        db.close()


def test_ct_pb08_05_rate_limit_reuses_stale_snapshot(
    client,
    session_factory,
    monkeypatch,
):
    user_id, _ = _authenticated_user(client, session_factory)
    original = _seed_snapshot(
        session_factory,
        user_id,
        fetched_at=datetime.now(timezone.utc) - timedelta(days=9),
    )

    async def valid_token(_db, _user_id):
        return "access-ficticio"

    async def rate_limited(*_args, **_kwargs):
        raise spotify_client.SpotifyRateLimited(17)

    monkeypatch.setattr(spotify_client, "get_valid_access_token", valid_token)
    monkeypatch.setattr(spotify_client, "get_top_tracks", rate_limited)

    response = client.get("/me/top")

    assert response.status_code == 200
    assert response.json()["snapshot_id"] == str(original.id)
    assert response.json()["cached"] is response.json()["stale"] is True
    assert "último snapshot" in response.json()["warning"]


def test_rate_limit_without_snapshot_returns_429_and_retry_after(
    client,
    session_factory,
    monkeypatch,
):
    _authenticated_user(client, session_factory)

    async def valid_token(_db, _user_id):
        return "access-ficticio"

    async def rate_limited(*_args, **_kwargs):
        raise spotify_client.SpotifyRateLimited(23)

    monkeypatch.setattr(spotify_client, "get_valid_access_token", valid_token)
    monkeypatch.setattr(spotify_client, "get_top_tracks", rate_limited)

    response = client.get("/me/top")

    assert response.status_code == 429
    assert response.headers["retry-after"] == "23"


def test_ct_pb08_06_empty_top_lists_create_valid_snapshot_with_warning(
    client,
    session_factory,
    monkeypatch,
):
    user_id, _ = _authenticated_user(client, session_factory)

    async def valid_token(_db, _user_id):
        return "access-ficticio"

    async def empty_items(*_args, **_kwargs):
        return []

    monkeypatch.setattr(spotify_client, "get_valid_access_token", valid_token)
    monkeypatch.setattr(spotify_client, "get_top_tracks", empty_items)
    monkeypatch.setattr(spotify_client, "get_top_artists", empty_items)

    response = client.post("/me/refresh-music-snapshot")

    assert response.status_code == 200
    assert response.json()["top_tracks"] == response.json()["top_artists"] == []
    assert "não retornou" in response.json()["warning"]
    db = session_factory()
    try:
        snapshot = db.query(UserMusicSnapshot).one()
        assert snapshot.user_id == user_id
        assert snapshot.top_tracks_json == snapshot.top_artists_json == []
    finally:
        db.close()


def test_top_items_client_uses_only_authorized_spotify_endpoints(monkeypatch):
    requests: list[dict] = []

    class FakeResponse:
        status_code = 200
        headers = {}

        @staticmethod
        def raise_for_status():
            return None

        @staticmethod
        def json():
            return {"items": []}

    class FakeAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def get(self, url, *, headers, params):
            requests.append({"url": url, "headers": headers, "params": params})
            return FakeResponse()

    monkeypatch.setattr(spotify_client, "AsyncClient", FakeAsyncClient)

    asyncio.run(spotify_client.get_top_tracks("token-ficticio"))
    asyncio.run(spotify_client.get_top_artists("token-ficticio", time_range="short_term", limit=20))

    assert [request["url"] for request in requests] == [
        "https://api.spotify.com/v1/me/top/tracks",
        "https://api.spotify.com/v1/me/top/artists",
    ]
    assert requests[0]["params"] == {"time_range": "medium_term", "limit": 50, "offset": 0}
    assert requests[1]["params"] == {"time_range": "short_term", "limit": 20, "offset": 0}
    assert all("recommend" not in request["url"] for request in requests)


def test_top_items_client_preserves_retry_after_from_spotify(monkeypatch):
    class RateLimitedResponse:
        status_code = 429
        headers = {"Retry-After": "31"}

    class FakeAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def get(self, *_args, **_kwargs):
            return RateLimitedResponse()

    monkeypatch.setattr(spotify_client, "AsyncClient", FakeAsyncClient)

    with pytest.raises(spotify_client.SpotifyRateLimited) as error:
        asyncio.run(spotify_client.get_top_tracks("token-ficticio"))

    assert error.value.retry_after == 31


def test_invalid_spotify_payload_returns_controlled_502(
    client,
    session_factory,
    monkeypatch,
):
    _authenticated_user(client, session_factory)

    async def valid_token(_db, _user_id):
        return "access-ficticio"

    async def invalid_payload(*_args, **_kwargs):
        raise spotify_client.SpotifyInvalidResponse("conteúdo externo omitido")

    monkeypatch.setattr(spotify_client, "get_valid_access_token", valid_token)
    monkeypatch.setattr(spotify_client, "get_top_tracks", invalid_payload)

    response = client.get("/me/top")

    assert response.status_code == 502
    assert response.json() == {"detail": "Não foi possível coletar os dados musicais agora."}


def test_music_routes_require_authentication(client):
    assert client.get("/me/top").status_code == 401
    assert client.post("/me/refresh-music-snapshot").status_code == 401


@pytest.mark.parametrize("time_range", ["short_term", "medium_term", "long_term"])
def test_each_supported_time_range_has_its_own_snapshot(
    client,
    session_factory,
    monkeypatch,
    time_range,
):
    user_id, _ = _authenticated_user(
        client,
        session_factory,
        spotify_id=f"pb08-{time_range}",
    )
    _mock_success(monkeypatch)

    response = client.get(f"/me/top?time_range={time_range}")

    assert response.status_code == 200
    assert response.json()["time_range"] == time_range
    db = session_factory()
    try:
        assert db.query(UserMusicSnapshot).filter_by(user_id=user_id, time_range=time_range).count() == 1
    finally:
        db.close()


def test_invalid_time_range_is_rejected_before_calling_spotify(
    client,
    session_factory,
    monkeypatch,
):
    _authenticated_user(client, session_factory)

    async def forbidden(*_args, **_kwargs):
        raise AssertionError("Spotify não deve ser chamado com time_range inválido.")

    monkeypatch.setattr(spotify_client, "get_valid_access_token", forbidden)

    response = client.get("/me/top?time_range=ontem")

    assert response.status_code == 422
