import json
import uuid
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.orm import Session

from app.db.models import PlaylistRunTrack
from app.engine.candidates import CandidateTrack
from app.services.generation_service import resolve_candidates


@pytest.fixture
def mock_search_track():
    with patch("app.clients.spotify_client.search_track", new_callable=AsyncMock) as mock:
        yield mock


def test_pb14_successful_matching(mock_search_track):
    """
    CT-PB14-01 - Correspondência bem sucedida.
    """
    mock_search_track.return_value = [
        {"id": "spotify_123", "uri": "spotify:track:123", "name": "Perfect Song", "artists": [{"name": "Perfect Artist"}], "is_playable": True}
    ]

    candidate = CandidateTrack(
        track_id="c1",
        raw_data={"name": "Perfect Song - Remastered", "artists": [{"name": "Perfect Artist"}]},
        source_user_ids={1}
    )

    db = MagicMock(spec=Session)
    asyncio.run(resolve_candidates(db, uuid.uuid4(), [candidate], "fake_token"))

    db.add_all.assert_called_once()
    tracks = db.add_all.call_args[0][0]

    assert len(tracks) == 1
    assert tracks[0].status == "matched"
    assert tracks[0].spotify_id == "spotify_123"
    assert tracks[0].match_confidence >= 0.8

    db.commit.assert_called_once()


def test_pb14_below_confidence(mock_search_track):
    """
    CT-PB14-02 - Correspondência falha por baixa confiança.
    """
    mock_search_track.return_value = [
        {"id": "spotify_456", "uri": "spotify:track:456", "name": "Different Song", "artists": [{"name": "Wrong Artist"}], "is_playable": True}
    ]

    candidate = CandidateTrack(
        track_id="c2",
        raw_data={"name": "My Song", "artists": [{"name": "My Artist"}]},
        source_user_ids={1}
    )

    db = MagicMock(spec=Session)
    asyncio.run(resolve_candidates(db, uuid.uuid4(), [candidate], "fake_token"))

    tracks = db.add_all.call_args[0][0]
    assert len(tracks) == 1
    assert tracks[0].status == "discarded"
    assert "Confidence below threshold" in tracks[0].discard_reason


def test_pb14_unplayable_market(mock_search_track):
    """
    CT-PB14-03 - Música indisponível no mercado do host.
    """
    mock_search_track.return_value = [
        {"id": "spotify_789", "uri": "spotify:track:789", "name": "Banned Song", "artists": [{"name": "Banned Artist"}], "is_playable": False}
    ]

    candidate = CandidateTrack(
        track_id="c3",
        raw_data={"name": "Banned Song", "artists": [{"name": "Banned Artist"}]},
        source_user_ids={1}
    )

    db = MagicMock(spec=Session)
    asyncio.run(resolve_candidates(db, uuid.uuid4(), [candidate], "fake_token"))

    tracks = db.add_all.call_args[0][0]
    assert len(tracks) == 1
    assert tracks[0].status == "discarded"
    assert tracks[0].discard_reason == "All results unplayable"


def test_pb14_empty_results_or_error(mock_search_track):
    """
    CT-PB14-04 - API retorna erro ou sem resultados.
    """
    mock_search_track.side_effect = Exception("Spotify API Down")

    candidate = CandidateTrack(
        track_id="c4",
        raw_data={"name": "Any Song", "artists": [{"name": "Any Artist"}]},
        source_user_ids={1}
    )

    db = MagicMock(spec=Session)
    asyncio.run(resolve_candidates(db, uuid.uuid4(), [candidate], "fake_token"))

    tracks = db.add_all.call_args[0][0]
    assert len(tracks) == 1
    assert tracks[0].status == "discarded"
    assert "Spotify search error: Spotify API Down" in tracks[0].discard_reason
