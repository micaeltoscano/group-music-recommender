"""Testes do Dev para a correcao DEF-S3-INT-03-01."""

from app.engine.candidates import CandidateTrack
from app.engine.context_scoring import ContextCriteria
from app.engine.taste import UserTasteProfile
from app.engine.vibe_scoring import (
    VibePreferences,
    aggregate_vibe_preferences,
    calculate_vibe_score,
)
from app.services.generation_service import _rank_candidates


def _candidate(track_id: str, genre: str, *, popularity: int = 50) -> CandidateTrack:
    return CandidateTrack(
        track_id,
        {
            "id": track_id,
            "name": track_id,
            "artists": [{"id": f"artist-{track_id}", "name": f"Artist {track_id}"}],
            "genres": [genre],
            "popularity": popularity,
        },
        {1},
    )


def test_baixa_tolerancia_penaliza_faixa_triste() -> None:
    sad = _candidate("sad-track", "sad")
    low_tolerance = VibePreferences(energy=0.5, valence=0.0, popularity=0.5)
    high_tolerance = VibePreferences(energy=0.5, valence=1.0, popularity=0.5)

    assert calculate_vibe_score(sad, low_tolerance) < calculate_vibe_score(
        sad, high_tolerance
    )


def test_energia_e_popularidade_aproximam_a_candidata_do_alvo() -> None:
    energetic_hit = _candidate("party-track", "dance pop", popularity=90)
    calm_obscure = _candidate("calm-track", "ambient", popularity=10)
    party = VibePreferences(energy=0.9, valence=0.5, popularity=0.9)

    assert calculate_vibe_score(energetic_hit, party) > calculate_vibe_score(
        calm_obscure, party
    )


def test_sem_respostas_mantem_sinal_ausente() -> None:
    assert aggregate_vibe_preferences([], total_members=3) is None


def test_membros_que_pulam_entram_com_valor_neutro() -> None:
    preferences = aggregate_vibe_preferences(
        [(1.0, 0.0, 1.0)],
        total_members=2,
    )

    assert preferences == VibePreferences(energy=0.75, valence=0.25, popularity=0.75)


def test_vibe_check_nao_inverte_afinidade_forte() -> None:
    loved_sad = _candidate("loved-sad", "sad", popularity=50)
    unknown_happy = _candidate("unknown-happy", "happy pop", popularity=100)
    profile = UserTasteProfile(
        1,
        {"items": [loved_sad.raw_data]},
        {"items": []},
    )
    neutral_context = ContextCriteria(
        occasion="",
        mood="",
        energy="media",
    )
    low_sadness_tolerance = VibePreferences(
        energy=0.9,
        valence=0.0,
        popularity=1.0,
    )

    ranked = _rank_candidates(
        [unknown_happy, loved_sad],
        [profile],
        "Democrático",
        neutral_context,
        low_sadness_tolerance,
    )

    assert ranked[0].id == loved_sad.id
