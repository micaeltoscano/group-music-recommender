"""Cliente do LLM local (Ollama) para interpretação estruturada de contexto (PB-17).

Interpreta a ocasião/descrição livre do host em um `LLMContext` (JSON validado).
**Nunca** decide músicas — apenas produz critérios que o motor (Preference
Negotiation Engine) usa como mais um sinal de scoring, com peso limitado.

Privacidade: só recebe o contexto do host (ocasião/descrição), nunca top
tracks/artists brutos dos membros nem qualquer dado individual.

Robustez: qualquer falha (Ollama indisponível, timeout, resposta fora do
schema) cai no fallback determinístico — a geração da playlist nunca é
interrompida por causa do LLM.
"""

from __future__ import annotations

import json
import logging

import httpx
from pydantic import ValidationError

from app.config import settings
from app.schemas.context import LLMContext

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "Você interpreta o contexto de uma festa/reunião em critérios estruturados "
    "para uma playlist em grupo. Responda APENAS com um JSON no formato exato:\n"
    '{"occasion": string, "mood": string, "energy": "baixa"|"media"|"alta", '
    '"tags_positive": [string], "tags_negative": [string], "avoid": [string]}\n'
    "Não inclua nenhum texto fora do JSON. tags_positive/tags_negative são "
    "gêneros ou vibes musicais (ex.: 'pop', 'animada', 'romantica'). avoid são "
    "temas/estilos a evitar (ex.: 'explicito', 'muito triste')."
)


class LLMUnavailableError(Exception):
    """O serviço Ollama não respondeu (indisponível, timeout, erro de rede/HTTP)."""


class LLMInvalidResponseError(Exception):
    """O LLM respondeu, mas o conteúdo não é um JSON válido conforme o schema."""


async def _call_ollama(prompt: str) -> str:
    """Chama a API HTTP local do Ollama e retorna o texto bruto da resposta."""
    url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"
    payload = {
        "model": settings.ollama_model,
        "system": _SYSTEM_PROMPT,
        "prompt": prompt,
        "format": "json",
        "stream": False,
    }
    try:
        async with httpx.AsyncClient(timeout=settings.ollama_timeout_seconds) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
    except (httpx.HTTPError, httpx.TimeoutException) as exc:
        raise LLMUnavailableError(f"Ollama indisponível: {exc}") from exc

    try:
        body = response.json()
    except (ValueError, json.JSONDecodeError) as exc:
        raise LLMUnavailableError("Resposta do Ollama não é JSON válido no envelope.") from exc

    if not isinstance(body, dict):
        raise LLMUnavailableError(
            f"Envelope de resposta do Ollama não é um objeto (tipo {type(body).__name__})."
        )

    text = body.get("response")
    if not isinstance(text, str) or not text.strip():
        raise LLMUnavailableError("Ollama retornou resposta vazia.")
    return text


def _parse_context(raw_text: str) -> LLMContext:
    """Valida o texto retornado pelo LLM contra o schema `LLMContext`."""
    try:
        data = json.loads(raw_text)
    except (ValueError, json.JSONDecodeError) as exc:
        raise LLMInvalidResponseError(f"JSON malformado do LLM: {exc}") from exc

    try:
        return LLMContext.model_validate(data)
    except ValidationError as exc:
        raise LLMInvalidResponseError(f"JSON fora do schema esperado: {exc}") from exc


def _default_energy(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ("estudo", "relax", "calma", "chill", "tranquil")):
        return "baixa"
    if any(word in lowered for word in ("festa", "balada", "animad", "agito", "pancadão", "pancadao")):
        return "alta"
    return "media"


def fallback_context(occasion: str | None, description: str | None) -> LLMContext:
    """Deriva um contexto determinístico (sem LLM) a partir de palavras-chave simples.

    Usado quando o LLM está indisponível ou retorna algo fora do schema —
    critério 3 do PB-17: a geração sempre segue com consenso/afinidade/popularidade.
    """
    text = " ".join(part for part in (occasion, description) if part).strip()
    lowered = text.lower()

    tags_positive: list[str] = []
    tags_negative: list[str] = []
    avoid: list[str] = []

    if any(word in lowered for word in ("festa", "balada", "aniversário", "aniversario")):
        tags_positive.append("festa")
    if any(word in lowered for word in ("estudo", "trabalho", "foco")):
        tags_positive.append("instrumental")
        tags_negative.append("agitado")
    if any(word in lowered for word in ("relax", "calma", "chill", "tranquil")):
        tags_positive.append("calma")
    if any(word in lowered for word in ("romantic", "romântic", "date", "encontro")):
        tags_positive.append("romantica")
    if any(word in lowered for word in ("triste", "explicit", "pesad")):
        avoid.append("explicito" if "explicit" in lowered else "muito triste")

    return LLMContext(
        occasion=(occasion or "Sem ocasião definida")[:100],
        mood="neutro" if not tags_positive else tags_positive[0],
        energy=_default_energy(text),
        tags_positive=tags_positive,
        tags_negative=tags_negative,
        avoid=avoid,
    )


async def interpret_context(occasion: str | None, description: str | None) -> LLMContext:
    """Interpreta o contexto do host, com fallback determinístico em qualquer falha.

    Só recebe `occasion`/`description` (texto livre do host) — nunca dados de
    tops/artists dos membros, preservando a privacidade exigida pelo PB-17.
    """
    prompt = f"Ocasião: {occasion or '(não informada)'}\nDescrição: {description or '(não informada)'}"

    try:
        raw_text = await _call_ollama(prompt)
        return _parse_context(raw_text)
    except LLMUnavailableError as exc:
        logger.info("LLM indisponível, usando fallback determinístico: %s", exc)
    except LLMInvalidResponseError as exc:
        logger.info("Resposta do LLM inválida, usando fallback determinístico: %s", exc)
    except Exception as exc:  # noqa: BLE001 - último recurso: critério 2 é absoluto.
        # Qualquer falha não prevista ao chamar/interpretar o LLM (ex.: um
        # envelope de resposta em formato inesperado que ainda escape das
        # checagens acima) nunca deve interromper a geração da playlist —
        # cai no fallback determinístico, como qualquer outra "resposta
        # inválida" (critério 2 do PB-17).
        logger.warning("Falha inesperada ao interpretar contexto via LLM, usando fallback: %s", exc)

    return fallback_context(occasion, description)
