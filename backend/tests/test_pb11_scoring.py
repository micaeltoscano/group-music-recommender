"""Testes para o PB-11: Pontuação individual e coletiva."""

import pytest

from app.engine.candidates import CandidateTrack
from app.engine.taste import UserTasteProfile
from app.engine.weights import DEFAULT_INDIVIDUAL_WEIGHTS, DEFAULT_GROUP_WEIGHTS
from app.engine.scoring import calculate_individual_score, calculate_group_score


@pytest.fixture
def sample_candidate():
    return CandidateTrack(
        track_id="t1",
        raw_data={
            "id": "t1",
            "name": "Super Track",
            "artists": [{"id": "a1", "name": "Artist 1"}],
            "genres": ["pop", "dance"],
            "popularity": 80,
            "album": {"release_date": "2024-05-01"}
        },
        source_user_ids={1}
    )


def create_profile(user_id, tracks, artists, genres):
    # Passando dicts vazios para satisfazer a assinatura
    p = UserTasteProfile(user_id, {}, {})
    p.tracks = tracks
    p.artists = artists
    p.genres = genres
    return p


@pytest.fixture
def p_high():
    return create_profile(1, {"t1"}, {"a1"}, {"pop"})


@pytest.fixture
def p_medium():
    return create_profile(2, {"t99"}, {"a1"}, {"rock"})


@pytest.fixture
def p_low():
    return create_profile(3, {"t99"}, {"a99"}, {"rock"})


def test_pb11_individual_score_expected_value(sample_candidate, p_high):
    """
    CT-PB11-01 — Score individual com valor esperado.
    Valores para p_high:
    track_affinity = 1.0 (w=0.4)
    artist_affinity = 1.0 (w=0.3)
    genre_affinity = 1.0 (w=0.2)
    popularity = 0.8 (w=0.05) -> 0.04
    novelty = 1.0 (w=0.05) -> 0.05
    Total esperado: 0.4 + 0.3 + 0.2 + 0.04 + 0.05 = 0.99
    """
    score = calculate_individual_score(sample_candidate, p_high, DEFAULT_INDIVIDUAL_WEIGHTS)
    assert score == 0.99


def test_pb11_group_score_components(sample_candidate, p_high, p_medium, p_low):
    """
    CT-PB11-02 — Score de grupo considera média, mínimo, cobertura, contexto, diversidade.
    """
    profiles = [p_high, p_medium, p_low]
    result = calculate_group_score(
        sample_candidate, 
        profiles, 
        DEFAULT_INDIVIDUAL_WEIGHTS, 
        DEFAULT_GROUP_WEIGHTS
    )
    
    assert "average_score" in result
    assert "min_user_score" in result
    assert "coverage" in result
    assert result["min_user_score"] < result["average_score"]
    # Cobertura: p_high (~0.99) e p_medium (artist=1.0 -> 0.3 + pop/nov=0.09 = 0.39) têm score > 0.1
    # p_low (track=0, artist=0, genre=0, pop/nov=0.09) tem score 0.09, que não é > 0.1
    assert result["coverage"] == round(2 / 3, 4)


def test_pb11_weights_adjustment(sample_candidate, p_high):
    """
    CT-PB11-03 — Pesos centralizados e ajustáveis.
    """
    custom_weights = {
        "track_affinity": 0.0,
        "artist_affinity": 0.0,
        "genre_affinity": 0.0,
        "popularity": 0.0,
        "novelty": 1.0,
    }
    score = calculate_individual_score(sample_candidate, p_high, custom_weights)
    # Com apenas novelty valendo 1.0 e o release_date sendo 2024, novelty = 1.0
    assert score == 1.0


def test_pb11_determinism(sample_candidate, p_medium):
    """
    CT-PB11-04 — Determinismo.
    """
    score1 = calculate_individual_score(sample_candidate, p_medium, DEFAULT_INDIVIDUAL_WEIGHTS)
    score2 = calculate_individual_score(sample_candidate, p_medium, DEFAULT_INDIVIDUAL_WEIGHTS)
    
    assert score1 == score2
    
    # E para o grupo
    result1 = calculate_group_score(sample_candidate, [p_medium], DEFAULT_INDIVIDUAL_WEIGHTS, DEFAULT_GROUP_WEIGHTS)
    result2 = calculate_group_score(sample_candidate, [p_medium], DEFAULT_INDIVIDUAL_WEIGHTS, DEFAULT_GROUP_WEIGHTS)
    
    assert result1 == result2
