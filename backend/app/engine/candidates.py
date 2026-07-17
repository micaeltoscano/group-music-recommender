"""Geração do conjunto de candidatas (PNE)."""

from typing import Any, Dict, List, Set, Tuple


class CandidateTrack:
    """Uma música candidata agregada no pool."""

    def __init__(self, track_id: str, raw_data: Dict[str, Any], source_user_ids: Set[int]):
        self.id = track_id
        self.raw_data = raw_data
        self.source_user_ids = source_user_ids


class DiscardedTrack:
    """Uma música descartada durante a formação do pool."""

    def __init__(self, raw_data: Dict[str, Any], reason: str, user_id: int):
        self.raw_data = raw_data
        self.reason = reason
        self.user_id = user_id


def generate_candidate_pool(
    snapshots: List[Tuple[int, Dict[str, Any]]]
) -> Tuple[List[CandidateTrack], List[DiscardedTrack]]:
    """
    Gera o pool de músicas candidatas a partir dos snapshots dos integrantes.
    
    Args:
        snapshots: Lista de tuplas contendo (user_id, top_tracks_json).
        
    Returns:
        Uma tupla (candidatas, descartadas), onde:
        - candidatas: Lista de objetos CandidateTrack, deduplicada pelo track_id.
        - descartadas: Lista de objetos DiscardedTrack.
    """
    candidates: Dict[str, CandidateTrack] = {}
    discarded: List[DiscardedTrack] = []

    for user_id, top_tracks_json in snapshots:
        items = top_tracks_json.get("items") or []
        
        for item in items:
            track_id = item.get("id")
            
            # Se não houver ID, descartamos motivadamente.
            if not track_id:
                discarded.append(DiscardedTrack(item, "Missing track ID", user_id))
                continue
                
            if track_id in candidates:
                # Deduplicação: apenas adiciona o usuário à lista de origem
                candidates[track_id].source_user_ids.add(user_id)
            else:
                # Nova candidata
                candidates[track_id] = CandidateTrack(
                    track_id=track_id,
                    raw_data=item,
                    source_user_ids={user_id}
                )
                
    return list(candidates.values()), discarded
