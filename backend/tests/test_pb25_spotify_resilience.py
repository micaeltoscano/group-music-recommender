"""PB-25 — resolução eficiente e rate limit recuperável do Spotify."""

from __future__ import annotations

import asyncio
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from app.api.auth import SESSION_COOKIE_NAME
from app.clients.spotify_client import SpotifyRateLimited
from app.db.base import Base
from app.db.models import (
    AppSession,
    MusicSession,
    MusicSessionMember,
    PlaylistRun,
    User,
)
from app.db.session import get_db
from app.engine.candidates import CandidateTrack
from app.main import app
from app.services.generation_service import (
    PlaylistGenerationError,
    fail_generation,
    get_generation_executor,
    resolve_candidates,
)


def _candidate(track_id: str, *, uri: str | None = None) -> CandidateTrack:
    raw_data = {
        "id": track_id,
        "name": f"Track {track_id}",
        "artists": [{"name": "Artist"}],
    }
    if uri is not None:
        raw_data["uri"] = uri
    return CandidateTrack(track_id, raw_data, {2, 1})


@patch("app.clients.spotify_client.search_track", new_callable=AsyncMock)
def test_native_spotify_candidate_reuses_id_and_uri_without_search(mock_search):
    db = MagicMock(spec=Session)
    candidate = _candidate("native-1", uri="spotify:track:native-1")

    asyncio.run(resolve_candidates(db, uuid.uuid4(), [candidate], "token"))

    mock_search.assert_not_awaited()
    track = db.add_all.call_args.args[0][0]
    assert track.status == "matched"
    assert track.spotify_id == "native-1"
    assert track.spotify_uri == "spotify:track:native-1"
    assert track.match_confidence == 1.0
    assert track.source == "[1, 2]"


@patch("app.clients.spotify_client.search_track", new_callable=AsyncMock)
def test_inconsistent_native_uri_falls_back_to_textual_matching(mock_search):
    mock_search.return_value = [
        {
            "id": "native-safe",
            "uri": "spotify:track:native-safe",
            "name": "Track native-safe",
            "artists": [{"name": "Artist"}],
            "is_playable": True,
        }
    ]
    db = MagicMock(spec=Session)
    candidate = _candidate("native-safe", uri="spotify:track:different-track")

    asyncio.run(resolve_candidates(db, uuid.uuid4(), [candidate], "token"))

    mock_search.assert_awaited_once()
    track = db.add_all.call_args.args[0][0]
    assert track.status == "matched"
    assert track.spotify_id == "native-safe"
    assert track.spotify_uri == "spotify:track:native-safe"


@patch("app.clients.spotify_client.search_track", new_callable=AsyncMock)
def test_incomplete_candidate_still_uses_textual_matching(mock_search):
    mock_search.return_value = [
        {
            "id": "resolved-1",
            "uri": "spotify:track:resolved-1",
            "name": "Track external-1",
            "artists": [{"name": "Artist"}],
            "is_playable": True,
        }
    ]
    db = MagicMock(spec=Session)

    asyncio.run(resolve_candidates(db, uuid.uuid4(), [_candidate("external-1")], "token"))

    mock_search.assert_awaited_once()
    track = db.add_all.call_args.args[0][0]
    assert track.status == "matched"
    assert track.spotify_id == "resolved-1"


@patch("app.clients.spotify_client.search_track", new_callable=AsyncMock)
def test_rate_limit_aborts_batch_immediately_without_false_discards(mock_search):
    mock_search.side_effect = SpotifyRateLimited(91)
    db = MagicMock(spec=Session)
    candidates = [_candidate(f"external-{index}") for index in range(4)]

    with pytest.raises(SpotifyRateLimited) as error:
        asyncio.run(resolve_candidates(db, uuid.uuid4(), candidates, "token"))

    assert error.value.retry_after == 91
    assert mock_search.await_count == 1
    db.add_all.assert_not_called()
    db.commit.assert_not_called()


@patch("app.clients.spotify_client.search_track", new_callable=AsyncMock)
def test_unavailable_native_candidate_is_discarded_without_search(mock_search):
    candidate = _candidate("native-blocked", uri="spotify:track:native-blocked")
    candidate.raw_data["is_playable"] = False
    db = MagicMock(spec=Session)

    asyncio.run(resolve_candidates(db, uuid.uuid4(), [candidate], "token"))

    mock_search.assert_not_awaited()
    track = db.add_all.call_args.args[0][0]
    assert track.status == "discarded"
    assert track.discard_reason == "unavailable_in_market"


def test_rate_limit_returns_429_and_releases_room_for_retry(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pb25-rate-limit.sqlite3'}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(engine)
    raw_token = "pb25-host-token"
    setup_db = factory()
    host = User(spotify_id="pb25-host", display_name="Host")
    setup_db.add(host)
    setup_db.flush()
    room = MusicSession(
        code="PB25-429",
        host_user_id=host.id,
        status="open",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    setup_db.add(room)
    setup_db.flush()
    room_id = room.id
    room_code = room.code
    setup_db.add(MusicSessionMember(session_id=room.id, user_id=host.id, role="host"))
    setup_db.add(
        AppSession(
            user_id=host.id,
            session_token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
    )
    setup_db.commit()
    setup_db.close()

    async def _rate_limited(_db, run_id, _host_id):
        fail_generation(_db, run_id, "Spotify temporariamente limitado.")
        raise PlaylistGenerationError(
            "Spotify temporariamente limitado; tente novamente em 73 segundos.",
            run_id=run_id,
            reason="rate_limited",
            retry_after=73,
        )

    def _override_get_db():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_generation_executor] = lambda: _rate_limited
    try:
        with TestClient(app) as client:
            client.cookies.set(SESSION_COOKIE_NAME, raw_token)
            response = client.post(f"/rooms/{room_code}/generate")

        assert response.status_code == 429
        assert response.json()["detail"]["retry_after"] == 73
        verify_db = factory()
        try:
            stored_room = verify_db.get(MusicSession, room_id)
            run = verify_db.query(PlaylistRun).filter_by(session_id=room_id).one()
            assert stored_room.status == "open"
            assert run.status == "failed"
        finally:
            verify_db.close()
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()
