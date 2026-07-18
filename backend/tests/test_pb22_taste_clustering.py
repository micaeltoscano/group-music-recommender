"""Testes técnicos do PB-22 — agrupamento de perfis musicais."""

from dataclasses import asdict
from itertools import permutations

import pytest

from app.engine.candidates import CandidateTrack
from app.engine.clustering import cluster_taste_profiles
from app.engine.context_scoring import ContextCriteria
from app.engine.taste import UserTasteProfile
from app.services.generation_service import _rank_candidates


def _profile(
    user_id: int,
    *,
    tracks: set[str],
    artists: set[str],
    genres: set[str],
) -> UserTasteProfile:
    profile = UserTasteProfile(user_id, {}, {})
    profile.tracks = tracks
    profile.artists = artists
    profile.genres = genres
    return profile


def _two_clear_groups() -> list[UserTasteProfile]:
    return [
        _profile(1, tracks={"pop-1"}, artists={"artist-pop"}, genres={"pop"}),
        _profile(2, tracks={"pop-2"}, artists={"artist-pop"}, genres={"pop"}),
        _profile(3, tracks={"rock-1"}, artists={"artist-rock"}, genres={"rock"}),
        _profile(4, tracks={"rock-2"}, artists={"artist-rock"}, genres={"rock"}),
    ]


def test_ct_pb22_01_usa_somente_sinais_temporarios_e_nao_os_expoe():
    profiles = _two_clear_groups()
    profiles[0].tracks.add("dado-musical-temporario-sensivel")

    result = cluster_taste_profiles(profiles)
    serialized_result = str(asdict(result))

    assert result.status == "clustered"
    assert "dado-musical-temporario-sensivel" not in serialized_result
    assert tuple(cluster.member_ids for cluster in result.clusters) == ((1, 2), (3, 4))


@pytest.mark.parametrize(
    "profiles, expected_reason",
    [
        (_two_clear_groups()[:2], "três perfis"),
        (
            [
                _profile(1, tracks={"only-signal"}, artists=set(), genres=set()),
                _profile(2, tracks={"t2"}, artists={"a2"}, genres=set()),
                _profile(3, tracks={"t3"}, artists={"a3"}, genres=set()),
            ],
            "sem sinais musicais suficientes",
        ),
        (
            [
                _profile(1, tracks={"t1"}, artists={"a1"}, genres={"g1"}),
                _profile(2, tracks={"t2"}, artists={"a2"}, genres={"g2"}),
                _profile(3, tracks={"t3"}, artists={"a3"}, genres={"g3"}),
            ],
            "Nenhum par",
        ),
    ],
)
def test_ct_pb22_02_identifica_evidencia_insuficiente(profiles, expected_reason):
    result = cluster_taste_profiles(profiles)

    assert result.status == "insufficient_evidence"
    assert result.clusters == ()
    assert expected_reason in result.reason


def test_ct_pb22_03_resultado_e_deterministico_para_qualquer_ordem_de_entrada():
    profiles = _two_clear_groups()
    expected = cluster_taste_profiles(profiles)

    for reordered_profiles in permutations(profiles):
        assert cluster_taste_profiles(reordered_profiles) == expected

    assert expected.status == "clustered"
    assert tuple(cluster.id for cluster in expected.clusters) == ("cluster-01", "cluster-02")
    assert tuple(cluster.member_ids for cluster in expected.clusters) == ((1, 2), (3, 4))


def test_ct_pb22_04_grupo_homogeneo_nao_e_dividido_artificialmente():
    profiles = [
        _profile(
            user_id,
            tracks={"shared-track"},
            artists={"shared-artist"},
            genres={"shared-genre"},
        )
        for user_id in (1, 2, 3, 4)
    ]

    result = cluster_taste_profiles(profiles)

    assert result.status == "single_group"
    assert len(result.clusters) == 1
    assert result.clusters[0].member_ids == (1, 2, 3, 4)


def test_ct_pb22_05_clusters_ficam_disponiveis_no_pipeline_sem_mudar_dados_brutos():
    profiles = _two_clear_groups()
    clustering = cluster_taste_profiles(profiles)
    candidate = CandidateTrack(
        track_id="candidate-across-groups",
        raw_data={
            "id": "candidate-across-groups",
            "artists": [{"id": "new-artist"}],
            "genres": ["indie"],
            "popularity": 50,
        },
        source_user_ids={1, 3},
    )
    original_raw_data = dict(candidate.raw_data)

    ranked = _rank_candidates(
        [candidate],
        profiles,
        "Democrático",
        ContextCriteria(occasion="", mood="", energy=""),
        taste_clusters=clustering,
    )

    assert ranked == [candidate]
    assert candidate.source_cluster_ids == ("cluster-01", "cluster-02")
    assert candidate.raw_data == original_raw_data


@pytest.mark.parametrize("threshold", [-0.01, 1.01])
def test_ct_pb22_06_rejeita_limite_de_similaridade_invalido(threshold):
    with pytest.raises(ValueError, match="entre 0 e 1"):
        cluster_taste_profiles(_two_clear_groups(), similarity_threshold=threshold)


def test_ct_pb22_06_rejeita_ids_de_usuario_duplicados():
    profiles = _two_clear_groups()
    profiles[-1].user_id = 1

    with pytest.raises(ValueError, match="user_id único"):
        cluster_taste_profiles(profiles)
