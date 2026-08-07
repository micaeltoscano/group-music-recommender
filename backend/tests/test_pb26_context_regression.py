"""Regressões do uso real do contexto no pool híbrido (PB-26)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.clients import lastfm_client
from app.db.base import Base
from app.engine.candidates import CandidateTrack
from app.engine.context_scoring import ContextCriteria, calculate_context_score
from app.services.context_enrichment_service import enrich_candidates_context


PUNK_ROCK_PARTY = ContextCriteria(
    occasion="Festa",
    mood="bobo/animada",
    energy="alta",
    tags_positive=("punk", "rock"),
    avoid=("demais suave",),
)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture()
def db(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pb26-context-regression.sqlite3'}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(engine)
    session = factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def _candidate(track_id: str, tags: tuple[str, ...]) -> CandidateTrack:
    return CandidateTrack(
        track_id,
        {
            "name": track_id,
            "artists": [{"name": f"Artist {track_id}"}],
            "genres": [],
            "context_tags": list(tags),
            "popularity": 60,
        },
        {1},
    )


def test_punk_rock_energetico_supera_rock_lento_e_melancolico():
    energetic = _candidate(
        "The Pretender",
        ("hard rock", "rock", "energetic", "post-grunge"),
    )
    slow = _candidate(
        "Go Slowly",
        ("alternative rock", "rock", "dreamy", "melancholy", "slow"),
    )
    post_punk_soft = _candidate(
        "Evangeline",
        ("post-punk", "dream pop", "ethereal", "shoegaze"),
    )

    energetic_score = calculate_context_score(energetic, PUNK_ROCK_PARTY)
    slow_score = calculate_context_score(slow, PUNK_ROCK_PARTY)
    post_punk_score = calculate_context_score(post_punk_soft, PUNK_ROCK_PARTY)

    assert energetic_score >= 0.60
    assert slow_score < 0.60
    assert post_punk_score < 0.60
    assert energetic_score > max(slow_score, post_punk_score)


def test_restricao_suave_penaliza_tema_calmo_sem_correspondencia_literal():
    soft = _candidate("Soft song", ("dream pop", "ethereal", "slow"))
    unrestricted = ContextCriteria(
        occasion=PUNK_ROCK_PARTY.occasion,
        mood=PUNK_ROCK_PARTY.mood,
        energy=PUNK_ROCK_PARTY.energy,
        tags_positive=PUNK_ROCK_PARTY.tags_positive,
    )

    unrestricted_score = calculate_context_score(soft, unrestricted)
    restricted_score = calculate_context_score(soft, PUNK_ROCK_PARTY)

    assert unrestricted_score > restricted_score
    assert restricted_score == 0.0


@pytest.mark.anyio
async def test_similar_recebe_tags_proprias_antes_do_ranking(db, monkeypatch):
    monkeypatch.setattr(lastfm_client.settings, "lastfm_api_key", "fake-key")
    similar = CandidateTrack(
        "lastfm:similar",
        {
            "name": "Actual Punk Track",
            "artists": [{"name": "Actual Punk Band"}],
            "genres": [],
            "context_tags": [],
            "discovery_tags": [],
            "discovery_seed": "spotify-seed",
        },
        {1},
        origin="lastfm_similar",
    )

    with (
        patch.object(
            lastfm_client,
            "get_track_tags",
            AsyncMock(return_value=["Punk", "Hard Rock", "Energetic"]),
        ),
        patch.object(lastfm_client, "get_artist_tags", AsyncMock()) as artist_tags,
    ):
        [enriched] = await enrich_candidates_context(db, [similar])

    assert enriched.raw_data["context_tags"] == ["energetic", "hard rock", "punk"]
    assert "party" not in enriched.raw_data["context_tags"]
    assert enriched.raw_data["genres"] == []
    artist_tags.assert_not_awaited()


@pytest.mark.anyio
async def test_tag_consultada_continua_valida_se_enriquecimento_falhar(db, monkeypatch):
    monkeypatch.setattr(lastfm_client.settings, "lastfm_api_key", "fake-key")
    by_tag = CandidateTrack(
        "lastfm:tag",
        {
            "name": "Punk Candidate",
            "artists": [{"name": "Punk Band"}],
            "genres": [],
            "context_tags": ["punk"],
            "discovery_tags": ["punk"],
        },
        set(),
        origin="lastfm_tag",
    )

    with (
        patch.object(lastfm_client, "get_track_tags", AsyncMock(side_effect=TimeoutError)),
        patch.object(lastfm_client, "get_artist_tags", AsyncMock(side_effect=TimeoutError)),
    ):
        [enriched] = await enrich_candidates_context(db, [by_tag])

    assert enriched.raw_data["context_tags"] == ["punk"]
    assert enriched.raw_data["context_source"] == "lastfm_tag"
    assert enriched.raw_data["context_confidence"] == 0.9
