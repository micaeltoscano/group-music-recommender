"""QA (validador independente) — PB-18 (enriquecimento de contexto com Last.fm).

Sondagem adversarial da autoridade de QA, além dos testes do Dev:

- CT-PB18-01: ordem REAL das chamadas (faixa antes de artista; artista só
  quando a faixa não traz tags) verificada por espião de sequência.
- CT-PB18-04: cache válido **não** chama a rede (mutação: cliente lança se
  chamado); cache expirado re-consulta.
- CT-PB18-03: confiança exata por fonte (0.95/0.75/0.50/0.20).
- CT-PB18-05: exceção inesperada do cliente (não só HTTP) não propaga.
- Privacidade: a chave do Last.fm nunca aparece no cache persistido nem na
  candidata enriquecida.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.clients import lastfm_client
from app.config import settings
from app.db.base import Base
from app.db.models import TrackContextCache
from app.engine.candidates import CandidateTrack
from app.services import context_enrichment_service as svc
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
        f"sqlite:///{tmp_path / 'pb18-qa.sqlite3'}",
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
    monkeypatch.setattr(settings, "lastfm_api_key", "SEGREDO-LASTFM-KEY")


def _candidate(track_id="t1", genres=None):
    return CandidateTrack(
        track_id,
        {
            "id": track_id,
            "name": "Midnight Song",
            "artists": [{"id": "a1", "name": "The Example"}],
            "genres": genres or [],
            "album": {"name": "Album"},
        },
        {1},
    )


# ---------------------------------------------------------------------------
# CT-PB18-01 — ordem real: faixa antes de artista; artista só se faixa vazia
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_ordem_das_chamadas_faixa_antes_artista(db, monkeypatch):
    calls: list[str] = []

    async def _track(artist, track):
        calls.append("track")
        return []  # faixa sem tags -> deve cair para artista

    async def _artist(artist):
        calls.append("artist")
        return ["indie", "rock"]

    monkeypatch.setattr(lastfm_client, "get_track_tags", _track)
    monkeypatch.setattr(lastfm_client, "get_artist_tags", _artist)

    out = await enrich_candidates_context(db, [_candidate()])
    assert calls == ["track", "artist"], f"ordem/uso inesperado: {calls}"
    assert out[0].raw_data["context_source"] == ARTIST_TAGS_SOURCE


@pytest.mark.anyio
async def test_faixa_com_tags_nao_consulta_artista(db, monkeypatch):
    calls: list[str] = []

    async def _track(artist, track):
        calls.append("track")
        return ["synthpop"]

    async def _artist(artist):
        calls.append("artist")
        return ["nao-deveria"]

    monkeypatch.setattr(lastfm_client, "get_track_tags", _track)
    monkeypatch.setattr(lastfm_client, "get_artist_tags", _artist)

    out = await enrich_candidates_context(db, [_candidate()])
    assert calls == ["track"], "artista não deveria ser consultado quando a faixa tem tags"
    assert out[0].raw_data["context_source"] == TRACK_TAGS_SOURCE
    assert out[0].raw_data["context_tags"] == ["synthpop"]


# ---------------------------------------------------------------------------
# CT-PB18-04 — cache válido não chama a rede; cache expirado re-consulta
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_cache_valido_nao_chama_a_rede(db, monkeypatch):
    async def _boom(*args, **kwargs):
        raise AssertionError("a rede NÃO deveria ser chamada com cache válido")

    # pré-popula cache fresco
    db.add(
        TrackContextCache(
            spotify_track_id="t1",
            track_name="Midnight Song",
            artist_name="The Example",
            lastfm_track_tags_json=["cached-tag"],
            lastfm_artist_tags_json=[],
            spotify_artist_genres_json=[],
            source=TRACK_TAGS_SOURCE,
            confidence=0.95,
            context_scores_json={"source": TRACK_TAGS_SOURCE, "confidence": 0.95},
            fetched_at=datetime.now(timezone.utc),
        )
    )
    db.commit()

    monkeypatch.setattr(lastfm_client, "get_track_tags", _boom)
    monkeypatch.setattr(lastfm_client, "get_artist_tags", _boom)

    out = await enrich_candidates_context(db, [_candidate()])
    assert out[0].raw_data["context_tags"] == ["cached-tag"]
    assert out[0].raw_data["context_source"] == TRACK_TAGS_SOURCE


@pytest.mark.anyio
async def test_cache_expirado_reconsulta(db, monkeypatch):
    stale = datetime.now(timezone.utc) - timedelta(days=settings.lastfm_cache_ttl_days + 1)
    db.add(
        TrackContextCache(
            spotify_track_id="t1",
            track_name="Midnight Song",
            artist_name="The Example",
            lastfm_track_tags_json=["old-tag"],
            lastfm_artist_tags_json=[],
            spotify_artist_genres_json=[],
            source=TRACK_TAGS_SOURCE,
            confidence=0.95,
            context_scores_json={"source": TRACK_TAGS_SOURCE, "confidence": 0.95},
            fetched_at=stale,
        )
    )
    db.commit()

    called = {"n": 0}

    async def _track(artist, track):
        called["n"] += 1
        return ["fresh-tag"]

    monkeypatch.setattr(lastfm_client, "get_track_tags", _track)

    out = await enrich_candidates_context(db, [_candidate()])
    assert called["n"] == 1, "cache expirado deveria disparar nova consulta"
    assert out[0].raw_data["context_tags"] == ["fresh-tag"]


# ---------------------------------------------------------------------------
# CT-PB18-03 — confiança exata por fonte
# ---------------------------------------------------------------------------

def test_confianca_por_fonte_valores_esperados():
    assert SOURCE_CONFIDENCE[TRACK_TAGS_SOURCE] == 0.95
    assert SOURCE_CONFIDENCE[ARTIST_TAGS_SOURCE] == 0.75
    assert SOURCE_CONFIDENCE[SPOTIFY_GENRES_SOURCE] == 0.50
    assert SOURCE_CONFIDENCE[CONSENSUS_SOURCE] == 0.20


@pytest.mark.anyio
async def test_cascata_ate_consenso_sem_tags_nem_generos(db, monkeypatch):
    async def _empty(*args, **kwargs):
        return []

    monkeypatch.setattr(lastfm_client, "get_track_tags", _empty)
    monkeypatch.setattr(lastfm_client, "get_artist_tags", _empty)

    out = await enrich_candidates_context(db, [_candidate(genres=[])])
    row = db.query(TrackContextCache).filter_by(spotify_track_id="t1").one()
    assert out[0].raw_data["context_source"] == CONSENSUS_SOURCE
    assert row.confidence == 0.20
    assert out[0].raw_data["context_tags"] == []


# ---------------------------------------------------------------------------
# CT-PB18-05 — exceção inesperada do cliente não propaga
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_excecao_inesperada_do_cliente_nao_interrompe(db, monkeypatch):
    async def _kaboom(*args, **kwargs):
        raise RuntimeError("erro totalmente inesperado")

    monkeypatch.setattr(lastfm_client, "get_track_tags", _kaboom)
    monkeypatch.setattr(lastfm_client, "get_artist_tags", _kaboom)

    # tem gêneros Spotify → cascata deve cair neles, sem levantar
    out = await enrich_candidates_context(db, [_candidate(genres=["indie pop"])])
    assert out[0].raw_data["context_source"] == SPOTIFY_GENRES_SOURCE
    assert out[0].raw_data["context_tags"] == ["indie pop"]


# ---------------------------------------------------------------------------
# Privacidade — a chave nunca aparece no cache nem na candidata
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_chave_lastfm_nao_vaza_no_cache_nem_na_candidata(db, monkeypatch):
    async def _track(artist, track):
        return ["dreampop"]

    monkeypatch.setattr(lastfm_client, "get_track_tags", _track)

    out = await enrich_candidates_context(db, [_candidate()])
    row = db.query(TrackContextCache).filter_by(spotify_track_id="t1").one()

    persisted = str(
        [
            row.track_name,
            row.artist_name,
            row.lastfm_track_tags_json,
            row.lastfm_artist_tags_json,
            row.spotify_artist_genres_json,
            row.source,
            row.confidence,
            row.context_scores_json,
        ]
    )
    candidate_blob = str(out[0].raw_data)
    assert "SEGREDO-LASTFM-KEY" not in persisted
    assert "SEGREDO-LASTFM-KEY" not in candidate_blob
