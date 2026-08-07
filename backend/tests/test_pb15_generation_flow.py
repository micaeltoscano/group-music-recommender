"""Regressão do fluxo integrado do PB-15, incluindo sala somente com o host."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.auth import SESSION_COOKIE_NAME
from app.db.base import Base
from app.db.models import AppSession, MusicSession, MusicSessionMember, PlaylistRun, User
from app.db.session import get_db
from app.main import app


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pb15-flow.sqlite3'}",
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


@pytest.fixture()
def solo_room(session_factory):
    raw_token = "pb15-solo-host-session"
    db = session_factory()
    try:
        host = User(spotify_id="solo_host", display_name="Solo Host")
        db.add(host)
        db.flush()
        room = MusicSession(
            code="SOLO-001",
            host_user_id=host.id,
            status="open",
            occasion="Viagem",
            mode="Democrático",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
        db.add(room)
        db.flush()
        db.add(MusicSessionMember(session_id=room.id, user_id=host.id, role="host"))
        db.add(
            AppSession(
                user_id=host.id,
                session_token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
        )
        db.commit()
        return SimpleNamespace(token=raw_token, host_id=host.id, room_id=room.id, code=room.code)
    finally:
        db.close()


def _top_tracks(total: int = 25) -> list[dict]:
    return [
        {
            "id": f"track{i:02d}",
            "name": f"Track{i:02d}",
            "artists": [{"id": f"artist{i:02d}", "name": f"Artist{i:02d}"}],
            "popularity": 70,
            "album": {"release_date": "2026"},
        }
        for i in range(total)
    ]


def _top_artists(total: int = 25) -> list[dict]:
    return [
        {"id": f"artist{i:02d}", "name": f"Artist{i:02d}", "genres": ["pop"]}
        for i in range(total)
    ]


async def _search_exact_track(_token, query, *, market="from_token", limit=3):
    del market, limit
    track_name, artist_name = query.split()
    suffix = track_name.removeprefix("Track")
    return [
        {
            "id": f"spotify{suffix}",
            "uri": f"spotify:track:{suffix}",
            "name": track_name,
            "artists": [{"name": artist_name}],
            "is_playable": True,
        }
    ]


def _snapshot_result(total: int = 25):
    return SimpleNamespace(
        snapshot=SimpleNamespace(
            top_tracks_json=_top_tracks(total),
            top_artists_json=_top_artists(total),
        )
    )


@patch("app.services.generation_service.get_or_refresh_snapshot", new_callable=AsyncMock)
@patch("app.clients.spotify_client.get_valid_access_token", new_callable=AsyncMock)
@patch("app.clients.spotify_client.search_track", new_callable=AsyncMock)
@patch("app.clients.spotify_client.create_playlist", new_callable=AsyncMock)
@patch("app.clients.spotify_client.add_items_to_playlist", new_callable=AsyncMock)
def test_pb15_host_sozinho_gera_playlist_completa(
    mock_add_items,
    mock_create_playlist,
    mock_search,
    mock_get_token,
    mock_snapshot,
    client,
    session_factory,
    solo_room,
):
    """Fluxo crítico: um único integrante, sendo o host, gera 20–30 faixas."""
    mock_snapshot.return_value = _snapshot_result()
    mock_get_token.return_value = "host-access-token"
    mock_search.side_effect = _search_exact_track
    mock_create_playlist.return_value = {
        "id": "playlist-solo",
        "external_urls": {"spotify": "https://open.spotify.com/playlist/solo"},
    }
    mock_add_items.return_value = {"snapshot_id": "snapshot-created"}
    client.cookies.set(SESSION_COOKIE_NAME, solo_room.token)

    response = client.post(f"/rooms/{solo_room.code}/generate")

    assert response.status_code == 202
    assert response.json()["status"] == "completed"
    assert response.json()["spotify_playlist_id"] == "playlist-solo"
    assert response.json()["spotify_playlist_url"].endswith("/solo")
    mock_snapshot.assert_awaited_once()
    assert mock_snapshot.await_args.args[1] == solo_room.host_id
    mock_create_playlist.assert_awaited_once()
    assert mock_create_playlist.await_args.kwargs["public"] is False
    sent_uris = mock_add_items.await_args.kwargs["uris"]
    assert 20 <= len(sent_uris) <= 30

    db = session_factory()
    try:
        run = db.query(PlaylistRun).filter_by(session_id=solo_room.room_id).one()
        room = db.get(MusicSession, solo_room.room_id)
        assert run.status == "completed"
        assert run.spotify_playlist_id == "playlist-solo"
        assert room.status == "open"
        assert len(run.tracks) == 25
    finally:
        db.close()


@patch("app.services.generation_service.get_or_refresh_snapshot", new_callable=AsyncMock)
@patch("app.clients.spotify_client.get_valid_access_token", new_callable=AsyncMock)
@patch("app.clients.spotify_client.search_track", new_callable=AsyncMock)
def test_pb15_faixas_insuficientes_falham_e_liberam_retry(
    mock_search,
    mock_get_token,
    mock_snapshot,
    client,
    session_factory,
    solo_room,
):
    mock_snapshot.return_value = _snapshot_result()
    mock_get_token.return_value = "host-access-token"
    mock_search.return_value = []
    client.cookies.set(SESSION_COOKIE_NAME, solo_room.token)

    response = client.post(f"/rooms/{solo_room.code}/generate")

    assert response.status_code == 422
    assert "20 faixas" in response.json()["detail"]["message"]
    db = session_factory()
    try:
        run = db.query(PlaylistRun).filter_by(session_id=solo_room.room_id).one()
        room = db.get(MusicSession, solo_room.room_id)
        assert run.status == "failed"
        assert room.status == "open"
    finally:
        db.close()
