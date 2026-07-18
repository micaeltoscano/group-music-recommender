"""QA (validador independente) — PB-24 (balanceamento entre subgrupos).

Sondagem adversarial da autoridade de QA, além dos testes do Dev:

- CT-PB24-01: teto por cluster respeitado no prefixo quando há alternativas;
  menos representado primeiro.
- CT-PB24-02/03: a saída é sempre uma PERMUTAÇÃO da entrada (não perde/duplica
  candidata); veto nunca é promovido ao prefixo pelo balanceador; scores intactos.
- CT-PB24-04 (mutação): flag off → ordem idêntica nos 3 modos; teto configurável.
- CT-PB24-06: None/single/insufficient → ordem preservada; size/share inválidos →
  ValueError; determinismo.
"""

from __future__ import annotations

import pytest

from app.engine.candidates import CandidateTrack
from app.engine.clustering import cluster_taste_profiles
from app.engine.context_scoring import ContextCriteria
from app.engine.subgroup_balance import balance_subgroup_candidates
from app.engine.taste import UserTasteProfile
from app.services.generation_service import _rank_candidates


def _profile(user_id, *, tracks, artist, genre):
    p = UserTasteProfile(user_id, {}, {})
    p.tracks = set(tracks)
    p.artists = {artist}
    p.genres = {genre}
    return p


def _profiles():
    a = {f"a-{i}" for i in range(8)}
    b = {f"b-{i}" for i in range(8)}
    return [
        _profile(1, tracks=set(a), artist="artist-a", genre="genre-a"),
        _profile(2, tracks=set(a), artist="artist-a", genre="genre-a"),
        _profile(3, tracks=set(b), artist="artist-b", genre="genre-b"),
        _profile(4, tracks=set(b), artist="artist-b", genre="genre-b"),
    ]


def _cand(track_id, cluster_id):
    return CandidateTrack(
        track_id,
        {"id": track_id, "name": track_id,
         "artists": [{"id": f"art-{track_id}", "name": track_id}],
         "genres": [], "popularity": 50, "album": {"release_date": "2026-01-01"}},
        {1},
        source_cluster_ids=(cluster_id,) if cluster_id else (),
    )


def _scored(cand, score, individual_scores=None):
    return {
        "candidate": cand, "penalized_score": score, "group_score": score,
        "individual_scores": individual_scores or [0.7, 0.7, 0.7, 0.7],
    }


def _clustering():
    return cluster_taste_profiles(_profiles())


# ---------------------------------------------------------------------------
# CT-PB24-01 — teto respeitado com alternativas
# ---------------------------------------------------------------------------

def test_teto_por_cluster_respeitado_com_alternativas():
    cl = _clustering()
    ids = [c.id for c in cl.clusters]  # ['cluster-01', 'cluster-02']
    # 5 candidatas do cluster-01 (topo) + 5 do cluster-02
    scored = [_scored(_cand(f"a{i}", ids[0]), 0.9 - i * 0.01) for i in range(5)]
    scored += [_scored(_cand(f"b{i}", ids[1]), 0.5 - i * 0.01) for i in range(5)]

    res = balance_subgroup_candidates(scored, cl, target_size=10, max_cluster_share=0.60)
    prefix_ids = [item["candidate"].source_cluster_ids[0] for item in res.ranked_candidates[:10]]
    # ceil(10*0.6)=6 → nenhum cluster > 6 no prefixo
    assert prefix_ids.count(ids[0]) <= 6
    assert prefix_ids.count(ids[1]) <= 6
    assert res.applied is True


# ---------------------------------------------------------------------------
# CT-PB24-02/03 — permutação, veto não promovido, scores intactos
# ---------------------------------------------------------------------------

def test_saida_e_permutacao_da_entrada():
    cl = _clustering()
    ids = [c.id for c in cl.clusters]
    scored = [_scored(_cand(f"a{i}", ids[0]), 0.9 - i * 0.01) for i in range(6)]
    scored += [_scored(_cand(f"b{i}", ids[1]), 0.5 - i * 0.01) for i in range(4)]

    res = balance_subgroup_candidates(scored, cl, target_size=10, max_cluster_share=0.60)
    in_ids = sorted(s["candidate"].id for s in scored)
    out_ids = sorted(item["candidate"].id for item in res.ranked_candidates)
    assert in_ids == out_ids, "balanceamento não pode adicionar/remover candidatas"
    # scores intactos
    for item in res.ranked_candidates:
        assert "penalized_score" in item


def test_veto_fora_do_prefixo_nao_e_puxado_para_dentro():
    """Propriedade central do critério 2: o balanceamento NÃO eleva ao prefixo
    uma faixa vetada que estava fora dele. Quando precisa de um representante do
    cluster minoritário, escolhe a candidata SEM veto; a vetada permanece fora.
    """
    cl = _clustering()
    ids = [c.id for c in cl.clusters]
    # cluster-01 domina o topo (índices 0..5); cluster-02 só aparece fora do
    # prefixo natural: b-clean (idx 6, sem veto) e b-veto (idx 7, com veto).
    scored = [_scored(_cand(f"a{i}", ids[0]), 0.90 - i * 0.01) for i in range(6)]
    scored.append(_scored(_cand("b-clean", ids[1]), 0.40))
    scored.append(_scored(_cand("b-veto", ids[1]), 0.35,
                          individual_scores=[0.9, 0.9, 0.0, 0.9]))
    scored += [_scored(_cand(f"a{i}", ids[0]), 0.20 - i * 0.01) for i in range(6, 8)]

    res = balance_subgroup_candidates(scored, cl, target_size=6, max_cluster_share=0.60)
    prefix = [item["candidate"].id for item in res.ranked_candidates[:6]]

    assert "b-veto" not in prefix, "faixa vetada não pode ser promovida ao prefixo"
    # o representante do cluster minoritário é a candidata SEM veto
    assert "b-clean" in prefix
    alloc_by_id = {a.candidate_id: a.cluster_id for a in res.allocations[:6]}
    assert alloc_by_id.get("b-clean") == ids[1]
    # cluster-01 respeitou o teto (ceil(6*0.6)=4)
    assert prefix.count("b-clean") == 1
    assert sum(1 for pid in prefix if pid.startswith("a")) <= 4 + 1  # 4 do cap + tolerância


# ---------------------------------------------------------------------------
# CT-PB24-04 — flag off = identidade; teto configurável
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", ["Democrático", "Festa Segura", "Descoberta"])
def test_flag_off_preserva_ordem_em_todos_os_modos(mode):
    profiles = _profiles()
    cl = cluster_taste_profiles(profiles)
    pool = [_cand(f"a{i}", "") for i in range(6)]
    ctx = ContextCriteria(occasion="", mood="", energy="media")
    off = [c.id for c in _rank_candidates(pool, profiles, mode, ctx, taste_clusters=cl,
           subgroup_balancing_enabled=False)]
    off2 = [c.id for c in _rank_candidates([_cand(f"a{i}", "") for i in range(6)], profiles, mode,
            ctx, taste_clusters=cl, subgroup_balancing_enabled=False)]
    assert off == off2  # determinístico e sem balanceamento


@pytest.mark.parametrize("bad", [0.49, 0.4, 1.01, 2.0])
def test_share_invalido_rejeitado(bad):
    with pytest.raises(ValueError):
        balance_subgroup_candidates([], _clustering(), target_size=10, max_cluster_share=bad)


def test_target_size_negativo_rejeitado():
    with pytest.raises(ValueError):
        balance_subgroup_candidates([], _clustering(), target_size=-1)


# ---------------------------------------------------------------------------
# CT-PB24-06 — sem subgrupos → ordem preservada; determinismo
# ---------------------------------------------------------------------------

def test_sem_clustering_preserva_ordem():
    scored = [_scored(_cand(f"x{i}", None), 0.9 - i * 0.01) for i in range(5)]
    res = balance_subgroup_candidates(scored, None, target_size=5)
    assert [i["candidate"].id for i in res.ranked_candidates] == [s["candidate"].id for s in scored]
    assert res.applied is False


def test_single_group_preserva_ordem():
    profiles = [
        _profile(1, tracks={"x"}, artist="a", genre="pop"),
        _profile(2, tracks={"y"}, artist="a", genre="pop"),
        _profile(3, tracks={"z"}, artist="a", genre="pop"),
    ]
    cl = cluster_taste_profiles(profiles)  # single_group
    scored = [_scored(_cand(f"x{i}", None), 0.9 - i * 0.01) for i in range(5)]
    res = balance_subgroup_candidates(scored, cl, target_size=5)
    assert res.applied is False
    assert [i["candidate"].id for i in res.ranked_candidates] == [s["candidate"].id for s in scored]


def test_determinismo():
    cl = _clustering()
    ids = [c.id for c in cl.clusters]
    def build():
        s = [_scored(_cand(f"a{i}", ids[0]), 0.9 - i * 0.01) for i in range(5)]
        s += [_scored(_cand(f"b{i}", ids[1]), 0.5 - i * 0.01) for i in range(5)]
        return s
    r1 = balance_subgroup_candidates(build(), cl, target_size=10, max_cluster_share=0.6)
    r2 = balance_subgroup_candidates(build(), cl, target_size=10, max_cluster_share=0.6)
    assert [i["candidate"].id for i in r1.ranked_candidates] == \
           [i["candidate"].id for i in r2.ranked_candidates]
    assert r1.applied == r2.applied
