"""Testes para o PB-09: Modelagem de gosto e compatibilidade."""

import pytest

from app.engine.taste import (
    UserTasteProfile,
    calculate_group_compatibility,
    calculate_pairwise_compatibility,
    jaccard_similarity,
)


@pytest.fixture
def empty_snapshot():
    return {"items": []}


@pytest.fixture
def top_tracks_a():
    return {
        "items": [
            {"id": "t1", "artists": [{"id": "a1"}]},
            {"id": "t2", "artists": [{"id": "a2"}]},
        ]
    }


@pytest.fixture
def top_artists_a():
    return {
        "items": [
            {"id": "a1", "genres": ["pop", "rock"]},
            {"id": "a3", "genres": ["indie"]},
        ]
    }


@pytest.fixture
def top_tracks_b():
    return {
        "items": [
            {"id": "t2", "artists": [{"id": "a2"}]},
            {"id": "t3", "artists": [{"id": "a3"}]},
        ]
    }


@pytest.fixture
def top_artists_b():
    return {
        "items": [
            {"id": "a3", "genres": ["indie", "rock"]},
            {"id": "a4", "genres": ["pop"]},
        ]
    }


def test_pb09_user_profile_parsing(top_tracks_a, top_artists_a):
    """O perfil individual deve extrair faixas, artistas e gêneros corretamente."""
    profile = UserTasteProfile(user_id=1, top_tracks_data=top_tracks_a, top_artists_data=top_artists_a)
    
    assert profile.tracks == {"t1", "t2"}
    assert profile.artists == {"a1", "a2", "a3"}
    assert profile.genres == {"pop", "rock", "indie"}


def test_pb09_jaccard_similarity():
    """Valida o cálculo manual do índice de Jaccard."""
    # A = {1, 2}, B = {2, 3}. intersection = {2}, union = {1, 2, 3}. Jaccard = 1/3
    assert jaccard_similarity({"1", "2"}, {"2", "3"}) == pytest.approx(1 / 3)
    
    # Conjuntos vazios
    assert jaccard_similarity(set(), set()) == 0.0
    
    # Um vazio e um não vazio
    assert jaccard_similarity({"1"}, set()) == 0.0


def test_pb09_pairwise_compatibility(top_tracks_a, top_artists_a, top_tracks_b, top_artists_b):
    """
    CT-PB09-01 — Compatibilidade com valores esperados.
    
    User A:
    tracks = {t1, t2}
    artists = {a1, a2, a3}
    genres = {pop, rock, indie}
    
    User B:
    tracks = {t2, t3}
    artists = {a2, a3, a4}
    genres = {indie, rock, pop}
    
    Tracks Jaccard: {t2} / {t1, t2, t3} = 1/3
    Artists Jaccard: {a2, a3} / {a1, a2, a3, a4} = 2/4 = 0.5
    Genres Jaccard: {pop, rock, indie} / {pop, rock, indie} = 3/3 = 1.0
    
    Total = (1/3 * 0.2) + (0.5 * 0.4) + (1.0 * 0.4) = 0.0666... + 0.2 + 0.4 = 0.6666...
    """
    profile_a = UserTasteProfile(1, top_tracks_a, top_artists_a)
    profile_b = UserTasteProfile(2, top_tracks_b, top_artists_b)
    
    score = calculate_pairwise_compatibility(profile_a, profile_b)
    expected_score = (1 / 3 * 0.2) + (0.5 * 0.4) + (1.0 * 0.4)
    assert score == pytest.approx(expected_score)


def test_pb09_group_one_member(top_tracks_a, top_artists_a):
    """CT-PB09-02 — Grupo de um integrante retorna 1.0."""
    profile = UserTasteProfile(1, top_tracks_a, top_artists_a)
    assert calculate_group_compatibility([profile]) == 1.0


def test_pb09_empty_lists_and_disjoint(empty_snapshot, top_tracks_a, top_artists_a):
    """CT-PB09-03 — Listas vazias e ausência de dados."""
    empty_profile = UserTasteProfile(2, empty_snapshot, empty_snapshot)
    normal_profile = UserTasteProfile(1, top_tracks_a, top_artists_a)
    
    # Compatibilidade com listas vazias deve ser 0.0, sem crash
    score = calculate_pairwise_compatibility(empty_profile, normal_profile)
    assert score == 0.0
    
    # Disjunto completo
    disjoint_profile = UserTasteProfile(3, {"items": [{"id": "t99"}]}, {"items": [{"id": "a99", "genres": ["jazz"]}]})
    assert calculate_pairwise_compatibility(normal_profile, disjoint_profile) == 0.0


def test_pb09_determinism(top_tracks_a, top_artists_a, top_tracks_b, top_artists_b):
    """CT-PB09-04 — Determinismo e ausência de rede."""
    profile_a = UserTasteProfile(1, top_tracks_a, top_artists_a)
    profile_b = UserTasteProfile(2, top_tracks_b, top_artists_b)
    
    score1 = calculate_group_compatibility([profile_a, profile_b])
    score2 = calculate_group_compatibility([profile_a, profile_b])
    
    # Se fosse não-determinístico (ex: dependesse de ordem), poderia variar.
    # A ordem dos membros não deve importar
    score3 = calculate_group_compatibility([profile_b, profile_a])
    
    assert score1 == score2
    assert score1 == score3
    # A prova de ausência de rede (I/O) é que este teste roda isolado sem mocks,
    # processando dicionários estáticos rapidamente em memória.
