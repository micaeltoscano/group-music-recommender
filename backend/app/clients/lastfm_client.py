"""Cliente mínimo e resiliente da API do Last.fm (PB-18/PB-26).

Tags, faixas por tag e similares são consultados. A chave permanece nos
parâmetros da chamada feita pelo backend e nunca é devolvida, registrada ou
incluída nas mensagens de erro da aplicação.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from app.config import settings

LASTFM_API_URL = "https://ws.audioscrobbler.com/2.0/"


class LastFmUnavailableError(RuntimeError):
    """Last.fm não está configurado ou não respondeu de forma utilizável."""


class LastFmInvalidResponseError(RuntimeError):
    """Last.fm respondeu, mas o payload não possui o formato esperado."""


@dataclass(frozen=True, slots=True)
class LastFmTrack:
    """Identidade pública suficiente para resolver uma faixa no Spotify."""

    name: str
    artist: str
    match: float = 0.0
    listeners: int = 0


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


async def _request(method: str, parameters: dict[str, Any]) -> dict[str, Any]:
    if not is_configured():
        raise LastFmUnavailableError("Last.fm não configurado.")

    params: dict[str, Any] = {
        "method": method,
        "api_key": settings.lastfm_api_key,
        "format": "json",
        "autocorrect": 1,
        **parameters,
    }
    try:
        async with httpx.AsyncClient(timeout=settings.lastfm_timeout_seconds) as client:
            response = await client.get(LASTFM_API_URL, params=params)
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, httpx.TimeoutException, ValueError) as exc:
        # Não interpolar a exceção: a URL de um HTTPError pode conter api_key.
        raise LastFmUnavailableError("Falha ao consultar o Last.fm.") from exc

    if not isinstance(payload, dict):
        raise LastFmInvalidResponseError("Envelope inválido na resposta do Last.fm.")
    if payload.get("error") is not None:
        raise LastFmUnavailableError("Last.fm recusou a consulta.")
    return payload


async def _get_top_tags(method: str, identity: dict[str, str]) -> list[str]:
    payload = await _request(method, identity)

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


def _artist_name(raw_artist: object) -> str:
    if isinstance(raw_artist, str):
        return raw_artist.strip()
    if isinstance(raw_artist, dict):
        return str(raw_artist.get("name") or "").strip()
    return ""


def _normalise_tracks(raw_tracks: object) -> list[LastFmTrack]:
    if isinstance(raw_tracks, dict):
        raw_tracks = [raw_tracks]
    if not isinstance(raw_tracks, list):
        raise LastFmInvalidResponseError("Lista de faixas ausente na resposta do Last.fm.")

    tracks: list[LastFmTrack] = []
    seen: set[tuple[str, str]] = set()
    for item in raw_tracks:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        artist = _artist_name(item.get("artist"))
        identity = (name.casefold(), artist.casefold())
        if not name or not artist or identity in seen:
            continue
        seen.add(identity)
        try:
            match = float(item.get("match") or 0.0)
        except (TypeError, ValueError):
            match = 0.0
        try:
            listeners = int(item.get("listeners") or 0)
        except (TypeError, ValueError):
            listeners = 0
        tracks.append(LastFmTrack(name, artist, match, listeners))
    return tracks


async def get_tag_top_tracks(tag: str, *, limit: int = 5) -> list[LastFmTrack]:
    """Descobre faixas representativas de uma tag contextual."""

    payload = await _request("tag.getTopTracks", {"tag": tag, "limit": limit})
    tracks = payload.get("tracks")
    if not isinstance(tracks, dict):
        raise LastFmInvalidResponseError("Bloco de faixas por tag ausente no Last.fm.")
    return _normalise_tracks(tracks.get("track", []))[:limit]


async def get_similar_tracks(
    artist: str,
    track: str,
    *,
    limit: int = 5,
) -> list[LastFmTrack]:
    """Descobre faixas próximas de uma âncora pessoal do grupo."""

    payload = await _request(
        "track.getSimilar",
        {"artist": artist, "track": track, "limit": limit},
    )
    similar = payload.get("similartracks")
    if not isinstance(similar, dict):
        raise LastFmInvalidResponseError("Bloco de faixas similares ausente no Last.fm.")
    return _normalise_tracks(similar.get("track", []))[:limit]
