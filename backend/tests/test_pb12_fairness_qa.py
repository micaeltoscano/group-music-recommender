import pytest
from app.engine.fairness import calculate_fairness_score, apply_rejection_penalty, evaluate_candidate_fairness, elevate_least_represented

def test_pb12_qa_fairness_score_zero_division():
    """Valida divisão por zero em calculate_fairness_score quando ambos são negativos ou zeros."""
    # Se avg + min for zero, deve retornar 0.0
    assert calculate_fairness_score(0.0, 0.0) == 0.0

    # Se avg + min < 0, a condição if average_score + min_user_score > 0 pega
    assert calculate_fairness_score(-1.0, 1.0) == 0.0

def test_pb12_qa_rejection_missing_keys():
    """apply_rejection_penalty com dados faltando chaves não deve crashar."""
    # group_score faltando, individual_scores faltando
    score_data = {}
    assert apply_rejection_penalty(score_data, 0.5) == 0.0

def test_pb12_qa_elevate_least_represented_no_scores():
    """Valida elevação com dicts vazios, zero usuários, etc."""
    scored = [
        {}, # candidata nula
        {}
    ]
    # Se num_users for 0, user_satisfaction será [], min() quebra?
    # Sim, user_satisfaction.index(min(user_satisfaction)) vai falhar se user_satisfaction for vazio.
    # Vamos rodar com num_users=0 para ver.
    try:
        elevate_least_represented(scored, 1, 0)
    except ValueError:
        pytest.fail("Função quebrou com ValueError (min() arg is an empty sequence) quando num_users=0")
