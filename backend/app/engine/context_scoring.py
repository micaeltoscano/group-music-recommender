"""Pontuação contextual determinística para candidatas (PB-17).

O LLM fornece apenas critérios estruturados. Este módulo puro transforma esses
critérios e os metadados já presentes nos snapshots em um score entre 0 e 1.
Não há acesso a rede, banco ou estado global mutável.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from app.engine.candidates import CandidateTrack


@dataclass(frozen=True)
class ContextCriteria:
    """Critérios normalizados que o motor usa para avaliar uma candidata."""

    occasion: str
    mood: str
    energy: str
    tags_positive: tuple[str, ...] = ()
    tags_negative: tuple[str, ...] = ()
    avoid: tuple[str, ...] = ()


_THEME_KEYWORDS: Mapping[str, frozenset[str]] = {
    "party": frozenset(
        {
            "animada",
            "animado",
            "balada",
            "dance",
            "danca",
            "edm",
            "electronic",
            "eletronica",
            "festa",
            "forro",
            "funk",
            "house",
            "pagode",
            "party",
            "reggaeton",
            "samba",
            "sertanejo",
            "techno",
        }
    ),
    "focus": frozenset(
        {
            "ambient",
            "classical",
            "classica",
            "concentracao",
            "estudo",
            "focus",
            "foco",
            "instrumental",
            "lofi",
            "piano",
            "study",
            "trabalho",
        }
    ),
    "calm": frozenset(
        {
            "acoustic",
            "acustica",
            "ambient",
            "ballad",
            "calma",
            "calmo",
            "chill",
            "dream",
            "dream pop",
            "dreamy",
            "ethereal",
            "meditation",
            "relax",
            "sleep",
            "slow",
            "soft",
            "suave",
            "tranquila",
            "tranquilo",
        }
    ),
    "romantic": frozenset(
        {
            "amor",
            "date",
            "encontro",
            "love",
            "romance",
            "romantica",
            "romantico",
        }
    ),
    "sad": frozenset(
        {
            "melancolica",
            "melancolico",
            "melancholic",
            "melancholy",
            "sad",
            "triste",
            "tristeza",
        }
    ),
    "heavy": frozenset(
        {"agitada", "agitado", "hardcore", "metal", "pesada", "pesado", "punk", "rock"}
    ),
    "explicit": frozenset({"explicit", "explicita", "explicito"}),
}

_HIGH_ENERGY = frozenset(
    {
        "animada",
        "animado",
        "aggressive",
        "dance",
        "danca",
        "edm",
        "electronic",
        "eletronica",
        "energetic",
        "forro",
        "funk",
        "hardcore",
        "hard rock",
        "heavy",
        "heavy rock",
        "hip hop",
        "house",
        "metal",
        "pagode",
        "party",
        "punk rock",
        "reggaeton",
        "samba",
        "sertanejo",
        "techno",
        "trap",
        "upbeat",
    }
)
_LOW_ENERGY = frozenset(
    {
        "acoustic",
        "acustica",
        "ambient",
        "ballad",
        "calma",
        "calmo",
        "chill",
        "classical",
        "classica",
        "instrumental",
        "jazz",
        "lofi",
        "melancholic",
        "melancholy",
        "meditation",
        "piano",
        "sad",
        "sleep",
        "slow",
        "soft",
        "suave",
        "dream",
        "dream pop",
        "dreamy",
        "ethereal",
    }
)
_TARGET_ENERGY = {"baixa": 0.2, "media": 0.55, "alta": 0.9}
_STOP_WORDS = frozenset(
    {"a", "as", "com", "da", "das", "de", "do", "dos", "e", "em", "o", "os", "para", "pra"}
)
_GENERIC_INTENT_TAGS = frozenset(
    {
        "agitada",
        "agitado",
        "alegre",
        "alta",
        "animada",
        "animado",
        "energia",
        "energetic",
        "energetica",
        "energetico",
        "frenetica",
        "frenetico",
        "intensa",
        "intenso",
        "media",
        "pesada",
        "pesado",
        "upbeat",
    }
)


def _normalize(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    ascii_text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", ascii_text.lower()).strip()


def _terms(values: Iterable[object]) -> set[str]:
    result: set[str] = set()
    for value in values:
        normalized = _normalize(value)
        if not normalized:
            continue
        result.add(normalized)
        result.update(
            term
            for term in normalized.split()
            if len(term) >= 3 and term not in _STOP_WORDS
        )
    return result


def _themes(terms: set[str]) -> set[str]:
    return {
        theme
        for theme, keywords in _THEME_KEYWORDS.items()
        if not keywords.isdisjoint(terms)
    }


def _candidate_terms(candidate: CandidateTrack) -> set[str]:
    raw = candidate.raw_data
    album = raw.get("album") or {}
    artists = raw.get("artists") or []
    values: list[object] = [raw.get("name"), album.get("name")]
    values.extend(raw.get("genres") or [])
    values.extend(raw.get("context_tags") or [])
    values.extend(
        artist.get("name")
        for artist in artists
        if isinstance(artist, dict)
    )
    return _terms(values)


def _candidate_labels(candidate: CandidateTrack) -> set[str]:
    """Rótulos musicais completos, sem promover pedaços de subgêneros.

    A camada temática ainda pode entender relações amplas, mas a cobertura de
    uma tag explícita exige o rótulo observado. Assim ``post-punk`` não vira
    prova literal de ``punk`` e ``dream pop`` não vira ``pop`` por acidente.
    """

    raw = candidate.raw_data
    return {
        normalised
        for value in (
            *(raw.get("genres") or []),
            *(raw.get("context_tags") or []),
        )
        if (normalised := _normalize(value))
    }


def specific_context_tags(criteria: ContextCriteria) -> tuple[str, ...]:
    """Extrai gêneros/temas explícitos, removendo apenas adjetivos de energia.

    O LLM pode devolver ``punk, energética, animada`` como tags positivas. Só
    ``punk`` representa, nesse caso, uma intenção musical específica que deve
    receber mais oferta e peso no ranking.
    """
    return tuple(
        dict.fromkeys(
            normalised
            for tag in criteria.tags_positive
            if (normalised := _normalize(tag))
            and normalised not in _GENERIC_INTENT_TAGS
        )
    )


def _contains_any(candidate_terms: set[str], requested_terms: set[str]) -> bool:
    return bool(candidate_terms & requested_terms)


def _candidate_energy(terms: set[str]) -> float:
    high = not _HIGH_ENERGY.isdisjoint(terms)
    # ``post-punk`` e outros subgêneros são quebrados em tokens por
    # ``_terms``. Punk isolado é um sinal de energia; post-punk, sozinho, não.
    if "punk" in terms and "post punk" not in terms:
        high = True
    low = not _LOW_ENERGY.isdisjoint(terms)
    if high and not low:
        return 0.9
    if low and not high:
        return 0.2
    return 0.55


def calculate_context_score(candidate: CandidateTrack, criteria: ContextCriteria) -> float:
    """Retorna adequação contextual em ``[0, 1]`` sem decidir a playlist.

    A ocasião, o humor e as tags positivas definem temas desejados. Tags
    negativas e itens em ``avoid`` aplicam penalidade. A energia é comparada
    com uma estimativa conservadora derivada de gênero/vibe; sem metadados
    suficientes, a estimativa fica neutra.
    """

    candidate_terms = _candidate_terms(candidate)
    candidate_labels = _candidate_labels(candidate)
    candidate_themes = _themes(candidate_terms)

    positive_terms = _terms(
        (criteria.occasion, criteria.mood, *criteria.tags_positive)
    )
    explicit_positive_tags = {
        normalised
        for tag in criteria.tags_positive
        if (normalised := _normalize(tag))
    }
    negative_terms = _terms((*criteria.tags_negative, *criteria.avoid))
    positive_themes = _themes(positive_terms)
    negative_themes = _themes(negative_terms)

    direct_positive = _contains_any(candidate_terms, positive_terms)
    if positive_themes:
        theme_alignment = len(candidate_themes & positive_themes) / len(positive_themes)
        alignment = 0.25 + (0.75 * theme_alignment)
    elif direct_positive:
        alignment = 1.0
    else:
        alignment = 0.5
    if explicit_positive_tags:
        explicit_coverage = (
            len(candidate_labels & explicit_positive_tags)
            / len(explicit_positive_tags)
        )
        # Temas preservam sinônimos (festa -> dance), enquanto a cobertura
        # explícita impede que um rótulo amplo como ``rock`` satisfaça sozinho
        # um pedido mais específico como ``punk + rock``.
        alignment = (alignment * 0.5) + (explicit_coverage * 0.5)

    target_energy = _TARGET_ENERGY.get(_normalize(criteria.energy), 0.55)
    energy_affinity = 1.0 - abs(_candidate_energy(candidate_terms) - target_energy)

    direct_negative = _contains_any(candidate_terms, negative_terms)
    negative_theme_match = bool(candidate_themes & negative_themes)
    penalty = 0.0
    if negative_theme_match:
        penalty += 0.35
    if direct_negative:
        penalty += 0.45

    score = (alignment * 0.65) + (energy_affinity * 0.35) - penalty
    return round(max(0.0, min(1.0, score)), 4)


def enrich_candidate_genres(
    candidates: Sequence[CandidateTrack],
    artist_genres: Mapping[str, Iterable[str]],
) -> list[CandidateTrack]:
    """Copia candidatas anexando gêneros dos artistas dos mesmos snapshots."""

    enriched: list[CandidateTrack] = []
    for candidate in candidates:
        genres = {
            str(genre).strip().lower()
            for genre in candidate.raw_data.get("genres", [])
            if isinstance(genre, str) and genre.strip()
        }
        for artist in candidate.raw_data.get("artists", []):
            if not isinstance(artist, dict) or not artist.get("id"):
                continue
            genres.update(
                str(genre).strip().lower()
                for genre in artist_genres.get(str(artist["id"]), ())
                if isinstance(genre, str) and genre.strip()
            )

        raw_data = dict(candidate.raw_data)
        raw_data["genres"] = sorted(genres)
        enriched.append(
            CandidateTrack(
                candidate.id,
                raw_data,
                set(candidate.source_user_ids),
                origin=candidate.origin,
            )
        )
    return enriched
