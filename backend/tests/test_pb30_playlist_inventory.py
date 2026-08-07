"""PB-30 — consentimento, paginação e inventário mínimo de playlists."""

from __future__ import annotations

import asyncio
import hashlib
import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.auth import SESSION_COOKIE_NAME, STATE_COOKIE_NAME
from app.clients import crypto, spotify_client
from app.config import settings
from app.db.base import Base
from app.db.models import AppSession, SpotifyToken, User, UserPlaylistInventory
from app.db.session import get_db
from app.main import app
from app.services.playlist_inventory_service import refresh_playlist_inventory


@pytest.fixture(autouse=True)
def fernet_key(monkeypatch):
    monkeypatch.setattr(settings, "fernet_key", Fernet.generate_key().decode())
    crypto._fernet = None
    yield
    crypto._fernet = None


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pb30.sqlite3'}",
        connect_args={"check_same_thread": False},
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


def _seed_user(
    session_factory,
    *,
    spotify_id: str = "pb30-user",
    scopes: str | None = None,
    reauth: bool = False,
) -> tuple[int, str]:
    raw_session = f"session-{spotify_id}"
    db = session_factory()
    try:
        user = User(spotify_id=spotify_id, display_name="PB30")
        db.add(user)
        db.flush()
        db.add(
            SpotifyToken(
                user_id=user.id,
                access_token=crypto.encrypt("access-fake"),
                refresh_token=crypto.encrypt("refresh-fake"),
                token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
                scopes=scopes,
                reauth_required_at=datetime.now(timezone.utc) if reauth else None,
            )
        )
        db.add(
            AppSession(
                user_id=user.id,
                session_token_hash=hashlib.sha256(raw_session.encode()).hexdigest(),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
        )
        db.commit()
        return user.id, raw_session
    finally:
        db.close()


def _playlist(
    playlist_id: str,
    *,
    owner_id: str,
    collaborative: bool = False,
    total: int = 3,
    snapshot_id: str | None = None,
) -> dict:
    return {
        "id": playlist_id,
        "owner": {"id": owner_id},
        "collaborative": collaborative,
        "tracks": {"total": total},
        "snapshot_id": snapshot_id or f"snapshot-{playlist_id}",
        "name": "não deve ser persistido",
        "description": "não deve ser persistida",
        "images": [{"url": "https://example.invalid/private.jpg"}],
    }


def test_ct_pb30_01_scope_missing_requires_reconsent_and_callback_clears_flag(
    client,
    session_factory,
    monkeypatch,
):
    monkeypatch.setattr(settings, "spotify_client_id", "fake-client")
    monkeypatch.setattr(settings, "spotify_client_secret", "fake-secret")
    monkeypatch.setattr(
        settings,
        "spotify_redirect_uri",
        "http://localhost:8000/auth/callback",
    )
    auth_url = spotify_client.get_auth_url("state")
    assert "playlist-read-private" in auth_url
    assert "playlist-read-collaborative" in auth_url

    user_id, _ = _seed_user(session_factory, scopes="user-top-read")
    db = session_factory()
    try:
        with pytest.raises(spotify_client.ReauthenticationRequired) as error:
            asyncio.run(
                spotify_client.get_valid_access_token(
                    db,
                    user_id,
                    required_scopes=spotify_client.PLAYLIST_INVENTORY_SCOPES,
                )
            )
        assert error.value.missing_scopes == (
            "playlist-read-collaborative",
            "playlist-read-private",
        )
    finally:
        db.close()

    async def exchange(_code):
        return {
            "access_token": "new-access",
            "refresh_token": "new-refresh",
            "expires_in": 3600,
            "scope": spotify_client.SCOPES,
        }

    async def profile(_token):
        return {"id": "pb30-user", "display_name": "PB30", "images": []}

    monkeypatch.setattr(spotify_client, "exchange_code_for_token", exchange)
    monkeypatch.setattr(spotify_client, "get_current_user_profile", profile)
    client.cookies.set(STATE_COOKIE_NAME, "reauth-state")
    response = client.get(
        "/auth/callback?code=new-code&state=reauth-state",
        follow_redirects=False,
    )
    assert response.status_code == 302

    db = session_factory()
    try:
        stored = db.query(SpotifyToken).filter_by(user_id=user_id).one()
        assert stored.reauth_required_at is None
        assert spotify_client.PLAYLIST_READ_PRIVATE_SCOPE in stored.scopes.split()
        assert spotify_client.PLAYLIST_READ_COLLABORATIVE_SCOPE in stored.scopes.split()
    finally:
        db.close()


def test_ct_pb30_02_inventory_and_items_are_fully_paginated(monkeypatch):
    calls: list[tuple[str, int]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        offset = int(request.url.params["offset"])
        calls.append((request.url.path, offset))
        if request.url.path == "/v1/me/playlists":
            payload = {
                "items": [{"id": f"playlist-{offset + index}"} for index in range(2)],
                "next": "next" if offset == 0 else None,
            }
        else:
            payload = {
                "items": [{"item": {"id": f"track-{offset + index}"}} for index in range(2)],
                "next": "next" if offset == 0 else None,
            }
        return httpx.Response(200, json=payload)

    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(
        spotify_client,
        "AsyncClient",
        lambda: httpx.AsyncClient(transport=transport),
    )

    playlists = asyncio.run(spotify_client.get_current_user_playlists("token", limit=2))
    items = asyncio.run(spotify_client.get_playlist_items("token", "Playlist01", limit=2))

    assert len(playlists) == 4
    assert len(items) == 4
    assert calls == [
        ("/v1/me/playlists", 0),
        ("/v1/me/playlists", 2),
        ("/v1/playlists/Playlist01/items", 0),
        ("/v1/playlists/Playlist01/items", 2),
    ]


def test_playlist_track_filter_ignores_null_episode_local_and_invalid_identity():
    valid = {
        "id": "Track01",
        "uri": "spotify:track:Track01",
        "type": "track",
        "is_local": False,
    }
    tracks = spotify_client.extract_playlist_tracks(
        [
            {"item": valid},
            {"item": None},
            {"item": {"id": "Episode01", "type": "episode"}},
            {
                "item": {
                    "id": "Local01",
                    "uri": "spotify:track:Local01",
                    "type": "track",
                    "is_local": True,
                }
            },
            {
                "track": {
                    "id": "Mismatch01",
                    "uri": "spotify:track:AnotherTrack",
                    "type": "track",
                }
            },
        ]
    )

    assert tracks == [valid]


def test_ct_pb30_03_and_04_only_accessible_minimal_inventory_is_persisted(
    session_factory,
    monkeypatch,
):
    user_id, _ = _seed_user(
        session_factory,
        scopes=spotify_client.SCOPES,
    )

    async def valid_token(_db, _user_id, *, required_scopes=()):
        assert required_scopes == spotify_client.PLAYLIST_INVENTORY_SCOPES
        return "access-fake"

    async def playlists(_token):
        return [
            _playlist("Owned01", owner_id="pb30-user", total=10),
            _playlist("Collab01", owner_id="other", collaborative=True, total=20),
            _playlist("Followed01", owner_id="other", total=30),
            _playlist("Forbidden01", owner_id="other", collaborative=True, total=40),
        ]

    async def probe(_token, playlist_id, *, limit, offset):
        assert (limit, offset) == (1, 0)
        if playlist_id == "Forbidden01":
            raise spotify_client.SpotifyAccessForbidden("forbidden")
        return {"items": [], "next": None}

    monkeypatch.setattr(spotify_client, "get_valid_access_token", valid_token)
    monkeypatch.setattr(spotify_client, "get_current_user_playlists", playlists)
    monkeypatch.setattr(spotify_client, "get_playlist_items_page", probe)

    db = session_factory()
    try:
        result = asyncio.run(refresh_playlist_inventory(db, user_id))
        assert [(item.spotify_playlist_id, item.access_type) for item in result.items] == [
            ("Collab01", "collaborative"),
            ("Owned01", "owned"),
        ]
        assert {(skip.spotify_playlist_id, skip.reason) for skip in result.skipped} == {
            ("Followed01", "followed_not_eligible"),
            ("Forbidden01", "content_forbidden"),
        }
        assert {column.name for column in UserPlaylistInventory.__table__.columns} == {
            "id",
            "user_id",
            "spotify_playlist_id",
            "access_type",
            "tracks_total",
            "snapshot_id",
            "verified_at",
        }
        persisted = str(
            [
                {
                    "playlist_id": item.spotify_playlist_id,
                    "access_type": item.access_type,
                    "tracks_total": item.tracks_total,
                    "snapshot_id": item.snapshot_id,
                }
                for item in result.items
            ]
        )
        assert "não deve" not in persisted
        assert "access-fake" not in persisted
    finally:
        db.close()


@pytest.mark.parametrize(
    ("status_code", "headers", "expected_exception"),
    [
        (401, {}, spotify_client.ReauthenticationRequired),
        (403, {}, spotify_client.SpotifyAccessForbidden),
        (429, {"Retry-After": "17"}, spotify_client.SpotifyRateLimited),
    ],
)
def test_ct_pb30_05_401_403_and_429_are_distinct(
    monkeypatch,
    status_code,
    headers,
    expected_exception,
):
    transport = httpx.MockTransport(
        lambda _request: httpx.Response(status_code, headers=headers, json={"error": {}})
    )
    monkeypatch.setattr(
        spotify_client,
        "AsyncClient",
        lambda: httpx.AsyncClient(transport=transport),
    )

    with pytest.raises(expected_exception) as error:
        asyncio.run(
            spotify_client.get_playlist_items_page(
                "token",
                "Playlist01",
                limit=1,
            )
        )
    if status_code == 429:
        assert error.value.retry_after == 17


def test_inventory_is_not_replaced_when_rate_limit_interrupts_probes(
    session_factory,
    monkeypatch,
):
    user_id, _ = _seed_user(session_factory, scopes=spotify_client.SCOPES)
    db = session_factory()
    db.add(
        UserPlaylistInventory(
            user_id=user_id,
            spotify_playlist_id="Cached01",
            access_type="owned",
            tracks_total=7,
            snapshot_id="cached-snapshot",
            verified_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
    )
    db.commit()

    async def valid_token(_db, _user_id, *, required_scopes=()):
        return "token"

    async def playlists(_token):
        return [_playlist("Fresh01", owner_id="pb30-user")]

    async def rate_limited(*_args, **_kwargs):
        raise spotify_client.SpotifyRateLimited(23)

    monkeypatch.setattr(spotify_client, "get_valid_access_token", valid_token)
    monkeypatch.setattr(spotify_client, "get_current_user_playlists", playlists)
    monkeypatch.setattr(spotify_client, "get_playlist_items_page", rate_limited)

    with pytest.raises(spotify_client.SpotifyRateLimited):
        asyncio.run(refresh_playlist_inventory(db, user_id))

    assert db.query(UserPlaylistInventory).one().spotify_playlist_id == "Cached01"
    db.close()


def test_pb30_migration_is_reversible_on_isolated_database(tmp_path):
    database_path = tmp_path / "pb30-migration.sqlite3"
    engine = create_engine(f"sqlite:///{database_path}", future=True)
    metadata = sa.MetaData()
    sa.Table("users", metadata, sa.Column("id", sa.Integer(), primary_key=True))
    metadata.create_all(engine)

    migration_path = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "0019_pb30_playlist_inventory.py"
    )
    spec = importlib.util.spec_from_file_location("pb30_migration", migration_path)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    with engine.begin() as connection:
        operations = Operations(MigrationContext.configure(connection))
        with patch.object(migration, "op", operations):
            migration.upgrade()
        inspector = sa.inspect(connection)
        assert "user_playlist_inventory" in inspector.get_table_names()
        assert {column["name"] for column in inspector.get_columns("user_playlist_inventory")} == {
            "id",
            "user_id",
            "spotify_playlist_id",
            "access_type",
            "tracks_total",
            "snapshot_id",
            "verified_at",
        }
        with patch.object(migration, "op", operations):
            migration.downgrade()
        assert "user_playlist_inventory" not in sa.inspect(connection).get_table_names()

    engine.dispose()
