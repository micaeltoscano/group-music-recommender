"""PB-33 — perfil ponderado e seleção limitada de candidatas."""

from __future__ import annotations

import inspect
from itertools import chain

import pytest

from app.engine.weighted_library import (
    PLAYLIST_POOL_TARGET,
    SOURCE_WEIGHTS,
    TOP_POOL_TARGET,
    TRACK_POOL_LIMIT,
    LibraryOriginSignal,
    LibraryTrackSignal,
    build_weighted_profile,
    calculate_weighted_compatibility,
    calculate_weighted_group_affinity,
    combine_origin_weights,
    merge_weighted_candidates,
)


def _origin(kind: str, reference: str, rank: int = 1, access: str | None = None):
    return LibraryOriginSignal(kind, reference, rank, access)


def _track(track_id: str, *origins: LibraryOriginSignal, artist: str | None = None):
    return LibraryTrackSignal(
        spotify_track_id=track_id,
        spotify_uri=f"spotify:track:{track_id}",
        track_name=track_id,
        artist_id=artist or f"Artist{track_id}",
        artist_name="Artista",
        origins=tuple(origins),
    )


def _top(track_id: str, time_range: str = "short_term"):
    return _track(track_id, _origin("top", time_range))


def _playlist(track_id: str, access: str = "owned"):
    return _track(track_id, _origin("playlist", f"Playlist{track_id}", access=access))


def test_ct_pb33_01_pesos_default_centralizados_e_sensiveis():
    assert SOURCE_WEIGHTS == {
        "top:short_term": 1.00,
        "top:medium_term": 0.85,
        "top:long_term": 0.65,
        "playlist:owned": 0.45,
        "playlist:collaborative": 0.35,
    }
    observed = [
        combine_origin_weights([_origin("top", "short_term")]),
        combine_origin_weights([_origin("top", "medium_term")]),
        combine_origin_weights([_origin("top", "long_term")]),
        combine_origin_weights([_origin("playlist", "A", access="owned")]),
        combine_origin_weights([_origin("playlist", "A", access="collaborative")]),
    ]
    assert observed == [1.0, 0.85, 0.65, 0.45, 0.35]
    assert observed == sorted(observed, reverse=True)


def test_ct_pb33_02_multiplas_origens_reforcam_sem_duplicar_ou_superar_um():
    repeated = _track(
        "Shared01",
        _origin("top", "medium_term"),
        _origin("top", "long_term"),
        _origin("playlist", "OwnedA", access="owned"),
        _origin("playlist", "CollabA", access="collaborative"),
    )
    profile = build_weighted_profile(1, [repeated, repeated])

    assert len(profile.tracks) == 1
    assert profile.tracks[0].weight == 0.995
    assert profile.tracks[0].weight <= 1.0
    assert len(profile.tracks[0].origins) == 4
    assert combine_origin_weights(
        [_origin("top", "short_term"), _origin("playlist", "P", access="owned")]
    ) == 1.0


@pytest.mark.parametrize(
    ("size", "expected"),
    [(0, 0), (50, 50), (250, 250), (500, TRACK_POOL_LIMIT)],
)
def test_ct_pb33_03_cap_absoluto_para_bibliotecas_de_todos_os_tamanhos(size, expected):
    library = [_playlist(f"P{index:04d}") for index in range(size)]
    profile = build_weighted_profile(1, library)
    assert len(profile.tracks) == expected
    assert len({track.spotify_track_id for track in profile.tracks}) == expected


def test_ct_pb33_03_alvos_top_playlist_e_redistribuicao_ociosa():
    mixed = build_weighted_profile(
        1,
        chain(
            (_top(f"T{index:04d}", "medium_term") for index in range(200)),
            (_playlist(f"P{index:04d}") for index in range(200)),
        ),
    )
    assert sum(track.has_top_origin for track in mixed.tracks) == TOP_POOL_TARGET
    assert sum(not track.has_top_origin for track in mixed.tracks) == PLAYLIST_POOL_TARGET

    only_tops = build_weighted_profile(1, (_top(f"T{index:04d}") for index in range(300)))
    only_playlists = build_weighted_profile(
        1, (_playlist(f"P{index:04d}") for index in range(300))
    )
    assert len(only_tops.tracks) == len(only_playlists.tracks) == TRACK_POOL_LIMIT


def test_ct_pb33_04_biblioteca_500_nao_da_mais_peso_por_pessoa_que_biblioteca_50():
    shared = _playlist("Shared")
    large = build_weighted_profile(
        10,
        [shared, *(_playlist(f"L{index:04d}") for index in range(499))],
        context_scores={"Shared": 1.0},
    )
    small = build_weighted_profile(
        20,
        [shared, *(_playlist(f"S{index:04d}") for index in range(49))],
        context_scores={"Shared": 1.0},
    )
    candidate = next(
        item for item in merge_weighted_candidates([large, small])
        if item.track.spotify_track_id == "Shared"
    )
    affinity = calculate_weighted_group_affinity(candidate, [large, small])
    candidates = merge_weighted_candidates([large, small])
    voice_totals = {
        user_id: sum(
            contribution.weight
            for item in candidates
            for contribution in item.contributors
            if contribution.user_id == user_id
        )
        for user_id in (10, 20)
    }

    assert len(large.tracks) == 250
    assert len(small.tracks) == 50
    assert voice_totals == pytest.approx({10: 1.0, 20: 1.0})
    assert affinity.individual_scores == pytest.approx((0.004, 0.02))
    assert affinity.average == 0.012
    assert affinity.coverage == 1.0
    assert {item.preference_weight for item in candidate.contributors} == {0.45}


def test_ct_pb33_05_playlist_nao_equivale_a_top_em_afinidade_e_compatibilidade():
    top_profile = build_weighted_profile(1, [_top("Common")])
    playlist_profile = build_weighted_profile(2, [_playlist("Common")])
    same_top = build_weighted_profile(3, [_top("Common")])

    assert top_profile.track_weights["Common"] == 1.0
    assert playlist_profile.track_weights["Common"] == 0.45
    assert calculate_weighted_compatibility(top_profile, playlist_profile) < 1.0
    assert calculate_weighted_compatibility(top_profile, same_top) == 1.0


def test_ct_pb33_06_determinismo_contextual_e_pureza():
    tracks = [_playlist("A"), _playlist("B"), _playlist("C")]
    first = build_weighted_profile(1, tracks, context_scores={"C": 1.0, "A": 0.2})
    second = build_weighted_profile(1, reversed(tracks), context_scores={"A": 0.2, "C": 1.0})

    assert [track.spotify_track_id for track in first.tracks] == ["C", "A", "B"]
    assert first == second
    source = inspect.getsource(inspect.getmodule(build_weighted_profile))
    assert "sqlalchemy" not in source.lower()
    assert "httpx" not in source.lower()
    assert "requests" not in source.lower()


def test_ct_pb33_06_rejeita_contexto_fora_do_intervalo():
    with pytest.raises(ValueError, match="entre 0 e 1"):
        build_weighted_profile(1, [_playlist("A")], context_scores={"A": 1.01})
