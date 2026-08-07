"""QA (validador independente) — correção de DEF-S3-INT-03-01 (Vibe Check no ranking).

Sondagem adversarial escrita pela autoridade de QA, não pelo implementador.
Verifica além do teste do Dev:

- limite de influência: o Vibe Check ajusta na margem e NÃO inverte um consenso
  forte (não decide a playlist);
- pular preserva o comportamento anterior (sem respostas → ranking idêntico);
- respostas parciais (parte do grupo pula) não quebram e diluem o sinal;
- semântica de `valence`: baixa penaliza faixas tristes, alta as tolera, de
  forma monotônica.
"""

from __future__ import annotations

import pytest

from app.engine.candidates import CandidateTrack
from app.engine.context_scoring import ContextCriteria
from app.engine.taste import UserTasteProfile
from app.engine.vibe_scoring import (
    VibePreferences,
    aggregate_vibe_preferences,
    calculate_vibe_score,
)
from app.engine.weights import VIBE_CHECK_INFLUENCE
from app.services.generation_service import _rank_candidates

NEUTRAL_CTX = ContextCriteria(occasion="", mood="", energy="media")


def _candidate(track_id: str, genre: str, *, popularity: int = 70) -> CandidateTrack:
    return CandidateTrack(
        track_id,
        {
            "id": track_id,
            "name": f"Faixa {track_id}",
            "artists": [{"id": f"art-{track_id}", "name": f"Art {track_id}"}],
            "genres": [genre],
            "popularity": popularity,
            "album": {"name": "Album", "release_date": "2026"},
        },
        {1},
    )


# ---------------------------------------------------------------------------
# Limite de influência: 0.20 e não inverte consenso forte
# ---------------------------------------------------------------------------

def test_influencia_do_vibe_check_e_limitada():
    assert 0.0 < VIBE_CHECK_INFLUENCE <= 0.25


def test_vibe_check_nao_inverte_consenso_forte():
    """Uma faixa amada pelo grupo (afinidade total), ainda que triste, não pode
    ser derrubada abaixo de uma faixa desconhecida só porque o grupo tem baixa
    tolerância a tristeza. O Vibe Check ajusta na margem, não decide."""
    loved_sad = _candidate("loved", "sad", popularity=90)
    unknown_happy = _candidate("unknown", "happy dance", popularity=90)

    profile = UserTasteProfile(1, {}, {})
    profile.tracks = {"loved"}          # só conhece a triste amada
    profile.artists = {"art-loved"}
    profile.genres = {"sad"}

    prefs = VibePreferences(energy=0.5, valence=0.0, popularity=0.5)  # odeia tristeza
    ranked = [
        c.id
        for c in _rank_candidates(
            [loved_sad, unknown_happy], [profile], "Democrático", NEUTRAL_CTX, prefs
        )
    ]
    assert ranked[0] == "loved", (
        "o Vibe Check (baixa tolerância) não deveria promover uma faixa "
        "desconhecida acima de uma faixa amada pelo grupo — não decide a playlist"
    )


# ---------------------------------------------------------------------------
# Pular preserva o comportamento anterior
# ---------------------------------------------------------------------------

def test_sem_respostas_ranking_identico_ao_anterior():
    pool = [_candidate(f"t{i:02d}", "sad" if i % 2 else "happy dance") for i in range(20)]
    profile = UserTasteProfile(1, {}, {})
    profile.tracks = {c.id for c in pool}
    profile.artists = {c.raw_data["artists"][0]["id"] for c in pool}
    profile.genres = {"sad", "happy dance"}

    without_vibe = [c.id for c in _rank_candidates(pool, [profile], "Democrático", NEUTRAL_CTX, None)]
    # aggregate de zero respostas -> None -> mesmo caminho
    prefs = aggregate_vibe_preferences([], total_members=1)
    assert prefs is None
    with_none = [c.id for c in _rank_candidates(pool, [profile], "Democrático", NEUTRAL_CTX, prefs)]
    assert without_vibe == with_none


# ---------------------------------------------------------------------------
# Respostas parciais: quem pula conta como neutro (0.5), sem quebrar
# ---------------------------------------------------------------------------

def test_respostas_parciais_diluem_o_sinal():
    # 1 de 4 membros respondeu valence=0.0 (odeia tristeza).
    only_one = aggregate_vibe_preferences([(0.5, 0.0, 0.5)], total_members=4)
    # 4 de 4 responderam valence=0.0.
    everyone = aggregate_vibe_preferences([(0.5, 0.0, 0.5)] * 4, total_members=4)
    assert only_one is not None and everyone is not None
    # Com só um respondente, a valence agregada fica mais perto do neutro (0.5)
    # do que quando todos respondem — sinal diluído.
    assert only_one.valence > everyone.valence
    assert everyone.valence == pytest.approx(0.0, abs=1e-6)


# ---------------------------------------------------------------------------
# Semântica de valence: monotônica e penaliza tristeza
# ---------------------------------------------------------------------------

def test_valence_baixa_penaliza_faixa_triste_mais_que_valence_alta():
    sad = _candidate("sad", "sad")
    low = calculate_vibe_score(sad, VibePreferences(energy=0.5, valence=0.0, popularity=0.5))
    mid = calculate_vibe_score(sad, VibePreferences(energy=0.5, valence=0.5, popularity=0.5))
    high = calculate_vibe_score(sad, VibePreferences(energy=0.5, valence=1.0, popularity=0.5))
    # monotônico crescente em valence para uma faixa triste
    assert low < mid < high


def test_valence_nao_afeta_faixa_sem_sinal_de_tristeza():
    """Faixa sem sinal triste fica neutra nesse eixo — valence não deve mudar o
    seu score de tristeza (evita penalizar/beneficiar o pool inteiro)."""
    happy = _candidate("happy", "happy dance")
    low = calculate_vibe_score(happy, VibePreferences(energy=0.5, valence=0.0, popularity=0.5))
    high = calculate_vibe_score(happy, VibePreferences(energy=0.5, valence=1.0, popularity=0.5))
    assert low == high
