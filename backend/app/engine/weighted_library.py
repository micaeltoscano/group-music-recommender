"""Perfil ponderado e seleção justa da biblioteca ampliada (PB-33).

Este módulo é deliberadamente puro: recebe DTOs, não conhece ORM e não realiza I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from app.engine.weights import LIBRARY_SOURCE_WEIGHTS as SOURCE_WEIGHTS

TRACK_POOL_LIMIT = 250
TOP_POOL_TARGET = 150
PLAYLIST_POOL_TARGET = 100
RECURRENCE_BONUS_FACTOR = 0.10
CONTEXT_INFLUENCE = 0.15

@dataclass(frozen=True)
class LibraryOriginSignal:
    source_type: str
    source_ref: str
    rank: int
    access_type: str | None = None

    @property
    def weight_key(self) -> str:
        if self.source_type == "top":
            return f"top:{self.source_ref}"
        if self.source_type == "playlist":
            return f"playlist:{self.access_type}"
        return ""


@dataclass(frozen=True)
class LibraryTrackSignal:
    spotify_track_id: str
    spotify_uri: str
    track_name: str | None
    artist_id: str | None
    artist_name: str | None
    origins: tuple[LibraryOriginSignal, ...]


@dataclass(frozen=True)
class WeightedTrack:
    spotify_track_id: str
    spotify_uri: str
    track_name: str | None
    artist_id: str | None
    artist_name: str | None
    weight: float
    context_score: float
    origins: tuple[LibraryOriginSignal, ...]

    @property
    def has_top_origin(self) -> bool:
        return any(origin.source_type == "top" for origin in self.origins)


@dataclass(frozen=True)
class WeightedTasteProfile:
    user_id: int
    tracks: tuple[WeightedTrack, ...]

    @property
    def track_weights(self) -> dict[str, float]:
        return {track.spotify_track_id: track.weight for track in self.tracks}

    @property
    def artist_weights(self) -> dict[str, float]:
        weights: dict[str, float] = {}
        for track in self.tracks:
            if track.artist_id:
                weights[track.artist_id] = max(weights.get(track.artist_id, 0.0), track.weight)
        return weights


@dataclass(frozen=True)
class ContributorWeight:
    user_id: int
    # Parcela do orçamento individual (a soma por pessoa é 1).
    weight: float
    # Força absoluta da origem, preservada para explicação/afinidade.
    preference_weight: float


@dataclass(frozen=True)
class WeightedCandidate:
    track: WeightedTrack
    contributors: tuple[ContributorWeight, ...]

    @property
    def source_user_ids(self) -> frozenset[int]:
        return frozenset(item.user_id for item in self.contributors)


@dataclass(frozen=True)
class WeightedGroupAffinity:
    average: float
    minimum: float
    coverage: float
    individual_scores: tuple[float, ...]


def combine_origin_weights(origins: Iterable[LibraryOriginSignal]) -> float:
    """Combina evidências sem permitir que recorrência ultrapasse preferência máxima."""
    unique = {
        (origin.source_type, origin.source_ref, origin.rank, origin.access_type): origin
        for origin in origins
    }
    weights = sorted(
        (SOURCE_WEIGHTS.get(origin.weight_key, 0.0) for origin in unique.values()),
        reverse=True,
    )
    weights = [weight for weight in weights if weight > 0]
    if not weights:
        return 0.0
    combined = weights[0] + (sum(weights[1:]) * RECURRENCE_BONUS_FACTOR)
    return round(min(1.0, combined), 4)


def _validate_context_scores(scores: Mapping[str, float]) -> None:
    if any(not 0.0 <= value <= 1.0 for value in scores.values()):
        raise ValueError("Scores de contexto devem estar entre 0 e 1.")


def _selection_score(track: WeightedTrack) -> float:
    return (track.weight * (1.0 - CONTEXT_INFLUENCE)) + (
        track.context_score * CONTEXT_INFLUENCE
    )


def _selection_key(track: WeightedTrack) -> tuple[float, float, str]:
    return (-_selection_score(track), -track.weight, track.spotify_track_id)


def build_weighted_profile(
    user_id: int,
    library: Iterable[LibraryTrackSignal],
    *,
    context_scores: Mapping[str, float] | None = None,
) -> WeightedTasteProfile:
    """Deduplica sinais e seleciona Tops/playlists com cap e redistribuição ociosa."""
    scores = context_scores or {}
    _validate_context_scores(scores)
    deduplicated: dict[str, LibraryTrackSignal] = {}
    merged_origins: dict[str, dict[tuple[str, str, int, str | None], LibraryOriginSignal]] = {}
    for signal in library:
        if (
            not signal.spotify_track_id
            or signal.spotify_uri != f"spotify:track:{signal.spotify_track_id}"
        ):
            continue
        deduplicated.setdefault(signal.spotify_track_id, signal)
        target = merged_origins.setdefault(signal.spotify_track_id, {})
        for origin in signal.origins:
            target.setdefault(
                (origin.source_type, origin.source_ref, origin.rank, origin.access_type), origin
            )

    weighted: list[WeightedTrack] = []
    for track_id, signal in deduplicated.items():
        origins = tuple(merged_origins[track_id][key] for key in sorted(merged_origins[track_id]))
        weight = combine_origin_weights(origins)
        if weight == 0:
            continue
        weighted.append(
            WeightedTrack(
                spotify_track_id=track_id,
                spotify_uri=signal.spotify_uri,
                track_name=signal.track_name,
                artist_id=signal.artist_id,
                artist_name=signal.artist_name,
                weight=weight,
                context_score=scores.get(track_id, 0.0),
                origins=origins,
            )
        )

    tops = sorted((track for track in weighted if track.has_top_origin), key=_selection_key)
    playlists = sorted(
        (track for track in weighted if not track.has_top_origin), key=_selection_key
    )
    selected = [*tops[:TOP_POOL_TARGET], *playlists[:PLAYLIST_POOL_TARGET]]
    selected_ids = {track.spotify_track_id for track in selected}
    remaining = sorted(
        (track for track in weighted if track.spotify_track_id not in selected_ids),
        key=_selection_key,
    )
    selected.extend(remaining[: max(0, TRACK_POOL_LIMIT - len(selected))])
    return WeightedTasteProfile(user_id=user_id, tracks=tuple(selected[:TRACK_POOL_LIMIT]))


def weighted_jaccard(first: Mapping[str, float], second: Mapping[str, float]) -> float:
    keys = set(first) | set(second)
    if not keys:
        return 0.0
    denominator = sum(max(first.get(key, 0.0), second.get(key, 0.0)) for key in keys)
    if denominator == 0:
        return 0.0
    numerator = sum(min(first.get(key, 0.0), second.get(key, 0.0)) for key in keys)
    return numerator / denominator


def calculate_weighted_compatibility(
    first: WeightedTasteProfile, second: WeightedTasteProfile
) -> float:
    track_similarity = weighted_jaccard(first.track_weights, second.track_weights)
    artist_similarity = weighted_jaccard(first.artist_weights, second.artist_weights)
    return round((track_similarity * 0.6) + (artist_similarity * 0.4), 4)


def merge_weighted_candidates(
    profiles: Iterable[WeightedTasteProfile],
) -> tuple[WeightedCandidate, ...]:
    """Deduplica o pool coletivo preservando peso de cada contribuidor."""
    ordered_profiles = sorted(profiles, key=lambda item: item.user_id)
    by_track: dict[str, dict[int, WeightedTrack]] = {}
    profile_totals = {
        profile.user_id: sum(track.weight for track in profile.tracks)
        for profile in ordered_profiles
    }
    for profile in ordered_profiles:
        for track in profile.tracks:
            by_track.setdefault(track.spotify_track_id, {})[profile.user_id] = track

    candidates: list[WeightedCandidate] = []
    for track_id in sorted(by_track):
        contributions = by_track[track_id]
        representative = sorted(
            contributions.items(), key=lambda item: (-item[1].weight, item[0])
        )[0][1]
        candidates.append(
            WeightedCandidate(
                track=representative,
                contributors=tuple(
                    ContributorWeight(
                        user_id=user_id,
                        weight=round(
                            contributions[user_id].weight / profile_totals[user_id], 12
                        ),
                        preference_weight=contributions[user_id].weight,
                    )
                    for user_id in sorted(contributions)
                    if profile_totals[user_id] > 0
                ),
            )
        )
    return tuple(candidates)


def calculate_weighted_group_affinity(
    candidate: WeightedCandidate,
    profiles: Iterable[WeightedTasteProfile],
) -> WeightedGroupAffinity:
    """Cada pessoa ocupa uma parcela igual, independentemente do tamanho da biblioteca."""
    ordered_profiles = sorted(profiles, key=lambda item: item.user_id)
    contribution = {item.user_id: item.weight for item in candidate.contributors}
    scores = tuple(contribution.get(profile.user_id, 0.0) for profile in ordered_profiles)
    if not scores:
        return WeightedGroupAffinity(0.0, 0.0, 0.0, ())
    return WeightedGroupAffinity(
        average=round(sum(scores) / len(scores), 4),
        minimum=round(min(scores), 4),
        coverage=round(sum(score > 0 for score in scores) / len(scores), 4),
        individual_scores=scores,
    )
