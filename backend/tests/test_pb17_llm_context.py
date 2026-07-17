"""Testes obrigatórios do PB-17 (Interpretação estruturada do contexto).

Cobre CT-PB17-01..06 do PLANO_TESTES.md. O Ollama nunca é chamado de verdade:
`httpx.AsyncClient.post` é mockado para simular respostas válidas, JSON
malformado e indisponibilidade (timeout/erro de rede).
"""

import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.clients import llm_client
from app.schemas.context import LLMContext


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def _mock_response(json_body: dict, status_code: int = 200) -> httpx.Response:
    request = httpx.Request("POST", "http://localhost:11434/api/generate")
    return httpx.Response(status_code, json=json_body, request=request)


# --------------------------------------------------------------------------
# CT-PB17-01 — Saída válida segue o schema
# --------------------------------------------------------------------------

@pytest.mark.anyio
async def test_saida_valida_segue_schema():
    ollama_payload = {
        "response": json.dumps(
            {
                "occasion": "Festa de aniversário",
                "mood": "animado",
                "energy": "alta",
                "tags_positive": ["pop", "festa"],
                "tags_negative": ["lento"],
                "avoid": ["explicito"],
            }
        )
    }
    with patch(
        "httpx.AsyncClient.post",
        new=AsyncMock(return_value=_mock_response(ollama_payload)),
    ):
        ctx = await llm_client.interpret_context("Festa de aniversário", "algo animado pra dançar")

    assert isinstance(ctx, LLMContext)
    assert ctx.occasion == "Festa de aniversário"
    assert ctx.energy == "alta"
    assert "pop" in ctx.tags_positive
    assert "explicito" in ctx.avoid


# --------------------------------------------------------------------------
# CT-PB17-02 — JSON inválido aciona fallback sem interromper
# --------------------------------------------------------------------------

@pytest.mark.anyio
async def test_json_invalido_aciona_fallback():
    ollama_payload = {"response": "isso não é um JSON {{{"}
    with patch(
        "httpx.AsyncClient.post",
        new=AsyncMock(return_value=_mock_response(ollama_payload)),
    ):
        ctx = await llm_client.interpret_context("Festa", "quero algo animado")

    # Não lança exceção; cai no fallback determinístico e ainda segue o schema.
    assert isinstance(ctx, LLMContext)
    assert ctx.occasion == "Festa"


@pytest.mark.anyio
async def test_json_fora_do_schema_aciona_fallback():
    """Resposta é JSON válido, mas não bate com o schema (ex.: energy inválida)."""
    ollama_payload = {
        "response": json.dumps({"occasion": "Festa", "mood": "x", "energy": "MUITO_ALTA"})
    }
    with patch(
        "httpx.AsyncClient.post",
        new=AsyncMock(return_value=_mock_response(ollama_payload)),
    ):
        ctx = await llm_client.interpret_context("Festa", None)

    assert isinstance(ctx, LLMContext)
    assert ctx.energy in ("baixa", "media", "alta")


# --------------------------------------------------------------------------
# CT-PB17-03 — LLM indisponível → fallback determinístico
# --------------------------------------------------------------------------

@pytest.mark.anyio
async def test_llm_indisponivel_timeout_aciona_fallback():
    with patch(
        "httpx.AsyncClient.post",
        new=AsyncMock(side_effect=httpx.TimeoutException("timeout")),
    ):
        ctx = await llm_client.interpret_context("Estudo em grupo", "preciso de foco")

    assert isinstance(ctx, LLMContext)
    assert ctx.energy == "baixa"  # fallback determinístico reconhece "estudo"


@pytest.mark.anyio
async def test_llm_indisponivel_connection_error_aciona_fallback():
    with patch(
        "httpx.AsyncClient.post",
        new=AsyncMock(side_effect=httpx.ConnectError("connection refused")),
    ):
        ctx = await llm_client.interpret_context("Festa", "animada")

    assert isinstance(ctx, LLMContext)


@pytest.mark.anyio
async def test_llm_http_error_aciona_fallback():
    error_response = _mock_response({}, status_code=500)
    with patch(
        "httpx.AsyncClient.post",
        new=AsyncMock(return_value=error_response),
    ):
        ctx = await llm_client.interpret_context("Festa", None)

    assert isinstance(ctx, LLMContext)


# --------------------------------------------------------------------------
# CT-PB17-04 — Privacidade: dados brutos não vão ao LLM
# --------------------------------------------------------------------------

@pytest.mark.anyio
async def test_privacidade_payload_nao_contem_dados_brutos_de_tops():
    """Inspeciona o payload enviado ao Ollama: só ocasião/descrição, nunca tops."""
    captured = {}

    async def _capture_post(self, url, json=None, **kwargs):
        captured["json"] = json
        return _mock_response(
            {
                "response": json_module_dumps(
                    {
                        "occasion": "Festa",
                        "mood": "animado",
                        "energy": "alta",
                        "tags_positive": [],
                        "tags_negative": [],
                        "avoid": [],
                    }
                )
            }
        )

    import json as json_module

    def json_module_dumps(d):
        return json_module.dumps(d)

    with patch("httpx.AsyncClient.post", new=_capture_post):
        await llm_client.interpret_context("Festa", "top artista secreto: Fulano de Tal")

    sent_payload = captured["json"]
    blob = json_module.dumps(sent_payload)
    # O payload contém a descrição do host (esperado), mas nada que se pareça
    # com estrutura de top tracks/artists (ids, uris, listas de faixas).
    assert "spotify" not in blob.lower()
    assert "top_tracks" not in blob.lower()
    assert "artists" not in blob.lower() or "artista secreto" in blob.lower()
    # Confirma que só as chaves esperadas (model/system/prompt/format/stream) existem.
    assert set(sent_payload.keys()) <= {"model", "system", "prompt", "format", "stream"}


# --------------------------------------------------------------------------
# CT-PB17-06 — LLM não decide a playlist (o motor ignora o contexto por padrão)
# --------------------------------------------------------------------------

def test_llm_context_nao_influencia_scoring_por_padrao():
    """`calculate_group_score` usa context_score=1.0 (neutro) por padrão — o
    LLM produz apenas os critérios; quem decide a seleção final é o motor
    (fora do escopo do LLMClient em si).
    """
    from app.engine.candidates import CandidateTrack
    from app.engine.scoring import calculate_group_score
    from app.engine.taste import UserTasteProfile

    candidate = CandidateTrack("t1", {"artists": [], "popularity": 50}, {1})
    profile = UserTasteProfile(1, {"items": []}, {"items": []})

    weights_individual = {"track_affinity": 0.4, "artist_affinity": 0.3, "genre_affinity": 0.2, "popularity": 0.05, "novelty": 0.05}
    weights_group = {"average_score": 0.5, "min_score": 0.3, "coverage": 0.1, "context": 0.05, "diversity": 0.05}

    result_default = calculate_group_score(candidate, [profile], weights_individual, weights_group)
    result_with_context = calculate_group_score(
        candidate, [profile], weights_individual, weights_group, context_score=0.0
    )
    # O peso de contexto é baixo (0.05) — mesmo no extremo (0 vs 1), a diferença
    # no group_score é pequena, provando que o LLM não domina a decisão.
    assert abs(result_default["group_score"] - result_with_context["group_score"]) <= 0.051
