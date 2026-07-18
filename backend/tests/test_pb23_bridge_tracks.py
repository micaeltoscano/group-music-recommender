"""Testes técnicos do PB-23 — identificação de músicas-ponte."""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timedelta, timezone
from itertools import permutations
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings
from app.db.base import Base
from app.db.models import MusicSession, MusicSessionMember, PlaylistRun, PlaylistRunTrack, User
from app.engine.bridge import evaluate_bridge_candidate
from app.engine.candidates import CandidateTrack
from app.engine.clustering import cluster_taste_profiles
from app.engine.context_scoring import ContextCriteria
from app.engine.taste import UserTasteProfile
from app.engine.weights import CONSENSUS_MODES
from app.services.generation_service import _rank_candidates, resolve_candidates
from app.services.result_service import BRIDGE_EXPLANATION, build_room_result


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
    return [
        _profile(1, tracks={"bridge", "pop-1"}, artist="artist-pop", genre="pop"),
        _profile(2, tracks={"bridge", "pop-2"}, artist="artist-pop", genre="pop"),
        _profile(3, tracks={"bridge", "rock-1"}, artist="artist-rock", genre="rock"),
        _profile(4, tracks={"bridge", "rock-2"}, artist="artist-rock", genre="rock"),
    ]


def _candidate(track_id: str, *, source_user_ids: set[int] | None = None) -> CandidateTrack:
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
        source_user_ids=source_user_ids or {1},
    )


def test_ct_pb23_01_identifica_boa_aceitacao_em_multiplos_subgrupos():
    profiles = _profiles()
    clustering = cluster_taste_profiles(profiles)

    evaluation = evaluate_bridge_candidate(
        _candidate("bridge", source_user_ids={1, 3}),
        profiles,
        clustering,
        CONSENSUS_MODES["democratic"]["individual"],
    )

    assert clustering.status == "clustered"
    assert evaluation.is_bridge is True
    assert evaluation.bridge_score == pytest.approx(0.4)
    assert evaluation.accepted_cluster_ids == ("cluster-01", "cluster-02")
    assert tuple(item.score for item in evaluation.cluster_acceptance) == (0.4, 0.4)


def test_ct_pb23_02_afinidade_com_um_unico_subgrupo_nao_forma_ponte():
    profiles = _profiles()
    profiles[0].tracks.add("pop-only")
    profiles[1].tracks.add("pop-only")

    evaluation = evaluate_bridge_candidate(
        _candidate("pop-only"),
        profiles,
        cluster_taste_profiles(profiles),
        CONSENSUS_MODES["democratic"]["individual"],
    )

    assert evaluation.is_bridge is False
    assert evaluation.bridge_score == 0.0
    assert evaluation.accepted_cluster_ids == ()
    assert evaluation.cluster_acceptance[0].score >= 0.25
    assert evaluation.cluster_acceptance[1].score < 0.25

    unrelated = evaluate_bridge_candidate(
        _candidate("unrelated-new-track"),
        profiles,
        cluster_taste_profiles(profiles),
        CONSENSUS_MODES["discovery"]["individual"],
    )
    assert unrelated.is_bridge is False
    assert all(item.score == 0.0 for item in unrelated.cluster_acceptance)


def test_ct_pb23_03_ranking_marca_ponte_sem_promover_sua_posicao():
    profiles = _profiles()
    clustering = cluster_taste_profiles(profiles)
    bridge = _candidate("bridge", source_user_ids={1, 3})
    local = _candidate("pop-1", source_user_ids={1})
    context = ContextCriteria(occasion="", mood="", energy="")

    enabled = _rank_candidates(
        [local, bridge],
        profiles,
        "Democrático",
        context,
        taste_clusters=clustering,
        bridge_tracks_enabled=True,
    )
    disabled_order = [
        candidate.id
        for candidate in _rank_candidates(
            [_candidate("pop-1"), _candidate("bridge")],
            profiles,
            "Democrático",
            context,
            taste_clusters=clustering,
            bridge_tracks_enabled=False,
        )
    ]

    assert [candidate.id for candidate in enabled] == disabled_order
    assert bridge.is_bridge is True
    assert bridge.bridge_score == pytest.approx(0.4)
    assert bridge.bridge_cluster_ids == ("cluster-01", "cluster-02")
    assert local.is_bridge is False


@pytest.mark.parametrize("mode", ["Democrático", "Festa Segura", "Descoberta"])
def test_ct_pb23_04_flag_desligada_preserva_todos_os_modos(mode, monkeypatch):
    assert Settings.model_fields["bridge_tracks_enabled"].default is False
    profiles = _profiles()
    clustering = cluster_taste_profiles(profiles)
    context = ContextCriteria(occasion="", mood="", energy="")

    def _must_not_run(*args, **kwargs):
        raise AssertionError("avaliação de ponte não deve executar com a flag desligada")

    monkeypatch.setattr(
        "app.services.generation_service.evaluate_bridge_candidate",
        _must_not_run,
    )
    expected = [
        candidate.id
        for candidate in _rank_candidates(
            [_candidate("pop-1"), _candidate("bridge"), _candidate("rock-1")],
            profiles,
            mode,
            context,
        )
    ]
    candidates = [_candidate("pop-1"), _candidate("bridge"), _candidate("rock-1")]
    actual = _rank_candidates(
        candidates,
        profiles,
        mode,
        context,
        taste_clusters=clustering,
        bridge_tracks_enabled=False,
    )

    assert [candidate.id for candidate in actual] == expected
    assert all(candidate.is_bridge is False for candidate in candidates)
    assert all(candidate.bridge_score == 0.0 for candidate in candidates)


def test_ct_pb23_05_matching_persiste_marcacao_de_ponte():
    candidate = _candidate("bridge", source_user_ids={1, 3})
    candidate.is_bridge = True
    db = MagicMock(spec=Session)
    search_result = [
        {
            "id": "spotify-bridge",
            "uri": "spotify:track:bridge",
            "name": "bridge",
            "artists": [{"name": "Artist bridge"}],
            "is_playable": True,
        }
    ]

    with patch(
        "app.clients.spotify_client.search_track",
        new=AsyncMock(return_value=search_result),
    ):
        asyncio.run(resolve_candidates(db, uuid.uuid4(), [candidate], "fake-token"))

    persisted = db.add_all.call_args.args[0][0]
    assert persisted.status == "matched"
    assert persisted.is_bridge is True


@pytest.fixture()
def result_session_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pb23.sqlite3'}",
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


def test_ct_pb23_05_resultado_indica_faixa_ponte_sem_expor_clusters(result_session_factory):
    db = result_session_factory()
    try:
        users = [
            User(spotify_id=f"pb23-{index}", display_name=f"Membro {index}")
            for index in (1, 2)
        ]
        db.add_all(users)
        db.flush()
        room = MusicSession(
            code="PB23-BRIDGE",
            host_user_id=users[0].id,
            status="open",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db.add(room)
        db.flush()
        db.add_all(
            [
                MusicSessionMember(
                    session_id=room.id,
                    user_id=user.id,
                    role="host" if index == 0 else "member",
                )
                for index, user in enumerate(users)
            ]
        )
        run = PlaylistRun(session_id=room.id, status="completed")
        db.add(run)
        db.flush()
        db.add(
            PlaylistRunTrack(
                run_id=run.id,
                candidate_id="bridge",
                spotify_id="spotify-bridge",
                spotify_uri="spotify:track:bridge",
                name="Bridge Song",
                artist="Bridge Artist",
                status="matched",
                source=json.dumps([user.id for user in users]),
                is_bridge=True,
                selection_rank=1,
            )
        )
        db.commit()

        payload = build_room_result(db, room, run).model_dump()

        assert payload["tracks"][0]["is_bridge"] is True
        assert "Faixa-ponte" in payload["tracks"][0]["reason"]
        assert "cluster" not in payload["tracks"][0]["reason"].lower()
        assert BRIDGE_EXPLANATION in payload["why_items"]
    finally:
        db.close()


@pytest.mark.parametrize("threshold", [-0.01, 1.01])
def test_ct_pb23_06_rejeita_limite_invalido(threshold):
    profiles = _profiles()
    with pytest.raises(ValueError, match="entre 0 e 1"):
        evaluate_bridge_candidate(
            _candidate("bridge"),
            profiles,
            cluster_taste_profiles(profiles),
            CONSENSUS_MODES["democratic"]["individual"],
            min_cluster_acceptance=threshold,
        )


def test_ct_pb23_06_sem_subgrupos_nao_marca_e_resultado_e_deterministico():
    profiles = _profiles()
    candidate = _candidate("bridge")
    insufficient = cluster_taste_profiles(profiles[:2])
    weights = CONSENSUS_MODES["democratic"]["individual"]

    assert (
        evaluate_bridge_candidate(candidate, profiles[:2], insufficient, weights).is_bridge
        is False
    )

    homogeneous = [
        _profile(
            user_id,
            tracks={"bridge", "shared"},
            artist="shared-artist",
            genre="shared-genre",
        )
        for user_id in (1, 2, 3)
    ]
    single_group = cluster_taste_profiles(homogeneous)
    assert single_group.status == "single_group"
    assert (
        evaluate_bridge_candidate(candidate, homogeneous, single_group, weights).is_bridge
        is False
    )

    expected = evaluate_bridge_candidate(
        candidate,
        profiles,
        cluster_taste_profiles(profiles),
        weights,
    )
    for reordered in permutations(profiles):
        assert evaluate_bridge_candidate(
            candidate,
            reordered,
            cluster_taste_profiles(reordered),
            weights,
        ) == expected
