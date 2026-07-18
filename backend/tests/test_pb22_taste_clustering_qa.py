"""QA (validador independente) — PB-22 (agrupamento de perfis musicais).

Sondagem adversarial da autoridade de QA, além dos testes do Dev:

- CT-PB22-01 (privacidade): o resultado não replica faixas/artistas/gêneros brutos,
  só IDs e scores.
- CT-PB22-02: <3 perfis, perfil esparso (<2 sinais) e nenhum par acima do limiar →
  `insufficient_evidence`.
- CT-PB22-03: determinismo sob TODAS as permutações de entrada (clusters, IDs,
  similaridades idênticos).
- CT-PB22-04: grupo homogêneo → `single_group` (sem divisão falsa).
- CT-PB22-05 + mutação: candidatas recebem os cluster IDs dos seus membros, e a
  presença dos clusters NÃO altera o ranking (score inalterado no PB-22).
- CT-PB22-06: limiar fora de [0,1] e user_id duplicado → ValueError.
"""

from __future__ import annotations

from dataclasses import asdict
from itertools import permutations

import pytest

from app.engine.candidates import CandidateTrack
from app.engine.clustering import (
    DEFAULT_SIMILARITY_THRESHOLD,
    cluster_taste_profiles,
)
from app.engine.context_scoring import ContextCriteria
from app.engine.taste import UserTasteProfile
from app.services.generation_service import _rank_candidates


def _profile(user_id, *, tracks, artists, genres):
    p = UserTasteProfile(user_id, {}, {})
    p.tracks = set(tracks)
    p.artists = set(artists)
    p.genres = set(genres)
    return p


def _two_groups():
    return [
        _profile(1, tracks={"t-pop-1"}, artists={"a-pop"}, genres={"pop"}),
        _profile(2, tracks={"t-pop-2"}, artists={"a-pop"}, genres={"pop"}),
        _profile(3, tracks={"t-rock-1"}, artists={"a-rock"}, genres={"rock"}),
        _profile(4, tracks={"t-rock-2"}, artists={"a-rock"}, genres={"rock"}),
    ]


# ---------------------------------------------------------------------------
# CT-PB22-01 — privacidade
# ---------------------------------------------------------------------------

def test_resultado_nao_replica_dados_brutos():
    profiles = _two_groups()
    profiles[0].tracks.add("SEGREDO-FAIXA")
    profiles[2].artists.add("SEGREDO-ARTISTA")
    result = cluster_taste_profiles(profiles)
    blob = str(asdict(result))
    assert "SEGREDO-FAIXA" not in blob
    assert "SEGREDO-ARTISTA" not in blob
    # só IDs de usuário aparecem nos clusters
    assert all(isinstance(m, int) for c in result.clusters for m in c.member_ids)


# ---------------------------------------------------------------------------
# CT-PB22-02 — evidência insuficiente
# ---------------------------------------------------------------------------

def test_menos_de_tres_perfis():
    r = cluster_taste_profiles(_two_groups()[:2])
    assert r.status == "insufficient_evidence"
    assert r.clusters == ()


def test_perfil_esparso_bloqueia():
    profiles = _two_groups()
    profiles[1] = _profile(2, tracks={"t-pop-2"}, artists=set(), genres=set())  # 1 sinal
    r = cluster_taste_profiles(profiles)
    assert r.status == "insufficient_evidence"


def test_nenhum_par_acima_do_limiar():
    # quatro perfis totalmente disjuntos → nenhum par similar
    profiles = [
        _profile(1, tracks={"t1"}, artists={"a1"}, genres={"g1"}),
        _profile(2, tracks={"t2"}, artists={"a2"}, genres={"g2"}),
        _profile(3, tracks={"t3"}, artists={"a3"}, genres={"g3"}),
        _profile(4, tracks={"t4"}, artists={"a4"}, genres={"g4"}),
    ]
    r = cluster_taste_profiles(profiles)
    assert r.status == "insufficient_evidence"
    assert r.clusters == ()


# ---------------------------------------------------------------------------
# CT-PB22-03 — determinismo sob permutações
# ---------------------------------------------------------------------------

def test_determinismo_sob_todas_as_permutacoes():
    base = cluster_taste_profiles(_two_groups())
    ref = (
        base.status,
        tuple((c.id, c.member_ids) for c in base.clusters),
        tuple((s.user_a, s.user_b, s.score) for s in base.similarities),
    )
    for perm in permutations(_two_groups()):
        r = cluster_taste_profiles(list(perm))
        got = (
            r.status,
            tuple((c.id, c.member_ids) for c in r.clusters),
            tuple((s.user_a, s.user_b, s.score) for s in r.similarities),
        )
        assert got == ref, "resultado depende da ordem de entrada"


# ---------------------------------------------------------------------------
# CT-PB22-04 — grupo homogêneo → single_group
# ---------------------------------------------------------------------------

def test_grupo_homogeneo_e_single_group():
    profiles = [
        _profile(1, tracks={"x"}, artists={"a"}, genres={"pop"}),
        _profile(2, tracks={"y"}, artists={"a"}, genres={"pop"}),
        _profile(3, tracks={"z"}, artists={"a"}, genres={"pop"}),
    ]
    r = cluster_taste_profiles(profiles)
    assert r.status == "single_group"
    assert len(r.clusters) == 1
    assert r.clusters[0].member_ids == (1, 2, 3)


# ---------------------------------------------------------------------------
# CT-PB22-05 + mutação — disponível ao motor sem alterar o ranking
# ---------------------------------------------------------------------------

def _candidate(track_id, source_users):
    return CandidateTrack(
        track_id,
        {
            "id": track_id, "name": track_id,
            "artists": [{"id": f"art-{track_id}", "name": track_id}],
            "genres": ["pop"], "popularity": 60,
            "album": {"name": "Al", "release_date": "2022"},
        },
        set(source_users),
    )


def test_candidatas_recebem_cluster_ids_dos_membros():
    profiles = _two_groups()
    clusters = cluster_taste_profiles(profiles)
    # candidata originada pelo usuário 1 (cluster dos pop) e 3 (cluster dos rock)
    cand = _candidate("c1", {1, 3})
    ctx = ContextCriteria(occasion="", mood="", energy="media")
    _rank_candidates([cand], profiles, "Democrático", ctx, None, clusters)
    assert set(cand.source_cluster_ids) == {"cluster-01", "cluster-02"}


def test_clusters_nao_alteram_o_ranking():
    """Mutação: o ranking com e sem clusters deve ser idêntico (score inalterado)."""
    profiles = _two_groups()
    clusters = cluster_taste_profiles(profiles)
    pool = [_candidate(f"c{i}", {1, 3}) for i in range(8)]
    ctx = ContextCriteria(occasion="", mood="", energy="media")

    without = [c.id for c in _rank_candidates([_candidate(f"c{i}", {1, 3}) for i in range(8)],
                                              profiles, "Democrático", ctx, None, None)]
    with_cl = [c.id for c in _rank_candidates(pool, profiles, "Democrático", ctx, None, clusters)]
    assert without == with_cl, "clusters não podem alterar o ranking no PB-22"


# ---------------------------------------------------------------------------
# CT-PB22-06 — robustez
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad", [-0.01, 1.01, 2.0, -1.0])
def test_limiar_fora_de_0_1_rejeitado(bad):
    with pytest.raises(ValueError):
        cluster_taste_profiles(_two_groups(), similarity_threshold=bad)


def test_user_id_duplicado_rejeitado():
    profiles = _two_groups()
    profiles[1] = _profile(1, tracks={"dup"}, artists={"a-pop"}, genres={"pop"})  # user_id 1 repetido
    with pytest.raises(ValueError):
        cluster_taste_profiles(profiles)
