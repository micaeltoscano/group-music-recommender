"""Testes do Dev para PB-03 — logout e remocao de dados."""

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
        f"sqlite:///{tmp_path / 'pb03.sqlite3'}",
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


def _seed_privacy_scenario(session_factory):
    db = session_factory()
    try:
        owner = User(
            spotify_id="spotify-owner",
            display_name="Pessoa a remover",
            image_url="https://images.invalid/owner.png",
        )
        other = User(
            spotify_id="spotify-other",
            display_name="Outra pessoa",
            image_url="https://images.invalid/other.png",
        )
        db.add_all([owner, other])
        db.flush()

        owner_token = "owner-session-current"
        owner_other_token = "owner-session-other-device"
        other_token = "other-session"
        expires_at = datetime.now(timezone.utc) + timedelta(days=1)
        db.add_all(
            [
                AppSession(
                    user_id=owner.id,
                    session_token_hash=_hash(owner_token),
                    expires_at=expires_at,
                ),
                AppSession(
                    user_id=owner.id,
                    session_token_hash=_hash(owner_other_token),
                    expires_at=expires_at,
                ),
                AppSession(
                    user_id=other.id,
                    session_token_hash=_hash(other_token),
                    expires_at=expires_at,
                ),
            ]
        )
        db.add_all(
            [
                SpotifyToken(
                    user_id=owner.id,
                    access_token="encrypted-owner-access",
                    refresh_token="encrypted-owner-refresh",
                    token_expires_at=expires_at,
                ),
                SpotifyToken(
                    user_id=other.id,
                    access_token="encrypted-other-access",
                    refresh_token="encrypted-other-refresh",
                    token_expires_at=expires_at,
                ),
            ]
        )

        room = MusicSession(
            code="PRIV-0001",
            host_user_id=owner.id,
            status="open",
            expires_at=expires_at,
        )
        db.add(room)
        db.flush()
        db.add_all(
            [
                MusicSessionMember(session_id=room.id, user_id=owner.id, role="host"),
                MusicSessionMember(session_id=room.id, user_id=other.id, role="member"),
                UserMusicSnapshot(
                    user_id=owner.id,
                    time_range="medium_term",
                    top_tracks_json=[{"id": "owner-track"}],
                    top_artists_json=[{"id": "owner-artist"}],
                    fetched_at=datetime.now(timezone.utc),
                ),
                UserMusicSnapshot(
                    user_id=other.id,
                    time_range="medium_term",
                    top_tracks_json=[{"id": "other-track"}],
                    top_artists_json=[{"id": "other-artist"}],
                    fetched_at=datetime.now(timezone.utc),
                ),
                VibeCheckAnswer(
                    session_id=room.id,
                    user_id=owner.id,
                    energy=0.1,
                    valence=0.2,
                    popularity=0.3,
                ),
                VibeCheckAnswer(
                    session_id=room.id,
                    user_id=other.id,
                    energy=0.7,
                    valence=0.8,
                    popularity=0.9,
                ),
            ]
        )
        db.commit()
        return {
            "owner_id": owner.id,
            "other_id": other.id,
            "room_id": room.id,
            "owner_token": owner_token,
            "owner_other_token": owner_other_token,
            "other_token": other_token,
        }
    finally:
        db.close()


def test_ct_pb03_01_logout_invalida_somente_sessao_atual(client, session_factory):
    seeded = _seed_privacy_scenario(session_factory)
    client.cookies.set(SESSION_COOKIE_NAME, seeded["owner_token"])

    response = client.post("/auth/logout")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get("/auth/me").status_code == 401

    db = session_factory()
    try:
        hashes = {row.session_token_hash for row in db.query(AppSession).all()}
        assert _hash(seeded["owner_token"]) not in hashes
        assert _hash(seeded["owner_other_token"]) in hashes
        assert _hash(seeded["other_token"]) in hashes
    finally:
        db.close()


def test_ct_pb03_02_rotas_protegidas_negam_acesso_apos_logout(client, session_factory):
    seeded = _seed_privacy_scenario(session_factory)
    client.cookies.set(SESSION_COOKIE_NAME, seeded["owner_token"])
    assert client.post("/auth/logout").status_code == 204

    assert client.get("/auth/me").status_code == 401
    assert client.get("/rooms/PRIV-0001").status_code == 401


def test_logout_sem_sessao_e_idempotente(client):
    response = client.post("/auth/logout")

    assert response.status_code == 204
    assert response.content == b""


def test_ct_pb03_03_remocao_apaga_dados_pessoais_e_anonimiza(
    client,
    session_factory,
):
    seeded = _seed_privacy_scenario(session_factory)
    client.cookies.set(SESSION_COOKIE_NAME, seeded["owner_token"])

    response = client.delete("/auth/me")

    assert response.status_code == 204
    assert response.content == b""
    assert "encrypted-owner" not in response.text
    assert client.get("/auth/me").status_code == 401

    db = session_factory()
    try:
        owner = db.get(User, seeded["owner_id"])
        assert owner is not None
        assert owner.spotify_id.startswith("deleted-")
        assert owner.spotify_id != "spotify-owner"
        assert owner.display_name == ANONYMIZED_DISPLAY_NAME
        assert owner.image_url is None
        assert db.query(SpotifyToken).filter_by(user_id=owner.id).count() == 0
        assert db.query(AppSession).filter_by(user_id=owner.id).count() == 0
        assert db.query(UserMusicSnapshot).filter_by(user_id=owner.id).count() == 0
        assert db.query(VibeCheckAnswer).filter_by(user_id=owner.id).count() == 0
    finally:
        db.close()


def test_ct_pb03_04_remocao_preserva_sala_e_dados_de_terceiros(
    client,
    session_factory,
):
    seeded = _seed_privacy_scenario(session_factory)
    client.cookies.set(SESSION_COOKIE_NAME, seeded["owner_token"])
    assert client.delete("/auth/me").status_code == 204

    db = session_factory()
    try:
        other = db.get(User, seeded["other_id"])
        room = db.get(MusicSession, seeded["room_id"])
        assert other is not None
        assert other.spotify_id == "spotify-other"
        assert other.display_name == "Outra pessoa"
        assert room is not None
        assert room.host_user_id == seeded["owner_id"]
        assert db.query(MusicSessionMember).filter_by(session_id=room.id).count() == 2
        assert db.query(SpotifyToken).filter_by(user_id=other.id).count() == 1
        assert db.query(AppSession).filter_by(user_id=other.id).count() == 1
        assert db.query(UserMusicSnapshot).filter_by(user_id=other.id).count() == 1
        assert db.query(VibeCheckAnswer).filter_by(user_id=other.id).count() == 1
    finally:
        db.close()

    client.cookies.set(SESSION_COOKIE_NAME, seeded["other_token"])
    room_response = client.get("/rooms/PRIV-0001")
    assert room_response.status_code == 200
    assert "encrypted-owner" not in room_response.text
    assert "encrypted-other" not in room_response.text


def test_remocao_exige_autenticacao(client):
    response = client.delete("/auth/me")

    assert response.status_code == 401
