"""Cliente mínimo e resiliente da API de tags do Last.fm (PB-18).

Somente artist/track.getTopTags são usados. A chave permanece nos parâmetros
da chamada feita pelo backend e nunca é devolvida, registrada ou incluída nas
mensagens de erro da aplicação.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.config import settings

LASTFM_API_URL = "https://ws.audioscrobbler.com/2.0/"


class LastFmUnavailableError(RuntimeError):
    """Last.fm não está configurado ou não respondeu de forma utilizável."""


class LastFmInvalidResponseError(RuntimeError):
    """Last.fm respondeu, mas o payload não possui o formato esperado."""


def is_configured() -> bool:
    """Indica se o caminho externo pode ser tentado sem expor a chave."""

    return bool(settings.lastfm_api_key and settings.lastfm_api_key.strip())


def _normalise_tags(raw_tags: object) -> list[str]:
    if isinstance(raw_tags, dict):
        raw_tags = [raw_tags]
    if not isinstance(raw_tags, list):
        raise LastFmInvalidResponseError("Lista de tags ausente na resposta do Last.fm.")

    result: list[str] = []
    seen: set[str] = set()
    for item in raw_tags:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            continue
        tag = item["name"].strip().lower()
        if tag and tag not in seen:
            result.append(tag)
            seen.add(tag)
    return result


async def _get_top_tags(method: str, identity: dict[str, str]) -> list[str]:
    if not is_configured():
        raise LastFmUnavailableError("Last.fm não configurado.")

    params: dict[str, Any] = {
        "method": method,
        "api_key": settings.lastfm_api_key,
        "format": "json",
        "autocorrect": 1,
        **identity,
    }
    try:
        async with httpx.AsyncClient(timeout=settings.lastfm_timeout_seconds) as client:
            response = await client.get(LASTFM_API_URL, params=params)
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, httpx.TimeoutException, ValueError) as exc:
        # Não interpolar a exceção: a URL de um HTTPError pode conter api_key.
        raise LastFmUnavailableError("Falha ao consultar tags no Last.fm.") from exc

    if not isinstance(payload, dict):
        raise LastFmInvalidResponseError("Envelope inválido na resposta do Last.fm.")
    if payload.get("error") is not None:
        raise LastFmUnavailableError("Last.fm recusou a consulta de tags.")

    top_tags = payload.get("toptags")
    if not isinstance(top_tags, dict):
        raise LastFmInvalidResponseError("Bloco de tags ausente na resposta do Last.fm.")
    return _normalise_tags(top_tags.get("tag", []))


async def get_track_tags(artist: str, track: str) -> list[str]:
    """Busca tags da faixa, que têm prioridade máxima na cascata."""

    return await _get_top_tags(
        "track.getTopTags",
        {"artist": artist, "track": track},
    )


async def get_artist_tags(artist: str) -> list[str]:
    """Busca tags do artista quando a faixa não possui tags úteis."""

    return await _get_top_tags("artist.getTopTags", {"artist": artist})
