"""Sequenciamento puro e determinístico da experiência musical (PB-19).

O módulo recebe somente valores já calculados pelo pipeline. Não acessa banco,
rede nem estado global e devolve a ordem final da playlist.
"""

from __future__ import annotations

import unicodedata
from collections import Counter
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True, slots=True)
class SequencerTrack:
    """Entrada mínima necessária para ordenar uma faixa selecionada."""

    track_id: str
    artist: str
    acceptance: float
    risk: float
    original_position: int = 0


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _artist_key(track: SequencerTrack) -> str:
    normalized = unicodedata.normalize("NFKC", track.artist or "").strip().casefold()
    # Artistas ausentes não devem ser tratados como uma mesma pessoa.
    return normalized or f"__unknown__:{track.track_id}"


def _stable_position(track: SequencerTrack) -> int:
    return track.original_position if track.original_position > 0 else 2**31 - 1


def _select_with_cap(
    tracks: Sequence[SequencerTrack],
    *,
    max_per_artist: int,
    limit: int | None,
) -> list[SequencerTrack]:
    indexed = list(enumerate(tracks, start=1))
    ranked = sorted(
        indexed,
        key=lambda item: (
            -_bounded(item[1].acceptance),
            _bounded(item[1].risk),
            _stable_position(item[1]),
            item[1].track_id,
        ),
    )

    selected: list[SequencerTrack] = []
    artist_counts: Counter[str] = Counter()
    for _, track in ranked:
        artist = _artist_key(track)
        if artist_counts[artist] >= max_per_artist:
            continue
        if limit is not None and len(selected) >= limit:
            break
        selected.append(track)
        artist_counts[artist] += 1
    return selected


def _can_finish_without_adjacent(
    tracks: Sequence[SequencerTrack],
    previous_artist: str,
) -> bool:
    """Verifica a condição de capacidade para o restante da sequência.

    O artista anterior só pode ocupar as posições pares do sufixo; os demais
    podem ocupar até o teto da metade. Isso evita escolhas gulosas que deixem
    uma repetição inevitável no fim quando existia uma solução sem adjacência.
    """

    total = len(tracks)
    if total == 0:
        return True
    counts = Counter(_artist_key(track) for track in tracks)
    previous_capacity = total // 2
    other_capacity = (total + 1) // 2
    return all(
        count <= (previous_capacity if artist == previous_artist else other_capacity)
        for artist, count in counts.items()
    )


def _centrality(position: int, total: int) -> float:
    if total <= 2:
        return 0.0
    center = (total - 1) / 2
    return 1.0 - (abs(position - center) / center)


def _sequence_selected(tracks: Sequence[SequencerTrack]) -> list[SequencerTrack]:
    if not tracks:
        return []

    remaining = list(tracks)
    opener_candidates = list(enumerate(remaining))
    feasible_openers = [
        (index, candidate)
        for index, candidate in opener_candidates
        if _can_finish_without_adjacent(
            remaining[:index] + remaining[index + 1 :],
            _artist_key(candidate),
        )
    ]
    opener = min(
        feasible_openers or opener_candidates,
        key=lambda item: (
            -_bounded(item[1].acceptance),
            _bounded(item[1].risk),
            _stable_position(item[1]),
            item[1].track_id,
        ),
    )[1]
    ordered = [opener]
    remaining.remove(opener)

    total = len(tracks)
    while remaining:
        position = len(ordered)
        desired_risk = _centrality(position, total)
        previous_artist = _artist_key(ordered[-1])
        indexed = list(enumerate(remaining))

        allowed = [item for item in indexed if _artist_key(item[1]) != previous_artist]
        pool = allowed or indexed  # melhor esforço para entrada dominada por um artista

        feasible: list[tuple[int, SequencerTrack]] = []
        for index, candidate in pool:
            tail = remaining[:index] + remaining[index + 1 :]
            if _can_finish_without_adjacent(tail, _artist_key(candidate)):
                feasible.append((index, candidate))
        if feasible:
            pool = feasible

        remaining_artist_counts = Counter(_artist_key(track) for track in remaining)
        max_risk_by_artist = {
            artist: max(
                _bounded(track.risk)
                for track in remaining
                if _artist_key(track) == artist
            )
            for artist in remaining_artist_counts
        }

        def sequencing_key(item: tuple[int, SequencerTrack]) -> tuple:
            candidate = item[1]
            artist = _artist_key(candidate)
            risk = _bounded(candidate.risk)
            # Antes/do centro, use primeiro a faixa mais arriscada de um
            # artista repetido. Assim a irmã menos arriscada ainda pode ocupar
            # a metade final, em vez de empurrar o maior risco para a borda.
            paired_risk_penalty = 0.0
            if position <= (total - 1) / 2 and remaining_artist_counts[artist] > 1:
                paired_risk_penalty = 2.0 * (max_risk_by_artist[artist] - risk)
            return (
                abs(risk - desired_risk) + paired_risk_penalty,
                -_bounded(candidate.acceptance),
                _stable_position(candidate),
                candidate.track_id,
            )

        _, chosen = min(
            pool,
            key=sequencing_key,
        )
        ordered.append(chosen)
        remaining.remove(chosen)

    return ordered


def sequence_tracks(
    tracks: Sequence[SequencerTrack],
    *,
    max_per_artist: int = 2,
    limit: int | None = None,
) -> list[SequencerTrack]:
    """Seleciona e ordena faixas aplicando as regras MVP do PB-19.

    A abertura maximiza aceitação. As demais posições aproximam o risco da
    centralidade da playlist, preservando a não adjacência quando possível.
    Cap, limite e todos os desempates são determinísticos.
    """

    if max_per_artist < 1:
        raise ValueError("max_per_artist deve ser pelo menos 1.")
    if limit is not None and limit < 0:
        raise ValueError("limit não pode ser negativo.")
    if limit == 0:
        return []

    selected = _select_with_cap(
        tracks,
        max_per_artist=max_per_artist,
        limit=limit,
    )
    return _sequence_selected(selected)
