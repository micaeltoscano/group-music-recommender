"""Testes para o PB-10: Geração do conjunto de candidatas."""

import pytest

from app.engine.candidates import generate_candidate_pool


@pytest.fixture
def snapshot_u1():
    return {
        "items": [
            {"id": "t1", "name": "Track 1"},
            {"id": "t2", "name": "Track 2"},
        ]
    }


@pytest.fixture
def snapshot_u2():
    return {
        "items": [
            {"id": "t2", "name": "Track 2"},
            {"id": "t3", "name": "Track 3"},
        ]
    }


@pytest.fixture
def snapshot_empty():
    return {"items": []}


@pytest.fixture
def snapshot_invalid():
    return {
        "items": [
            {"id": "t4", "name": "Track 4"},
            {"name": "No ID Track"},  # Sem ID
            {"id": None, "name": "Null ID Track"},  # ID nulo
        ]
    }


def test_pb10_pool_contributions_and_deduplication(snapshot_u1, snapshot_u2):
    """
    CT-PB10-01 — Contribuição de diferentes integrantes.
    CT-PB10-02 — Sem duplicatas.
    CT-PB10-03 — Origem registrada.
    """
    snapshots = [
        (1, snapshot_u1),
        (2, snapshot_u2),
    ]
    
    candidates, discarded = generate_candidate_pool(snapshots)
    
    assert len(discarded) == 0
    assert len(candidates) == 3
    
    # Extrair os IDs para conferir a deduplicação e origens
    c_dict = {c.id: c for c in candidates}
    
    assert "t1" in c_dict
    assert c_dict["t1"].source_user_ids == {1}
    
    assert "t2" in c_dict
    assert c_dict["t2"].source_user_ids == {1, 2}  # Origem registrada corretamente
    
    assert "t3" in c_dict
    assert c_dict["t3"].source_user_ids == {2}


def test_pb10_discard_without_id(snapshot_invalid):
    """CT-PB10-04 — Descarte motivado de candidata sem identificação."""
    snapshots = [(3, snapshot_invalid)]
    
    candidates, discarded = generate_candidate_pool(snapshots)
    
    assert len(candidates) == 1
    assert candidates[0].id == "t4"
    
    assert len(discarded) == 2
    assert discarded[0].reason == "Missing track ID"
    assert discarded[0].user_id == 3
    assert discarded[1].reason == "Missing track ID"
    assert discarded[1].user_id == 3


def test_pb10_member_without_data(snapshot_u1, snapshot_empty):
    """CT-PB10-05 — Membro sem dados não quebra o pool."""
    snapshots = [
        (1, snapshot_u1),
        (4, snapshot_empty),
        (5, {}),  # Ausência total da chave 'items'
    ]
    
    candidates, discarded = generate_candidate_pool(snapshots)
    
    assert len(discarded) == 0
    assert len(candidates) == 2  # As duas faixas de u1
    
    c_dict = {c.id: c for c in candidates}
    assert c_dict["t1"].source_user_ids == {1}
    assert c_dict["t2"].source_user_ids == {1}
