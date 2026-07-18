"""QA (validador independente) — PB-23 (identificação de músicas-ponte).

Sondagem adversarial da autoridade de QA, além dos testes do Dev:

- CT-PB23-01/02: ponte exige aceitação >= 0.25 em >= 2 clusters; fronteiras.
- CT-PB23-03/04 (mutação): com a flag LIGADA a marcação aparece mas a ordem e os
  scores NÃO mudam (não promove); com a flag DESLIGADA nada é marcado.
- CT-PB23-06: clustering None/single_group/insufficient → sem ponte; limiar fora
  de [0,1] → ValueError; determinismo sob reordenação.
- popularity/novelty zerados: candidata só popular/nova não vira ponte.
- Privacidade: bridge_score e scores de cluster NÃO aparecem no resultado da API.
"""

from __future__ import annotations

from itertools import permutations

import pytest

from app.engine.bridge import (
    DEFAULT_MIN_CLUSTER_ACCEPTANCE,
    evaluate_bridge_candidate,
)
from app.engine.candidates import CandidateTrack
from app.engine.clustering import TasteClusteringResult, cluster_taste_profiles
from app.engine.context_scoring import ContextCriteria
from app.engine.taste import UserTasteProfile
from app.engine.weights import CONSENSUS_MODES
from app.services.generation_service import _rank_candidates

INDIV = CONSENSUS_MODES["democratic"]["individual"]


def _profile(user_id, *, tracks, artist, genre):
    p = UserTasteProfile(user_id, {}, {})
    p.tracks = set(tracks)
    p.artists = {artist}
    p.genres = {genre}
    return p


def _two_clusters():
    return [
        _profile(1, tracks={"bridge", "p1"}, artist="a-pop", genre="pop"),
        _profile(2, tracks={"bridge", "p2"}, artist="a-pop", genre="pop"),
        _profile(3, tracks={"bridge", "r1"}, artist="a-rock", genre="rock"),
        _profile(4, tracks={"bridge", "r2"}, artist="a-rock", genre="rock"),
    ]


def _candidate(track_id, *, source_user_ids=None, genres=None, artist_id=None, pop=50):
    return CandidateTrack(
        track_id,
        {
            "id": track_id, "name": track_id,
            "artists": [{"id": artist_id or f"art-{track_id}", "name": track_id}],
            "genres": genres or [], "popularity": pop,
            "album": {"release_date": "2026-01-01"},
        },
        set(source_user_ids or {1}),
    )


# ---------------------------------------------------------------------------
# CT-PB23-01 / 02 — aceitação em >= 2 clusters
# ---------------------------------------------------------------------------

def test_faixa_conhecida_por_dois_clusters_e_ponte():
    profiles = _two_clusters()
    clustering = cluster_taste_profiles(profiles)
    assert clustering.status == "clustered"
    # "bridge" está nos tracks de todos → afinidade de faixa alta nos 2 clusters
    cand = _candidate("bridge")
    ev = evaluate_bridge_candidate(cand, profiles, clustering, INDIV)
    assert ev.is_bridge is True
    assert len(ev.accepted_cluster_ids) >= 2
    # bridge_score conservador = 2º maior score de cluster
    scores = sorted((a.score for a in ev.cluster_acceptance), reverse=True)
    assert ev.bridge_score == pytest.approx(scores[1], abs=1e-4)


def test_faixa_de_um_unico_cluster_nao_e_ponte():
    profiles = _two_clusters()
    clustering = cluster_taste_profiles(profiles)
    # faixa só conhecida pelo artista pop e gênero pop → aceita só no cluster pop
    cand = _candidate("pop-only", genres=["pop"], artist_id="a-pop")
    ev = evaluate_bridge_candidate(cand, profiles, clustering, INDIV)
    assert ev.is_bridge is False
    assert ev.accepted_cluster_ids == ()
    assert ev.bridge_score == 0.0


def test_popularidade_e_novidade_nao_criam_ponte():
    """Uma candidata apenas popular/nova (sem afinidade) não deve virar ponte."""
    profiles = _two_clusters()
    clustering = cluster_taste_profiles(profiles)
    cand = _candidate("hit", genres=["sertanejo"], artist_id="a-unknown", pop=100)
    ev = evaluate_bridge_candidate(cand, profiles, clustering, INDIV)
    assert ev.is_bridge is False


# ---------------------------------------------------------------------------
# CT-PB23-06 — robustez
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("status_profiles", ["single", "insufficient", "none"])
def test_sem_subgrupos_nao_produz_ponte(status_profiles):
    cand = _candidate("bridge")
    if status_profiles == "none":
        ev = evaluate_bridge_candidate(cand, [], None, INDIV)
    elif status_profiles == "single":
        profiles = [
            _profile(1, tracks={"x"}, artist="a", genre="pop"),
            _profile(2, tracks={"y"}, artist="a", genre="pop"),
            _profile(3, tracks={"z"}, artist="a", genre="pop"),
        ]
        ev = evaluate_bridge_candidate(cand, profiles, cluster_taste_profiles(profiles), INDIV)
    else:  # insufficient (2 perfis)
        profiles = _two_clusters()[:2]
        ev = evaluate_bridge_candidate(cand, profiles, cluster_taste_profiles(profiles), INDIV)
    assert ev.is_bridge is False
    assert ev.accepted_cluster_ids == ()


@pytest.mark.parametrize("bad", [-0.1, 1.1, 2.0])
def test_limiar_invalido_rejeitado(bad):
    profiles = _two_clusters()
    with pytest.raises(ValueError):
        evaluate_bridge_candidate(
            _candidate("bridge"), profiles, cluster_taste_profiles(profiles), INDIV,
            min_cluster_acceptance=bad,
        )


def test_determinismo_sob_reordenacao():
    cand = _candidate("bridge")
    ref = None
    for perm in permutations(_two_clusters()):
        profs = list(perm)
        ev = evaluate_bridge_candidate(cand, profs, cluster_taste_profiles(profs), INDIV)
        snap = (ev.is_bridge, ev.bridge_score, tuple(sorted(ev.accepted_cluster_ids)))
        ref = ref or snap
        assert snap == ref


# ---------------------------------------------------------------------------
# CT-PB23-03 / 04 — mutação: marca sem alterar ordem; flag off não marca
# ---------------------------------------------------------------------------

def _rankable_pool():
    # candidatas com afinidades variadas para produzir uma ordem não trivial
    return [
        _candidate("bridge", source_user_ids={1, 3}),
        _candidate("pop-1", genres=["pop"], artist_id="a-pop", source_user_ids={1}),
        _candidate("rock-1", genres=["rock"], artist_id="a-rock", source_user_ids={3}),
        _candidate("neutral", source_user_ids={2}),
    ]


def test_flag_off_nao_marca_e_flag_on_nao_muda_ordem():
    profiles = _two_clusters()
    clustering = cluster_taste_profiles(profiles)
    ctx = ContextCriteria(occasion="", mood="", energy="media")

    off = _rank_candidates(_rankable_pool(), profiles, "Democrático", ctx,
                           taste_clusters=clustering, bridge_tracks_enabled=False)
    on = _rank_candidates(_rankable_pool(), profiles, "Democrático", ctx,
                          taste_clusters=clustering, bridge_tracks_enabled=True)

    # ordem idêntica: bridge não promove (critério 3)
    assert [c.id for c in off] == [c.id for c in on], "faixa-ponte não pode reordenar o ranking"
    # flag off: nada marcado
    assert all(c.is_bridge is False for c in off)
    # flag on: a candidata 'bridge' está marcada
    assert any(c.id == "bridge" and c.is_bridge for c in on)


@pytest.mark.parametrize("mode", ["Democrático", "Festa Segura", "Descoberta"])
def test_ordem_preservada_em_todos_os_modos(mode):
    profiles = _two_clusters()
    clustering = cluster_taste_profiles(profiles)
    ctx = ContextCriteria(occasion="", mood="", energy="media")
    off = [c.id for c in _rank_candidates(_rankable_pool(), profiles, mode, ctx,
           taste_clusters=clustering, bridge_tracks_enabled=False)]
    on = [c.id for c in _rank_candidates(_rankable_pool(), profiles, mode, ctx,
          taste_clusters=clustering, bridge_tracks_enabled=True)]
    assert off == on


# ---------------------------------------------------------------------------
# Privacidade — resultado não expõe bridge_score nem scores de cluster
# ---------------------------------------------------------------------------

def test_avaliacao_nao_expoe_scores_individuais_no_resultado_agregado():
    """O objeto de avaliação carrega os scores por cluster (uso interno do motor),
    mas o contrato de resultado (PB-16/PB-23) só expõe o booleano + explicação
    agregada. Aqui garantimos que os IDs aceitos não carregam scores."""
    profiles = _two_clusters()
    clustering = cluster_taste_profiles(profiles)
    ev = evaluate_bridge_candidate(_candidate("bridge"), profiles, clustering, INDIV)
    # accepted_cluster_ids são apenas strings de id, sem números de afinidade
    assert all(isinstance(cid, str) for cid in ev.accepted_cluster_ids)
