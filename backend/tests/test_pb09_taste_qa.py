import pytest
from app.engine.taste import UserTasteProfile, calculate_group_compatibility, calculate_pairwise_compatibility

def test_pb09_qa_missing_keys():
    """Testa robustez contra dicionários malformados ou faltando chaves essenciais."""
    bad_snapshot_1 = {}
    bad_snapshot_2 = {"items": [{"artists": [{}]}]} # missing id everywhere

    profile = UserTasteProfile(1, bad_snapshot_1, bad_snapshot_2)
    assert len(profile.tracks) == 0
    assert len(profile.artists) == 0
    assert len(profile.genres) == 0

def test_pb09_qa_genre_case_insensitivity():
    """Gêneros devem ser case-insensitive e trimados."""
    snapshot = {"items": [{"id": "a1", "genres": [" Pop ", "ROCK", " InDiE"]}]}
    profile = UserTasteProfile(1, {"items": []}, snapshot)
    assert profile.genres == {"pop", "rock", "indie"}

def test_pb09_qa_empty_group():
    """Grupo sem integrantes deve retornar 0.0, não erro."""
    assert calculate_group_compatibility([]) == 0.0

def test_pb09_qa_large_group():
    """Grupo com múltiplos membros (teste de estabilidade da média)."""
    p1 = UserTasteProfile(1, {"items": [{"id": "t1"}]}, {"items": []})
    p2 = UserTasteProfile(2, {"items": [{"id": "t1"}]}, {"items": []})
    p3 = UserTasteProfile(3, {"items": [{"id": "t1"}]}, {"items": []})

    # Todos perfeitamente iguais nas faixas, vazios no resto
    # Pairwise: track_sim=1.0, artist_sim=0.0, genre_sim=0.0
    # Expected pairwise = 1.0 * 0.2 = 0.2
    assert calculate_group_compatibility([p1, p2, p3]) == pytest.approx(0.2)
