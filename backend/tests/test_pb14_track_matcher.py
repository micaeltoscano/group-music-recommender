"""Testes unitários para a correspondência de faixas (PB-14)."""

import pytest
from app.engine.track_matcher import normalize_string, calculate_match_confidence

def test_normalize_string():
    """Testa remoção de sufixos e limpeza."""
    assert normalize_string("Song Name - Remastered") == "song name"
    assert normalize_string("Another Song (Live at Wembley)") == "another song"
    assert normalize_string("Track [2021 Remaster]") == "track"
    assert normalize_string("Just a normal track") == "just a normal track"
    assert normalize_string("A!@# W3ird N4m3") == "a w3ird n4m3"
    assert normalize_string("") == ""


def test_calculate_match_confidence():
    """Testa o cálculo ponderado de confiança."""
    # Exato
    assert calculate_match_confidence("Hello", "Adele", "Hello", "Adele") == 1.0

    # Diferença menor no nome (ex: case ou sufixos removidos)
    conf = calculate_match_confidence("Hello - Remastered", "Adele", "Hello", "Adele")
    assert conf == 1.0

    # Nome completamente diferente
    conf = calculate_match_confidence("Hello", "Adele", "Rolling in the Deep", "Adele")
    assert conf < 0.6  # Só o artista vai bater (40%)

    # Artista diferente
    conf = calculate_match_confidence("Hello", "Adele", "Hello", "Lionel Richie")
    assert conf < 0.8  # Só o título vai bater (60%)

    # Teste de tipografia parecida
    conf = calculate_match_confidence("Bohemian Rhapsody", "Queen", "Bohemian Rapsody", "Queen")
    assert conf > 0.9  # Erro de digitação mínimo, deve ser bem alto
