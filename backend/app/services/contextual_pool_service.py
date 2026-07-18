"""Descoberta contextual híbrida, com I/O isolado fora do motor puro (PB-26)."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Iterable

from app.clients import lastfm_client
from app.config import settings
from app.engine.candidates import CandidateTrack
from app.engine.context_scoring import ContextCriteria, calculate_context_score

_THEME_TAGS: dict[str, tuple[str, ...]] = {
    "party": ("party", "dance", "pop"),
    "focus": ("focus", "instrumental", "ambient"),
    "calm": ("chill", "acoustic", "ambient"),
    "romantic": ("romantic", "love songs"),
    "workout": ("workout", "energy", "dance"),
}
_THEME_TERMS: dict[str, frozenset[str]] = {
    "party": frozenset({"balada", "dance", "festa", "party", "churrasco"}),
    "focus": frozenset({"concentracao", "estudo", "focus", "trabalho"}),
    "calm": frozenset({"calma", "calmo", "chill", "relax", "tranquila"}),
    "romantic": frozenset({"amor", "date", "romance", "romantica"}),
    "workout": frozenset({"academia", "corrida", "treino", "workout"}),
}


def _normalise(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    ascii_text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", ascii_text.casefold()).strip()


def _identity(name: object, artist: object) -> tuple[str, str]:
    return _normalise(name), _normalise(artist)


def _candidate_identity(candidate: CandidateTrack) -> tuple[str, str]:
    artists = candidate.raw_data.get("artists") or []
    artist = artists[0].get("name") if artists and isinstance(artists[0], dict) else ""
    return _identity(candidate.raw_data.get("name"), artist)


def context_discovery_tags(criteria: ContextCriteria, *, limit: int = 3) -> tuple[str, ...]:
    """Traduz o contexto livre em poucas tags estáveis aceitas pelo Last.fm."""

    requested = _normalise(
        " ".join((criteria.occasion, criteria.mood, *criteria.tags_positive))
    )
    terms = set(requested.split())
    tags: list[str] = []
    for theme, theme_terms in _THEME_TERMS.items():
        if terms & theme_terms:
            tags.extend(_THEME_TAGS[theme])
    if not tags:
        tags.extend(
            _normalise(tag)
            for tag in criteria.tags_positive
            if _normalise(tag)
        )
    if not tags and _normalise(criteria.occasion):
        tags.append(_normalise(criteria.occasion))
    return tuple(dict.fromkeys(tags))[:limit]


def select_personal_seeds(
    anchors: Iterable[CandidateTrack],
    criteria: ContextCriteria,
    *,
    limit: int = 5,
) -> tuple[CandidateTrack, ...]:
    """Escolhe deterministicamente âncoras contextuais, cobrindo membros primeiro."""

    ranked = sorted(
        anchors,
        key=lambda candidate: (
            -calculate_context_score(candidate, criteria),
            candidate.id,
        ),
    )
    selected: list[CandidateTrack] = []
    covered_members: set[int] = set()
    for candidate in ranked:
        if candidate.source_user_ids - covered_members:
            selected.append(candidate)
            covered_members.update(candidate.source_user_ids)
            if len(selected) >= limit:
                return tuple(selected)
    for candidate in ranked:
        if candidate not in selected:
            selected.append(candidate)
            if len(selected) >= limit:
                break
    return tuple(selected)


def _external_candidate(
    name: str,
    artist: str,
    *,
    origin: str,
    context_tags: Iterable[str],
    source_user_ids: set[int],
    seed: CandidateTrack | None = None,
) -> CandidateTrack:
    digest = hashlib.sha256(f"{artist.casefold()}\0{name.casefold()}".encode()).hexdigest()[:24]
    inherited_genres = list(seed.raw_data.get("genres") or []) if seed else []
    raw_data = {
        "name": name,
        "artists": [{"name": artist}],
        "genres": sorted(set(inherited_genres) | set(context_tags)),
        "context_tags": list(dict.fromkeys(context_tags)),
        "context_source": origin,
        "context_confidence": 0.9 if origin == "lastfm_tag" else 0.8,
        # Valor neutro, ligeiramente acima do limiar que historicamente significa
        # rejeição. Ausência no Top não equivale a veto explícito.
        "popularity": 60,
        "candidate_origin": origin,
    }
    if seed is not None:
        raw_data["discovery_seed"] = seed.id
    return CandidateTrack(
        f"lastfm:{digest}",
        raw_data,
        set(source_user_ids),
        origin=origin,
    )


async def discover_context_candidates(
    anchors: list[CandidateTrack],
    criteria: ContextCriteria,
) -> list[CandidateTrack]:
    """Amplia Tops com tags e similares; qualquer falha externa mantém o fallback."""

    if not anchors or not lastfm_client.is_configured():
        return []

    seen = {_candidate_identity(candidate) for candidate in anchors}
    discovered: list[CandidateTrack] = []
    tags = context_discovery_tags(criteria, limit=settings.contextual_pool_tag_count)

    for tag in tags:
        try:
            tracks = await lastfm_client.get_tag_top_tracks(
                tag,
                limit=settings.contextual_pool_tracks_per_source,
            )
        except Exception:  # noqa: BLE001 - a fonte é opcional e falha aberta.
            continue
        for track in tracks:
            identity = _identity(track.name, track.artist)
            if identity in seen:
                continue
            seen.add(identity)
            discovered.append(
                _external_candidate(
                    track.name,
                    track.artist,
                    origin="lastfm_tag",
                    context_tags=(tag,),
                    source_user_ids=set(),
                )
            )

    seeds = select_personal_seeds(
        anchors,
        criteria,
        limit=settings.contextual_pool_seed_count,
    )
    for seed in seeds:
        name, artist = _candidate_identity(seed)
        if not name or not artist:
            continue
        raw_artists = seed.raw_data.get("artists") or []
        display_artist = str(raw_artists[0].get("name") or "")
        display_name = str(seed.raw_data.get("name") or "")
        try:
            tracks = await lastfm_client.get_similar_tracks(
                display_artist,
                display_name,
                limit=settings.contextual_pool_tracks_per_source,
            )
        except Exception:  # noqa: BLE001 - descoberta nunca bloqueia geração.
            continue
        seed_tags = tuple(seed.raw_data.get("context_tags") or ()) + tags
        for track in tracks:
            identity = _identity(track.name, track.artist)
            if identity in seen:
                continue
            seen.add(identity)
            discovered.append(
                _external_candidate(
                    track.name,
                    track.artist,
                    origin="lastfm_similar",
                    context_tags=seed_tags,
                    source_user_ids=set(seed.source_user_ids),
                    seed=seed,
                )
            )
    return discovered[: settings.contextual_pool_max_candidates]
