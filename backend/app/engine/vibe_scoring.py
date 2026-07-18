"""Pontuacao deterministica das preferencias momentaneas do Vibe Check.

Este modulo e puro: recebe apenas valores normalizados e metadados das
candidatas, sem consultar banco ou rede. O sinal resultante ajusta o ranking na
margem; afinidade, consenso, justica e contexto continuam sendo os componentes
principais da selecao.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable

from app.engine.candidates import CandidateTrack


@dataclass(frozen=True)
class VibePreferences:
    """Preferencias agregadas do grupo, todas no intervalo ``[0, 1]``.

    ``valence`` preserva o nome legado do contrato do PB-07, mas representa a
    tolerancia do grupo a conteudo melancolico: valores baixos penalizam sinais
    tristes e valores altos apenas os tornam aceitaveis.
    """

    energy: float
    valence: float
    popularity: float


_HIGH_ENERGY = frozenset(
    {
        "dance",
        "danca",
        "edm",
        "electronic",
        "eletronica",
        "forro",
        "funk",
        "happy",
        "house",
        "metal",
        "party",
        "pop",
        "reggaeton",
        "rock",
        "samba",
        "techno",
        "trap",
    }
)
_LOW_ENERGY = frozenset(
    {
        "acoustic",
        "acustica",
        "ambient",
        "calm",
        "calma",
        "chill",
        "classical",
        "instrumental",
        "lofi",
        "piano",
        "relax",
        "sleep",
        "suave",
    }
)
_SAD = frozenset(
    {
        "melancholic",
        "melancolica",
        "melancolico",
        "sad",
        "sadness",
        "triste",
        "tristeza",
    }
)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def aggregate_vibe_preferences(
    answers: Iterable[tuple[float, float, float]],
    *,
    total_members: int,
) -> VibePreferences | None:
    """Agrega respostas pela media e trata quem pulou como neutro.

    Sem resposta alguma, retorna ``None`` para que a geracao mantenha exatamente
    o comportamento anterior. Quando apenas parte do grupo responde, os membros
    ausentes contribuem com ``0.5`` e reduzem naturalmente a influencia do sinal.
    """

    normalized = [
        (_clamp(energy), _clamp(valence), _clamp(popularity))
        for energy, valence, popularity in answers
    ]
    if not normalized:
        return None

    denominator = max(total_members, len(normalized), 1)
    missing = max(0, denominator - len(normalized))
    return VibePreferences(
        energy=round((sum(item[0] for item in normalized) + (0.5 * missing)) / denominator, 4),
        valence=round((sum(item[1] for item in normalized) + (0.5 * missing)) / denominator, 4),
        popularity=round(
            (sum(item[2] for item in normalized) + (0.5 * missing)) / denominator,
            4,
        ),
    )


def _normalize(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    ascii_text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", ascii_text.lower()).strip()


def _candidate_terms(candidate: CandidateTrack) -> set[str]:
    raw = candidate.raw_data
    album = raw.get("album") or {}
    values: list[object] = [raw.get("name"), album.get("name")]
    values.extend(raw.get("genres") or [])
    values.extend(
        artist.get("name")
        for artist in raw.get("artists") or []
        if isinstance(artist, dict)
    )

    terms: set[str] = set()
    for value in values:
        normalized = _normalize(value)
        if normalized:
            terms.add(normalized)
            terms.update(normalized.split())
    return terms


def _candidate_energy(terms: set[str]) -> float:
    high = not _HIGH_ENERGY.isdisjoint(terms)
    low = not _LOW_ENERGY.isdisjoint(terms)
    if high and not low:
        return 0.9
    if low and not high:
        return 0.2
    return 0.55


def _candidate_popularity(candidate: CandidateTrack) -> float:
    try:
        return _clamp(float(candidate.raw_data.get("popularity", 50)) / 100.0)
    except (TypeError, ValueError):
        return 0.5


def calculate_vibe_score(candidate: CandidateTrack, preferences: VibePreferences) -> float:
    """Calcula a adequacao da candidata ao Vibe Check em ``[0, 1]``.

    Energia e popularidade usam proximidade ao alvo. Conteudo melancolico usa
    ``valence`` como tolerancia; faixas sem esse sinal ficam neutras nesse eixo.
    """

    terms = _candidate_terms(candidate)
    energy_alignment = 1.0 - abs(_candidate_energy(terms) - preferences.energy)
    popularity_alignment = 1.0 - abs(
        _candidate_popularity(candidate) - preferences.popularity
    )
    sadness_alignment = preferences.valence if not _SAD.isdisjoint(terms) else 0.5

    score = (
        (energy_alignment * 0.35)
        + (sadness_alignment * 0.45)
        + (popularity_alignment * 0.20)
    )
    return round(_clamp(score), 4)
