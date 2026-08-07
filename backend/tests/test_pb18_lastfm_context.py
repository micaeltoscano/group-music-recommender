"""Testes do Dev para o PB-18 — contexto Last.fm, cascata e cache."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.clients import lastfm_client
from app.config import settings
from app.db.base import Base
from app.db.models import TrackContextCache
from app.engine.candidates import CandidateTrack
from app.engine.context_scoring import ContextCriteria, calculate_context_score
from app.services.context_enrichment_service import (
    ARTIST_TAGS_SOURCE,
    CONSENSUS_SOURCE,
    SOURCE_CONFIDENCE,
    SPOTIFY_GENRES_SOURCE,
    TRACK_TAGS_SOURCE,
    enrich_candidates_context,
)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture()
def db(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pb18.sqlite3'}",
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


@pytest.fixture(autouse=True)
def configured_lastfm(monkeypatch):
    monkeypatch.setattr(settings, "lastfm_api_key", "fake-lastfm-key")


def _candidate(track_id: str = "spotify-track-1", genres: list[str] | None = None):
    return CandidateTrack(
        track_id,
        {
            "id": track_id,
            "name": "Midnight Song",
            "artists": [{"id": "artist-1", "name": "The Example"}],
            "genres": genres or [],
            "album": {"name": "Example Album"},
        },
        {1},
    )


def _cached(db, track_id: str = "spotify-track-1") -> TrackContextCache:
    return db.query(TrackContextCache).filter_by(spotify_track_id=track_id).one()


# ---------------------------------------------------------------------------
# CT-PB18-01 — faixa antes do artista, com confiança maior
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_tags_da_faixa_tem_prioridade_e_evitam_consulta_do_artista(db):
    track_call = AsyncMock(return_value=["Dance", "Party", "dance"])
    artist_call = AsyncMock(return_value=["pop"])

    with (
        patch.object(lastfm_client, "get_track_tags", track_call),
        patch.object(lastfm_client, "get_artist_tags", artist_call),
    ):
        [enriched] = await enrich_candidates_context(db, [_candidate(genres=["indie pop"])])

    assert enriched.raw_data["context_tags"] == ["dance", "party"]
    assert enriched.raw_data["context_source"] == TRACK_TAGS_SOURCE
    assert enriched.raw_data["context_confidence"] == SOURCE_CONFIDENCE[TRACK_TAGS_SOURCE]
    track_call.assert_awaited_once_with("The Example", "Midnight Song")
    artist_call.assert_not_awaited()

    row = _cached(db)
    assert row.lastfm_track_tags_json == ["dance", "party"]
    assert row.lastfm_artist_tags_json == []
    assert row.spotify_artist_genres_json == ["indie pop"]


# ---------------------------------------------------------------------------
# CT-PB18-02/03 — cascata, fonte e confiança
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_sem_tags_da_faixa_usa_tags_do_artista_com_confianca_menor(db):
    with (
        patch.object(lastfm_client, "get_track_tags", AsyncMock(return_value=[])),
        patch.object(
            lastfm_client,
            "get_artist_tags",
            AsyncMock(return_value=["Alternative", "Rock"]),
        ),
    ):
        [enriched] = await enrich_candidates_context(db, [_candidate(genres=["indie pop"])])

    assert enriched.raw_data["context_tags"] == ["alternative", "rock"]
    assert enriched.raw_data["context_source"] == ARTIST_TAGS_SOURCE
    assert enriched.raw_data["context_confidence"] == SOURCE_CONFIDENCE[ARTIST_TAGS_SOURCE]
    assert SOURCE_CONFIDENCE[ARTIST_TAGS_SOURCE] < SOURCE_CONFIDENCE[TRACK_TAGS_SOURCE]

    row = _cached(db)
    assert row.source == ARTIST_TAGS_SOURCE
    assert row.confidence == SOURCE_CONFIDENCE[ARTIST_TAGS_SOURCE]
    assert row.context_scores_json == {
        "source": ARTIST_TAGS_SOURCE,
        "confidence": SOURCE_CONFIDENCE[ARTIST_TAGS_SOURCE],
    }


@pytest.mark.anyio
async def test_sem_lastfm_usa_generos_spotify_e_depois_consenso(db):
    with (
        patch.object(lastfm_client, "get_track_tags", AsyncMock(return_value=[])),
        patch.object(lastfm_client, "get_artist_tags", AsyncMock(return_value=[])),
    ):
        [with_genres] = await enrich_candidates_context(
            db,
            [_candidate("spotify-genres", ["Dance Pop", "Electronic"])],
        )
        [without_signals] = await enrich_candidates_context(
            db,
            [_candidate("consensus-only")],
        )

    assert with_genres.raw_data["context_source"] == SPOTIFY_GENRES_SOURCE
    assert with_genres.raw_data["context_tags"] == ["dance pop", "electronic"]
    assert with_genres.raw_data["context_confidence"] == SOURCE_CONFIDENCE[SPOTIFY_GENRES_SOURCE]
    assert without_signals.raw_data["context_source"] == CONSENSUS_SOURCE
    assert without_signals.raw_data["context_tags"] == []
    assert without_signals.raw_data["context_confidence"] == SOURCE_CONFIDENCE[CONSENSUS_SOURCE]


# ---------------------------------------------------------------------------
# CT-PB18-04 — cache válido evita nova chamada externa
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_consulta_repetida_reutiliza_cache_valido(db):
    track_call = AsyncMock(return_value=["dream pop"])
    artist_call = AsyncMock(return_value=[])
    candidate = _candidate()

    with (
        patch.object(lastfm_client, "get_track_tags", track_call),
        patch.object(lastfm_client, "get_artist_tags", artist_call),
    ):
        [first] = await enrich_candidates_context(db, [candidate])
        [second] = await enrich_candidates_context(db, [_candidate()])

    assert first.raw_data["context_tags"] == second.raw_data["context_tags"] == ["dream pop"]
    track_call.assert_awaited_once()
    artist_call.assert_not_awaited()
    assert db.query(TrackContextCache).count() == 1


# ---------------------------------------------------------------------------
# CT-PB18-05 — erro/vazio nunca interrompe a geração
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_erros_do_lastfm_caem_para_spotify_sem_propagar(db):
    # Inclui erro não previsto no contrato do cliente: o fallback da camada de
    # serviço ainda deve preservar a geração.
    external_failure = RuntimeError("falha externa inesperada")
    with (
        patch.object(
            lastfm_client,
            "get_track_tags",
            AsyncMock(side_effect=external_failure),
        ),
        patch.object(
            lastfm_client,
            "get_artist_tags",
            AsyncMock(side_effect=external_failure),
        ),
    ):
        [enriched] = await enrich_candidates_context(db, [_candidate(genres=["Synthwave"])])

    assert enriched.raw_data["context_source"] == SPOTIFY_GENRES_SOURCE
    assert enriched.raw_data["context_tags"] == ["synthwave"]
    assert _cached(db).source == SPOTIFY_GENRES_SOURCE


@pytest.mark.anyio
async def test_sem_chave_nao_chama_rede_e_usa_consenso(db, monkeypatch):
    monkeypatch.setattr(settings, "lastfm_api_key", None)
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as http_get:
        [enriched] = await enrich_candidates_context(db, [_candidate()])

    assert enriched.raw_data["context_source"] == CONSENSUS_SOURCE
    http_get.assert_not_awaited()


def test_tags_enriquecidas_participam_do_score_contextual():
    base = _candidate()
    enriched = _candidate("with-lastfm")
    enriched.raw_data["context_tags"] = ["dance", "party"]
    context = ContextCriteria(
        occasion="Festa",
        mood="animado",
        energy="alta",
        tags_positive=("party",),
    )

    assert calculate_context_score(enriched, context) > calculate_context_score(base, context)


@pytest.mark.anyio
async def test_cliente_parseia_envelope_oficial_de_top_tags(monkeypatch):
    monkeypatch.setattr(settings, "lastfm_api_key", "fake-lastfm-key")
    request = httpx.Request("GET", lastfm_client.LASTFM_API_URL)
    response = httpx.Response(
        200,
        json={
            "toptags": {
                "tag": [
                    {"name": "Rock", "count": 100},
                    {"name": "Alternative", "count": 80},
                    {"name": "rock", "count": 60},
                ]
            }
        },
        request=request,
    )
    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=response)) as http_get:
        tags = await lastfm_client.get_track_tags("The Example", "Midnight Song")

    assert tags == ["rock", "alternative"]
    assert http_get.await_args.kwargs["params"]["method"] == "track.getTopTags"
    assert http_get.await_args.kwargs["params"]["artist"] == "The Example"
    assert http_get.await_args.kwargs["params"]["track"] == "Midnight Song"


def test_cache_model_registra_instante_com_timezone(db):
    row = TrackContextCache(
        spotify_track_id="metadata-check",
        track_name="Track",
        artist_name="Artist",
        lastfm_track_tags_json=[],
        lastfm_artist_tags_json=[],
        spotify_artist_genres_json=[],
        context_scores_json={"source": CONSENSUS_SOURCE, "confidence": 0.2},
        source=CONSENSUS_SOURCE,
        confidence=0.2,
        fetched_at=datetime.now(timezone.utc),
    )
    db.add(row)
    db.commit()

    assert row.id is not None
