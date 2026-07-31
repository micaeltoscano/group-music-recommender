"""Testes adversariais independentes da PB-33."""

from __future__ import annotations

import pytest

from app.engine.weighted_library import (
    LibraryOriginSignal,
    LibraryTrackSignal,
    build_weighted_profile,
    calculate_weighted_compatibility,
    merge_weighted_candidates,
)


def _track(track_id: str, *, user_prefix: str = "", context: bool = False):
    del context
    return LibraryTrackSignal(
        spotify_track_id=track_id,
        spotify_uri=f"spotify:track:{track_id}",
        track_name=track_id,
        artist_id=f"Artist{user_prefix}{track_id}",
        artist_name="QA",
        origins=(
            LibraryOriginSignal(
                source_type="playlist",
                source_ref=f"Playlist{user_prefix}",
                rank=1,
                access_type="owned",
            ),
        ),
    )


def test_qa_compatibilidade_ponderada_e_simetrica():
    first = build_weighted_profile(1, [_track("Shared"), _track("OnlyA")])
    second = build_weighted_profile(2, [_track("Shared"), _track("OnlyB")])

    forward = calculate_weighted_compatibility(first, second)
    backward = calculate_weighted_compatibility(second, first)

    assert 0 < forward < 1
    assert forward == backward


def test_qa_ct_pb33_04_total_de_voz_e_equilibrado_entre_bibliotecas_500_e_50():
    """O tamanho do repertório não pode multiplicar o peso agregado da pessoa."""
    large = build_weighted_profile(
        10,
        (_track(f"Large{index:04d}", user_prefix="L") for index in range(500)),
    )
    small = build_weighted_profile(
        20,
        (_track(f"Small{index:04d}", user_prefix="S") for index in range(50)),
    )
    candidates = merge_weighted_candidates([large, small])
    total_voice = {
        user_id: sum(
            contribution.weight
            for candidate in candidates
            for contribution in candidate.contributors
            if contribution.user_id == user_id
        )
        for user_id in (10, 20)
    }

    assert len(large.tracks) == 250
    assert len(small.tracks) == 50
    assert total_voice[10] == pytest.approx(total_voice[20])
