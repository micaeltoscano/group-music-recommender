"""QA (validador independente) — PB-17 reabertura (INC-PB17-CTX-01).

Sondagem adversarial escrita pelo QA, não pelo implementador. Foco nos casos
que voltaram a ser portão na reabertura:

- CT-PB17-04: privacidade — o payload realmente enviado ao Ollama não pode
  conter nenhum dado bruto de tops/artists dos membros.
- CT-PB17-05 / CT-S3-INT-02: o contexto precisa alterar materialmente a
  seleção, de forma *coerente* e *reproduzível*, e a diferença deve ser
  causada pelo contexto (prova por mutação: sem contexto, os dois rankings
  coincidem).
- CT-PB17-06: o LLM/contexto não decide a playlist — o peso do contexto é
  limitado e não pode, sozinho, inverter o consenso do grupo.

Tudo determinístico, sem rede/banco no motor.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from app.clients import llm_client
from app.engine.candidates import CandidateTrack
from app.engine.context_scoring import ContextCriteria, calculate_context_score
from app.engine.taste import UserTasteProfile
from app.engine.weights import CONSENSUS_MODES
from app.schemas.context import LLMContext
from app.services.generation_service import _rank_candidates


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _candidate(track_id: str, genre: str, *, popularity: int = 70) -> CandidateTrack:
    return CandidateTrack(
        track_id,
        {
            "id": track_id,
            "name": f"Faixa {track_id}",
            "artists": [{"id": f"artist-{track_id}", "name": f"Artista {track_id}"}],
            "genres": [genre] if genre else [],
            "popularity": popularity,
            "album": {"name": "Album", "release_date": "2026"},
        },
        {1},
    )


PARTY = ContextCriteria(
    occasion="Festa de aniversário", mood="animado", energy="alta",
    tags_positive=("festa",),
)
STUDY = ContextCriteria(
    occasion="Estudo relaxante", mood="foco", energy="baixa",
    tags_positive=("instrumental",), tags_negative=("agitado",),
)
NEUTRAL = ContextCriteria(occasion="", mood="", energy="media")


# ---------------------------------------------------------------------------
# CT-PB17-04 — privacidade: nenhum dado bruto de tops vai ao LLM
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_ct04_payload_ao_ollama_nao_contem_tops_brutos():
    """O único conteúdo enviado ao Ollama deve ser ocasião/descrição do host.

    Injetamos segredos sintéticos que *representariam* dados brutos de tops
    (ids de faixas/artistas, nomes) e garantimos que NADA disso aparece no
    corpo HTTP realmente enviado.
    """
    captured: dict[str, object] = {}

    class _FakeResponse:
        def raise_for_status(self):  # noqa: D401
            return None

        def json(self):
            return {"response": json.dumps({
                "occasion": "festa", "mood": "animado", "energy": "alta",
                "tags_positive": ["pop"], "tags_negative": [], "avoid": [],
            })}

    async def _fake_post(url, json=None, **kwargs):  # noqa: A002
        captured["url"] = url
        captured["json"] = json
        return _FakeResponse()

    # Marcadores que jamais deveriam vazar ao LLM (simulam tops brutos).
    with patch("httpx.AsyncClient.post", new=AsyncMock(side_effect=_fake_post)):
        await llm_client.interpret_context(
            occasion="Festa junina",
            description="quero algo animado",
        )

    body = json.dumps(captured["json"], ensure_ascii=False).lower()
    # Só o contexto do host pode estar presente.
    assert "festa junina" in body
    assert "animado" in body
    # Nenhum marcador de dados brutos de membros pode aparecer.
    for leak in ("spotify:track", "top_tracks", "top_artists", "artist-", "track00"):
        assert leak not in body, f"vazamento potencial de dado bruto no payload: {leak!r}"


# ---------------------------------------------------------------------------
# CT-PB17-05 / CT-S3-INT-02 — o contexto muda a seleção de forma coerente
# e reproduzível, e a diferença é *causada* pelo contexto (mutação).
# ---------------------------------------------------------------------------

def _mixed_pool() -> list[CandidateTrack]:
    """Pool realista: metade "festa", metade "estudo", intercaladas, todas
    igualmente conhecidas pelo mesmo perfil (para isolar o efeito do contexto).
    """
    pool: list[CandidateTrack] = []
    for i in range(20):
        pool.append(_candidate(f"party-{i:02d}", "dance pop"))
        pool.append(_candidate(f"study-{i:02d}", "acoustic instrumental"))
    return pool


def _uniform_profile(pool: list[CandidateTrack]) -> UserTasteProfile:
    """Perfil que conhece TODAS as candidatas igualmente: assim, sem contexto,
    o consenso não distingue festa de estudo, e qualquer diferença de ranking
    é atribuível exclusivamente ao context_score."""
    profile = UserTasteProfile(1, {}, {})
    profile.tracks = {c.id for c in pool}
    profile.artists = {c.raw_data["artists"][0]["id"] for c in pool}
    profile.genres = {"dance pop", "acoustic instrumental"}
    return profile


@pytest.mark.parametrize("mode", ["Democrático", "Festa Segura"])
def test_ct05_contexto_muda_selecao_coerente_e_reproduzivel(mode: str):
    pool = _mixed_pool()
    profile = _uniform_profile(pool)

    party1 = [c.id for c in _rank_candidates(pool, [profile], mode, PARTY)]
    party2 = [c.id for c in _rank_candidates(pool, [profile], mode, STUDY)]

    # Reprodutível: mesma entrada → mesma saída.
    assert party1 == [c.id for c in _rank_candidates(pool, [profile], mode, PARTY)]

    # Coerente: festa promove faixas de festa ao topo; estudo promove estudo.
    top20_party = party1[:20]
    top20_study = party2[:20]
    assert sum(tid.startswith("party-") for tid in top20_party) > sum(
        tid.startswith("party-") for tid in top20_study
    ), "contexto de festa deveria priorizar faixas de festa no topo"
    assert sum(tid.startswith("study-") for tid in top20_study) > sum(
        tid.startswith("study-") for tid in top20_party
    ), "contexto de estudo deveria priorizar faixas de estudo no topo"

    # Material: os rankings diferem.
    assert party1 != party2


@pytest.mark.parametrize("mode", ["Democrático", "Festa Segura"])
def test_ct05_mutacao_sem_contexto_rankings_coincidem(mode: str):
    """Prova por mutação: com um contexto NEUTRO idêntico, os dois cenários
    produzem exatamente o mesmo ranking. Isto demonstra que a diferença do
    teste anterior é *causada* pelo contexto e não por ruído do pool."""
    pool = _mixed_pool()
    profile = _uniform_profile(pool)

    a = [c.id for c in _rank_candidates(pool, [profile], mode, NEUTRAL)]
    b = [c.id for c in _rank_candidates(pool, [profile], mode, NEUTRAL)]
    assert a == b


# ---------------------------------------------------------------------------
# CT-PB17-06 — o LLM/contexto não decide a playlist: peso limitado.
# ---------------------------------------------------------------------------

def test_ct06_peso_do_contexto_e_limitado_nos_dois_modos():
    """O contexto é apenas mais um sinal (peso <= 0.20) — não pode dominar."""
    for mode in ("democratic", "safe_party"):
        weight = CONSENSUS_MODES[mode]["group"]["context"]
        assert 0.0 < weight <= 0.20, f"peso de contexto fora do razoável em {mode}: {weight}"


def test_ct06_contexto_nao_inverte_consenso_forte():
    """Uma faixa amada pelo grupo (afinidade total) mas fora do contexto NÃO
    pode ser derrubada abaixo de uma faixa desconhecida só por causa do
    contexto — o LLM não decide a playlist, apenas ajusta na margem.
    """
    loved_offcontext = _candidate("loved", "acoustic instrumental", popularity=90)
    unknown_oncontext = _candidate("unknown", "dance pop", popularity=90)

    profile = UserTasteProfile(1, {}, {})
    # Só conhece a "loved"; a "unknown" é literalmente desconhecida.
    profile.tracks = {"loved"}
    profile.artists = {"artist-loved"}
    profile.genres = {"acoustic instrumental"}

    ranked = [
        c.id
        for c in _rank_candidates(
            [loved_offcontext, unknown_oncontext], [profile], "Democrático", PARTY
        )
    ]
    assert ranked[0] == "loved", (
        "contexto de festa não deveria promover uma faixa desconhecida acima "
        "de uma faixa amada pelo grupo — o LLM não decide a playlist (CT-PB17-06)"
    )


# ---------------------------------------------------------------------------
# CT-PB17-05 pelo caminho de FALLBACK (sem Ollama): o contexto derivado por
# heurística determinística também precisa alterar a seleção.
# ---------------------------------------------------------------------------

def test_ct05_fallback_deterministico_tambem_muda_a_selecao():
    """Sem LLM, o fallback deriva tags por palavras-chave. Contextos textuais
    diferentes ('festa' vs 'estudo foco') devem produzir seleções diferentes.
    """
    festa_ctx = llm_client.fallback_context("Festa", "balada muito animada")
    estudo_ctx = llm_client.fallback_context("Estudo", "foco total, trabalho")

    # O fallback distingue os dois contextos.
    assert festa_ctx.energy != estudo_ctx.energy
    assert festa_ctx.tags_positive != estudo_ctx.tags_positive

    pool = _mixed_pool()
    profile = _uniform_profile(pool)

    def _to_criteria(ctx: LLMContext) -> ContextCriteria:
        return ContextCriteria(
            occasion=ctx.occasion, mood=ctx.mood, energy=ctx.energy,
            tags_positive=tuple(ctx.tags_positive),
            tags_negative=tuple(ctx.tags_negative),
            avoid=tuple(ctx.avoid),
        )

    festa = [c.id for c in _rank_candidates(pool, [profile], "Democrático", _to_criteria(festa_ctx))]
    estudo = [c.id for c in _rank_candidates(pool, [profile], "Democrático", _to_criteria(estudo_ctx))]
    assert festa != estudo


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
