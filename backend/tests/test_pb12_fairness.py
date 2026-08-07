"""Testes para o PB-12: Rejeição, justiça e modos de consenso."""

import pytest
from app.engine.fairness import (
    calculate_fairness_score,
    apply_rejection_penalty,
    evaluate_candidate_fairness,
    elevate_least_represented
)
from app.engine.weights import CONSENSUS_MODES


@pytest.fixture
def group_score_popular_with_veto():
    # Média alta, mas um dos usuários odeia a música (score 0.0)
    return {
        "group_score": 0.8,
        "average_score": 0.85,
        "min_user_score": 0.0,
        "coverage": 0.9,
        "individual_scores": [1.0, 1.0, 1.0, 1.0, 0.0]
    }


@pytest.fixture
def group_score_least_misery_A():
    return {
        "group_score": 0.8,
        "average_score": 1.0,
        "min_user_score": 0.1,  # = 1/10
        "coverage": 0.6,
        "individual_scores": [1.0, 1.0, 0.1]
    }


@pytest.fixture
def group_score_least_misery_B():
    return {
        "group_score": 0.7,
        "average_score": 0.7,
        "min_user_score": 0.7,
        "coverage": 1.0,
        "individual_scores": [0.7, 0.7, 0.7]
    }


def test_pb12_veto_derruba_faixa_popular(group_score_popular_with_veto):
    """
    CT-PB12-01 — Veto forte derruba faixa popular.
    """
    mode = CONSENSUS_MODES["democratic"]
    result = evaluate_candidate_fairness(group_score_popular_with_veto, mode, veto_threshold=0.05)

    # Democratic penalty_factor is 0.5. So 0.8 * 0.5 = 0.4
    assert result["penalized_score"] == 0.4
    assert result["penalized_score"] < group_score_popular_with_veto["group_score"]


def test_pb12_least_misery_vs_media(group_score_least_misery_A, group_score_least_misery_B):
    """
    CT-PB12-02 — Least misery vs média simples.
    """
    # Justificando que o fairness capta a discrepância
    f_A = calculate_fairness_score(group_score_least_misery_A["average_score"], group_score_least_misery_A["min_user_score"])
    f_B = calculate_fairness_score(group_score_least_misery_B["average_score"], group_score_least_misery_B["min_user_score"])

    # A tem média 1.0 e min 0.1 -> Harmonica = 0.18
    # B tem média 0.7 e min 0.7 -> Harmonica = 0.7
    assert f_B > f_A


def test_pb12_metricas_justica(group_score_popular_with_veto):
    """
    CT-PB12-03 — Métricas de justiça calculadas.
    """
    result = evaluate_candidate_fairness(group_score_popular_with_veto, CONSENSUS_MODES["democratic"])
    assert "fairness_score" in result
    assert "penalized_score" in result
    assert result["fairness_score"] == 0.0  # Média harmônica de 0.85 e 0.0 é 0.0


def test_pb12_modo_democratico():
    """
    CT-PB12-04 — Modo Democrático (pesos iguais).
    """
    # Apenas verificamos se as chaves existem e os pesos são adequados
    mode = CONSENSUS_MODES["democratic"]
    assert mode["group"]["average_score"] > 0
    assert mode["rejection_penalty"] == 0.5


def test_pb12_modo_festa_segura(group_score_popular_with_veto):
    """
    CT-PB12-05 — Modo Festa Segura (familiaridade/baixa rejeição).
    """
    mode = CONSENSUS_MODES["safe_party"]
    result = evaluate_candidate_fairness(group_score_popular_with_veto, mode)
    # Festa Segura tem penalidade 1.0. A faixa cai pra 0.
    assert result["penalized_score"] == 0.0


def test_pb12_elevar_minimo():
    """
    CT-PB12-06 — Elevação do integrante menos representado.
    """
    c1 = {"id": "c1", "individual_scores": [1.0, 1.0, 0.9], "penalized_score": 0.9}
    c2 = {"id": "c2", "individual_scores": [0.8, 0.8, 0.8], "penalized_score": 0.8}
    c3 = {"id": "c3", "individual_scores": [0.9, 0.9, 0.0], "penalized_score": 0.7} # pior para U3

    c_pool = {"id": "cp", "individual_scores": [0.6, 0.6, 1.0], "penalized_score": 0.65} # Excelente pra U3

    # target_size=3, array de 4 (3 selecionadas, 1 no pool)
    # Usuários = 3
    # A seleção original teria c1, c2, c3
    # Satisfação original U3 = 0.9 + 0.8 + 0.0 = 1.7
    # c3 será a pior pro U3 na seleção.
    # best pro U3 no pool é c_pool
    # Ganho do U3 = 1.0 - 0.0 = 1.0
    # Perda Global = c3.penalized(0.7) - c_pool.penalized(0.65) = 0.05
    # Ganho > 0 e Perda < 0.2 -> a troca DEVE ocorrer!

    candidates = [c1, c2, c3, c_pool]
    selected = elevate_least_represented(candidates, target_size=3, num_users=3)

    assert len(selected) == 3
    ids = [c["id"] for c in selected]
    assert "cp" in ids
    assert "c3" not in ids
