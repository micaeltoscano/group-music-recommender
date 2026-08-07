"""Testes técnicos do implementador para correções do PB-02."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.clients import crypto, spotify_client
from app.config import settings
from app.db.base import Base
from app.db.models import SpotifyToken, User
from app.main import create_app


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def fernet_key(monkeypatch):
    monkeypatch.setattr(settings, "fernet_key", Fernet.generate_key().decode())
    crypto._fernet = None
    yield
    crypto._fernet = None


def _expired_token(db) -> SpotifyToken:
    user = User(spotify_id="pb02-user")
    db.add(user)
    db.flush()
    token = SpotifyToken(
        user_id=user.id,
        access_token=crypto.encrypt("old-access"),
        refresh_token=crypto.encrypt("valid-refresh"),
        token_expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )
    db.add(token)
    db.commit()
    return token


def test_missing_fernet_key_never_generates_temporary_key(monkeypatch):
    monkeypatch.setattr(settings, "fernet_key", None)
    crypto._fernet = None
    with pytest.raises(RuntimeError, match="FERNET_KEY"):
        crypto.encrypt("token-ficticio")


def test_production_startup_requires_fernet_key(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "fernet_key", None)
    with pytest.raises(RuntimeError, match="FERNET_KEY"):
        create_app()


def test_expired_access_token_is_refreshed_and_persisted(db, monkeypatch):
    stored = _expired_token(db)

    async def fake_refresh(refresh_token: str):
        assert refresh_token == "valid-refresh"
        return {"access_token": "new-access", "expires_in": 1800, "scope": "user-top-read"}

    monkeypatch.setattr(spotify_client, "refresh_access_token", fake_refresh)
    result = asyncio.run(spotify_client.get_valid_access_token(db, stored.user_id))

    db.refresh(stored)
    assert result == "new-access"
    assert crypto.decrypt(stored.access_token) == "new-access"
    assert stored.reauth_required_at is None


def test_failed_refresh_marks_reauthentication_required(db, monkeypatch):
    stored = _expired_token(db)

    async def failed_refresh(_refresh_token: str):
        raise RuntimeError("falha externa simulada")

    monkeypatch.setattr(spotify_client, "refresh_access_token", failed_refresh)
    with pytest.raises(spotify_client.ReauthenticationRequired):
        asyncio.run(spotify_client.get_valid_access_token(db, stored.user_id))

    db.refresh(stored)
    assert stored.reauth_required_at is not None
