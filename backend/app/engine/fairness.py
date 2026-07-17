"""Módulo para aplicar regras de justiça e rejeição às candidatas (PB-12)."""

from typing import Any, Dict, List


def calculate_fairness_score(average_score: float, min_user_score: float) -> float:
    """
    Calcula o fairness score, usando a média harmônica entre a média e o mínimo.
    Dessa forma, a métrica só será alta se AMBOS forem altos.
    """
    if average_score + min_user_score > 0:
        return 2 * (average_score * min_user_score) / (average_score + min_user_score)
    return 0.0


def apply_rejection_penalty(
    group_score_data: Dict[str, Any], 
    penalty_factor: float, 
    veto_threshold: float = 0.05
) -> float:
    """
    Aplica uma penalidade caso algum integrante tenha rejeitado fortemente a música (score <= threshold).
    """
    scores = group_score_data.get("individual_scores", [])
    has_veto = any(s <= veto_threshold for s in scores)
    
    original_score = group_score_data.get("group_score", 0.0)
    if has_veto:
        return round(original_score * (1.0 - penalty_factor), 4)
    return original_score


def evaluate_candidate_fairness(
    group_score_data: Dict[str, Any],
    mode_config: Dict[str, Any],
    veto_threshold: float = 0.05
) -> Dict[str, Any]:
    """
    Acrescenta o fairness_score e o penalized_score na avaliação da candidata.
    """
    result = dict(group_score_data)
    penalty_factor = mode_config.get("rejection_penalty", 0.5)
    
    result["fairness_score"] = round(calculate_fairness_score(
        result.get("average_score", 0.0), 
        result.get("min_user_score", 0.0)
    ), 4)
    
    result["penalized_score"] = apply_rejection_penalty(result, penalty_factor, veto_threshold)
    return result


def elevate_least_represented(
    scored_candidates: List[Dict[str, Any]], 
    target_size: int, 
    num_users: int
) -> List[Dict[str, Any]]:
    """
    Tenta elevar o integrante menos representado trocando a música que ele menos gosta
    por outra que aumente a satisfação dele, sem derrubar a qualidade geral excessivamente.
    """
    if not scored_candidates or target_size >= len(scored_candidates) or num_users <= 0:
        return scored_candidates
        
    # Primeiro ordena pelo score final penalizado
    sorted_cands = sorted(
        scored_candidates, 
        key=lambda c: c.get("penalized_score", 0.0), 
        reverse=True
    )
    
    selected = sorted_cands[:target_size]
    pool = sorted_cands[target_size:]
    
    # Calcular a satisfação total de cada usuário na seleção atual
    user_satisfaction = [0.0] * num_users
    for c in selected:
        for i, s in enumerate(c.get("individual_scores", [])):
            if i < num_users:
                user_satisfaction[i] += s
                
    # Achar o usuário menos satisfeito
    min_user_idx = user_satisfaction.index(min(user_satisfaction))
    
    # Encontrar a música no 'selected' que o min_user_idx menos gosta
    # Para priorizar a remoção de faixas que prejudicam ele
    selected.sort(key=lambda c: c.get("individual_scores", [0]*num_users)[min_user_idx])
    worst_for_min_user = selected[0]
    
    # Encontrar no 'pool' a música que o min_user_idx mais gosta, 
    # desde que seja minimamente aceita pelo grupo (score geral)
    pool.sort(key=lambda c: (
        c.get("individual_scores", [0]*num_users)[min_user_idx], 
        c.get("penalized_score", 0.0)
    ), reverse=True)
    best_for_min_user = pool[0]
    
    # Verificar os ganhos e perdas da troca
    min_user_gain = best_for_min_user.get("individual_scores", [0]*num_users)[min_user_idx] - worst_for_min_user.get("individual_scores", [0]*num_users)[min_user_idx]
    global_loss = worst_for_min_user.get("penalized_score", 0.0) - best_for_min_user.get("penalized_score", 0.0)
    
    # Fazemos a troca se o ganho dele for positivo e o grupo não perder mais de 0.2 no score
    if min_user_gain > 0 and global_loss < 0.2:
        selected[0] = best_for_min_user
        
    # Restaura a ordenação final de quem ficou
    selected.sort(key=lambda c: c.get("penalized_score", 0.0), reverse=True)
    return selected
