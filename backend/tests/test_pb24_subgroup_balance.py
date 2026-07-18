"""Testes técnicos do PB-24 — balanceamento entre subgrupos."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.db.base import Base
from app.db.models import MusicSession, MusicSessionMember, PlaylistRun, PlaylistRunTrack, User
from app.engine.candidates import CandidateTrack
from app.engine.clustering import cluster_taste_profiles
from app.engine.context_scoring import ContextCriteria
from app.engine.subgroup_balance import balance_subgroup_candidates
from app.engine.taste import UserTasteProfile
from app.services.generation_service import _rank_candidates
from app.services.result_service import (
    SUBGROUP_BALANCE_EXPLANATION,
    build_room_result,
    finalize_run_metrics,
)


def _profile(
    user_id: int,
    *,
    tracks: set[str],
    artist: str,
    genre: str,
) -> UserTasteProfile:
    profile = UserTasteProfile(user_id, {}, {})
    profile.tracks = tracks
    profile.artists = {artist}
    profile.genres = {genre}
    return profile


def _profiles() -> list[UserTasteProfile]:
    a_tracks = {f"a-{index}" for index in range(8)}
    b_tracks = {f"b-{index}" for index in range(8)}
    return [
        _profile(1, tracks=set(a_tracks), artist="artist-a", genre="genre-a"),
        _profile(2, tracks=set(a_tracks), artist="artist-a", genre="genre-a"),
        _profile(3, tracks=set(b_tracks), artist="artist-b", genre="genre-b"),
        _profile(4, tracks=set(b_tracks), artist="artist-b", genre="genre-b"),
    ]


def _candidate(track_id: str, source_user_id: int, cluster_id: str) -> CandidateTrack:
    return CandidateTrack(
        track_id=track_id,
        raw_data={
            "id": track_id,
            "name": track_id,
            "artists": [{"id": f"artist-{track_id}", "name": f"Artist {track_id}"}],
            "genres": [],
            "popularity": 50,
            "album": {"release_date": "2026-01-01"},
        },
        source_user_ids={source_user_id},
        source_cluster_ids=(cluster_id,),
    )


def _scored(candidate: CandidateTrack, score: float, individual_scores=None) -> dict:
    return {
        "candidate": candidate,
        "penalized_score": score,
        "group_score": score,
        "individual_scores": individual_scores or [0.7, 0.7, 0.7, 0.7],
    }


def _ranked_pool(a_count: int, b_count: int) -> tuple[list[dict], object]:
    profiles = _profiles()
    clustering = cluster_taste_profiles(profiles)
    scored = [
        _scored(_candidate(f"a-{index}", 1, "cluster-01"), 1.0 - index * 0.01)
        for index in range(a_count)
    ] + [
        _scored(_candidate(f"b-{index}", 3, "cluster-02"), 0.7 - index * 0.01)
        for index in range(b_count)
    ]
    return scored, clustering


def test_ct_pb24_01_limita_predominancia_e_intercala_quando_ha_alternativas():
    scored, clustering = _ranked_pool(8, 8)

    result = balance_subgroup_candidates(
        scored,
        clustering,
        target_size=10,
        max_cluster_share=0.60,
    )

    prefix_allocations = [allocation.cluster_id for allocation in result.allocations]
    counts = Counter(prefix_allocations)
    assert result.applied is True
    assert result.max_per_cluster == 6
    assert counts == {"cluster-01": 5, "cluster-02": 5}
    assert prefix_allocations[:6] == [
        "cluster-01",
        "cluster-02",
        "cluster-01",
        "cluster-02",
        "cluster-01",
        "cluster-02",
    ]


def test_ct_pb24_02_melhor_esforco_preserva_tamanho_quando_faltam_alternativas():
    scored, clustering = _ranked_pool(8, 2)

    result = balance_subgroup_candidates(
        scored,
        clustering,
        target_size=10,
        max_cluster_share=0.60,
    )

    assert len(result.ranked_candidates) == len(scored)
    assert {id(item) for item in result.ranked_candidates} == {id(item) for item in scored}
    assert dict(result.cluster_counts) == {"cluster-01": 8, "cluster-02": 2}
    assert dict(result.cluster_counts)["cluster-01"] > result.max_per_cluster


def test_ct_pb24_03_nao_promove_veto_nem_altera_scores_ou_conjunto():
    scored, clustering = _ranked_pool(5, 5)
    vetoed = _scored(
        _candidate("b-veto", 3, "cluster-02"),
        0.99,
        individual_scores=[0.9, 0.9, 0.0, 0.9],
    )
    ranked = [vetoed, *scored]
    original_scores = {id(item): item["penalized_score"] for item in ranked}

    result = balance_subgroup_candidates(ranked, clustering, target_size=6)
    prefix = result.ranked_candidates[:6]

    assert vetoed not in prefix
    assert {id(item) for item in result.ranked_candidates} == {id(item) for item in ranked}
    assert all(item["penalized_score"] == original_scores[id(item)] for item in ranked)


@pytest.mark.parametrize("mode", ["Democrático", "Festa Segura", "Descoberta"])
def test_ct_pb24_04_flag_desligada_preserva_modos(mode, monkeypatch):
    assert Settings.model_fields["subgroup_balancing_enabled"].default is False
    assert Settings.model_fields["subgroup_max_share"].default == pytest.approx(0.60)
    profiles = _profiles()
    clustering = cluster_taste_profiles(profiles)
    context = ContextCriteria(occasion="", mood="", energy="")

    def _must_not_run(*args, **kwargs):
        raise AssertionError("balanceamento não deve executar com a flag desligada")

    monkeypatch.setattr(
        "app.services.generation_service.balance_subgroup_candidates",
        _must_not_run,
    )
    candidates = [
        *[_candidate(f"a-{index}", 1, "cluster-01") for index in range(8)],
        *[_candidate(f"b-{index}", 3, "cluster-02") for index in range(8)],
    ]
    expected = [
        candidate.id
        for candidate in _rank_candidates(
            candidates,
            profiles,
            mode,
            context,
            taste_clusters=clustering,
        )
    ]
    fresh = [
        *[_candidate(f"a-{index}", 1, "cluster-01") for index in range(8)],
        *[_candidate(f"b-{index}", 3, "cluster-02") for index in range(8)],
    ]
    actual = _rank_candidates(
        fresh,
        profiles,
        mode,
        context,
        taste_clusters=clustering,
        subgroup_balancing_enabled=False,
    )

    assert [candidate.id for candidate in actual] == expected
    assert all(candidate.subgroup_balancing_applied is False for candidate in actual)


def test_ct_pb24_04_pipeline_ligado_aplica_limite_configurado():
    profiles = _profiles()
    clustering = cluster_taste_profiles(profiles)
    candidates = [
        *[_candidate(f"a-{index}", 1, "cluster-01") for index in range(8)],
        *[_candidate(f"b-{index}", 3, "cluster-02") for index in range(8)],
    ]

    ranked = _rank_candidates(
        candidates,
        profiles,
        "Democrático",
        ContextCriteria(occasion="", mood="", energy=""),
        taste_clusters=clustering,
        subgroup_balancing_enabled=True,
        subgroup_max_share=0.60,
    )

    prefix_clusters = [candidate.balanced_cluster_id for candidate in ranked]
    assert Counter(prefix_clusters) == {"cluster-01": 8, "cluster-02": 8}
    assert all(
        current != following
        for current, following in zip(prefix_clusters, prefix_clusters[1:])
    )
    assert all(candidate.subgroup_balancing_applied is True for candidate in ranked)


@pytest.fixture()
def result_session_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pb24.sqlite3'}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(engine)
    try:
        yield factory
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.mark.parametrize("applied", [False, True])
def test_ct_pb24_05_persiste_e_exibe_explicacao_somente_quando_aplicado(
    result_session_factory,
    applied,
):
    db = result_session_factory()
    try:
        user = User(spotify_id=f"pb24-{applied}", display_name="Membro")
        db.add(user)
        db.flush()
        room = MusicSession(
            code=f"PB24-{int(applied)}",
            host_user_id=user.id,
            status="open",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db.add(room)
        db.flush()
        db.add(MusicSessionMember(session_id=room.id, user_id=user.id, role="host"))
        run = PlaylistRun(
            session_id=room.id,
            status="completed",
            subgroup_balancing_applied=applied,
        )
        db.add(run)
        db.flush()
        db.add(
            PlaylistRunTrack(
                run_id=run.id,
                candidate_id="selected",
                spotify_id="spotify-selected",
                spotify_uri="spotify:track:selected",
                name="Selected",
                artist="Artist",
                status="matched",
                source=json.dumps([user.id]),
                selection_rank=1,
            )
        )
        db.commit()

        finalize_run_metrics(db, run)
        db.commit()
        result = build_room_result(db, room, run)

        assert run.subgroup_balancing_applied is applied
        assert (SUBGROUP_BALANCE_EXPLANATION in result.why_items) is applied
        assert result.why_items.count(SUBGROUP_BALANCE_EXPLANATION) == int(applied)
    finally:
        db.close()


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"target_size": -1}, "target_size"),
        ({"target_size": 2, "max_cluster_share": 0.49}, "max_cluster_share"),
        ({"target_size": 2, "max_cluster_share": 1.01}, "max_cluster_share"),
        ({"target_size": 2, "veto_threshold": -0.01}, "veto_threshold"),
    ],
)
def test_ct_pb24_06_rejeita_configuracao_invalida(kwargs, message):
    scored, clustering = _ranked_pool(2, 2)
    with pytest.raises(ValueError, match=message):
        balance_subgroup_candidates(scored, clustering, **kwargs)


def test_ct_pb24_06_sem_subgrupos_preserva_ordem_e_mesma_entrada_e_deterministica():
    scored, _ = _ranked_pool(4, 4)
    profiles = _profiles()
    insufficient = cluster_taste_profiles(profiles[:2])

    without_clusters = balance_subgroup_candidates(scored, None, target_size=6)
    without_evidence = balance_subgroup_candidates(scored, insufficient, target_size=6)
    first = balance_subgroup_candidates(
        scored,
        cluster_taste_profiles(profiles),
        target_size=6,
    )
    second = balance_subgroup_candidates(
        scored,
        cluster_taste_profiles(profiles),
        target_size=6,
    )

    assert list(without_clusters.ranked_candidates) == scored
    assert list(without_evidence.ranked_candidates) == scored
    assert without_clusters.applied is False
    assert without_evidence.applied is False
    assert first == second
