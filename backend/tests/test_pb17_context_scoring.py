"""Regressão da reabertura do PB-17: contexto precisa alterar o ranking."""

from __future__ import annotations

import pytest

from app.engine.candidates import CandidateTrack
from app.engine.context_scoring import (
    ContextCriteria,
    calculate_context_score,
    enrich_candidate_genres,
)
from app.engine.taste import UserTasteProfile
from app.services.generation_service import _rank_candidates


def _candidate(track_id: str, genre: str, artist_id: str | None = None) -> CandidateTrack:
    artist_id = artist_id or f"artist-{track_id}"
    return CandidateTrack(
        track_id,
        {
            "id": track_id,
            "name": f"Faixa {track_id}",
            "artists": [{"id": artist_id, "name": f"Artista {track_id}"}],
            "genres": [genre],
            "popularity": 70,
            "album": {"name": "Album", "release_date": "2026"},
        },
        {1},
    )


PARTY_CONTEXT = ContextCriteria(
    occasion="Festa de aniversário",
    mood="animado",
    energy="alta",
    tags_positive=("festa",),
)
FOCUS_CONTEXT = ContextCriteria(
    occasion="Estudo",
    mood="foco",
    energy="baixa",
    tags_positive=("instrumental",),
    tags_negative=("agitado",),
)


def test_context_score_muda_com_a_ocasiao_e_energia():
    dance = _candidate("dance", "dance pop")
    focus = _candidate("focus", "acoustic instrumental")

    assert calculate_context_score(dance, PARTY_CONTEXT) > calculate_context_score(
        focus, PARTY_CONTEXT
    )
    assert calculate_context_score(focus, FOCUS_CONTEXT) > calculate_context_score(
        dance, FOCUS_CONTEXT
    )


def test_avoid_penaliza_genero_especifico_sem_penalizar_todo_o_tema():
    funk = _candidate("funk", "funk")
    dance = _candidate("dance", "dance pop")
    context = ContextCriteria(
        occasion="Festa",
        mood="animado",
        energy="alta",
        tags_positive=("festa",),
        avoid=("funk",),
    )

    assert calculate_context_score(dance, context) > calculate_context_score(funk, context)


def test_generos_dos_artistas_enriquecem_candidata_sem_mutar_snapshot():
    original = _candidate("t1", "", artist_id="a1")
    original.raw_data["genres"] = []

    enriched = enrich_candidate_genres([original], {"a1": {"dance pop", "electronic"}})

    assert enriched[0] is not original
    assert enriched[0].raw_data["genres"] == ["dance pop", "electronic"]
    assert original.raw_data["genres"] == []


@pytest.mark.parametrize("mode", ["Democrático", "Festa Segura"])
def test_motor_troca_as_30_primeiras_faixas_conforme_contexto(mode: str):
    """CT-PB17-05/CT-S3-INT-02: o contexto chega ao motor e muda a seleção."""

    dance_tracks = [_candidate(f"dance-{index:02d}", "dance pop") for index in range(30)]
    focus_tracks = [
        _candidate(f"focus-{index:02d}", "acoustic instrumental") for index in range(30)
    ]
    candidates = dance_tracks + focus_tracks
    profile = UserTasteProfile(1, {}, {})
    profile.tracks = {candidate.id for candidate in candidates}
    profile.artists = {
        artist["id"]
        for candidate in candidates
        for artist in candidate.raw_data["artists"]
    }
    profile.genres = {"dance pop", "acoustic instrumental"}

    party_ranking = _rank_candidates(candidates, [profile], mode, PARTY_CONTEXT)
    focus_ranking = _rank_candidates(candidates, [profile], mode, FOCUS_CONTEXT)

    assert all(candidate.id.startswith("dance-") for candidate in party_ranking[:30])
    assert all(candidate.id.startswith("focus-") for candidate in focus_ranking[:30])
    assert [candidate.id for candidate in party_ranking] != [
        candidate.id for candidate in focus_ranking
    ]
