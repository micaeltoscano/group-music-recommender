"""PB-26 — pool híbrido de Tops e descoberta contextual."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

from app.clients.lastfm_client import LastFmTrack
from app.engine.candidates import CandidateTrack
from app.engine.context_scoring import ContextCriteria
from app.engine.contextual_pool import blend_contextual_candidates
from app.engine.taste import UserTasteProfile
from app.services.contextual_pool_service import (
    context_discovery_tags,
    discover_context_candidates,
)
from app.services.generation_service import _rank_candidates

PARTY = ContextCriteria(
    occasion="Festa",
    mood="animada",
    energy="alta",
    tags_positive=("dance", "party"),
)


def _candidate(
    track_id: str,
    *,
    name: str | None = None,
    genres: tuple[str, ...] = ("sad",),
    source: set[int] | None = None,
    origin: str = "spotify_top",
) -> CandidateTrack:
    return CandidateTrack(
        track_id,
        {
            "id": track_id if origin == "spotify_top" else None,
            "uri": f"spotify:track:{track_id}" if origin == "spotify_top" else None,
            "name": name or track_id,
            "artists": [{"id": f"artist-{track_id}", "name": f"Artist {track_id}"}],
            "genres": list(genres),
            "context_tags": list(genres),
            "popularity": 60,
        },
        source or set(),
        origin=origin,
    )


def _evaluation(candidate: CandidateTrack, score: float = 0.8) -> dict[str, object]:
    return {
        "candidate": candidate,
        "context_score": score,
        "individual_scores": [0.2, 0.3],
        "penalized_score": score,
    }


def test_party_context_maps_to_stable_lastfm_tags():
    assert context_discovery_tags(PARTY) == ("party", "dance", "pop")


def test_discovery_combines_tag_and_personal_similar_without_duplicates():
    anchors = [
        _candidate("anchor-1", name="Known", genres=("pop",), source={1}),
        _candidate("anchor-2", name="Other", genres=("rock",), source={2}),
    ]
    tag_tracks = [
        LastFmTrack("Dance Floor", "DJ One"),
        LastFmTrack("Known", "Artist anchor-1"),
    ]
    similar_tracks = [
        LastFmTrack("Dance Floor", "DJ One"),
        LastFmTrack("New Similar", "Band Two", match=0.9),
    ]
    with (
        patch("app.services.contextual_pool_service.lastfm_client.is_configured", return_value=True),
        patch(
            "app.services.contextual_pool_service.lastfm_client.get_tag_top_tracks",
            new=AsyncMock(return_value=tag_tracks),
        ) as tag_call,
        patch(
            "app.services.contextual_pool_service.lastfm_client.get_similar_tracks",
            new=AsyncMock(return_value=similar_tracks),
        ) as similar_call,
    ):
        discovered = asyncio.run(discover_context_candidates(anchors, PARTY))

    identities = {(item.raw_data["name"], item.raw_data["artists"][0]["name"]) for item in discovered}
    assert identities == {("Dance Floor", "DJ One"), ("New Similar", "Band Two")}
    assert {item.origin for item in discovered} == {"lastfm_tag", "lastfm_similar"}
    personal = next(item for item in discovered if item.origin == "lastfm_similar")
    assert personal.source_user_ids in ({1}, {2})
    assert personal.raw_data["discovery_seed"].startswith("anchor-")
    assert tag_call.await_count == 3
    assert similar_call.await_count == 2


def test_discovery_failure_keeps_top_tracks_fallback():
    with (
        patch("app.services.contextual_pool_service.lastfm_client.is_configured", return_value=True),
        patch(
            "app.services.contextual_pool_service.lastfm_client.get_tag_top_tracks",
            new=AsyncMock(side_effect=RuntimeError("offline")),
        ),
        patch(
            "app.services.contextual_pool_service.lastfm_client.get_similar_tracks",
            new=AsyncMock(side_effect=RuntimeError("offline")),
        ),
    ):
        assert asyncio.run(
            discover_context_candidates([_candidate("anchor", source={1})], PARTY)
        ) == []


def test_blend_reserves_half_prefix_and_keeps_anchor_floor():
    anchors = [_evaluation(_candidate(f"anchor-{index}")) for index in range(50)]
    contextual = [
        _evaluation(_candidate(f"context-{index}", genres=("party",), origin="lastfm_tag"))
        for index in range(30)
    ]

    selected = blend_contextual_candidates(
        anchors + contextual,
        target_size=30,
        contextual_share=0.5,
    )

    origins = [item["candidate"].origin for item in selected]
    assert origins.count("lastfm_tag") == 15
    assert origins.count("spotify_top") == 15
    assert origins[:6] == [
        "spotify_top",
        "lastfm_tag",
        "spotify_top",
        "lastfm_tag",
        "spotify_top",
        "lastfm_tag",
    ]


def test_blend_never_promotes_contextual_candidate_with_veto():
    anchors = [_evaluation(_candidate(f"anchor-{index}")) for index in range(3)]
    blocked = _evaluation(_candidate("blocked", genres=("party",), origin="lastfm_tag"))
    blocked["individual_scores"] = [0.9, 0.05]

    selected = blend_contextual_candidates(
        anchors + [blocked],
        target_size=3,
        contextual_share=0.5,
    )

    assert [item["candidate"].id for item in selected] == [
        "anchor-0",
        "anchor-1",
        "anchor-2",
    ]


def test_party_ranking_is_not_limited_to_sad_top50():
    anchor_payload = {
        "items": [
            {
                "id": f"anchor-{index}",
                "artists": [{"id": f"artist-{index}"}],
            }
            for index in range(50)
        ]
    }
    profile = UserTasteProfile(1, anchor_payload, {"items": []})
    anchors = [_candidate(f"anchor-{index}", source={1}) for index in range(50)]
    contextual = [
        _candidate(
            f"context-{index}",
            genres=("party", "dance"),
            origin="lastfm_tag",
        )
        for index in range(25)
    ]

    ranked = _rank_candidates(
        anchors + contextual,
        [profile],
        "Democrático",
        PARTY,
        contextual_pool_enabled=True,
        contextual_pool_share=0.5,
    )

    first_thirty = ranked[:30]
    assert sum(item.origin.startswith("lastfm_") for item in first_thirty) == 15
    assert sum(item.origin == "spotify_top" for item in first_thirty) == 15
