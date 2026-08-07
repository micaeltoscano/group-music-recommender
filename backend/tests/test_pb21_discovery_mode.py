"""Testes do Dev para PB-21 — Modo Descoberta."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.auth import SESSION_COOKIE_NAME
from app.config import settings
from app.db.base import Base
from app.db.models import (
    AppSession,
    MusicSession,
    MusicSessionMember,
    PlaylistRun,
    PlaylistRunTrack,
    User,
)
from app.db.session import get_db
from app.engine.candidates import CandidateTrack
from app.engine.context_scoring import ContextCriteria
from app.engine.fairness import elevate_least_represented, evaluate_candidate_fairness
from app.engine.taste import UserTasteProfile
from app.engine.weights import CONSENSUS_MODES
from app.main import app
from app.services.generation_service import _rank_candidates
from app.services.result_service import (
    DISCOVERY_EXPLANATION,
    build_room_result,
    finalize_run_metrics,
)


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pb21.sqlite3'}",
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


@pytest.fixture()
def client(session_factory):
    def _override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _seed_host(session_factory) -> dict[str, object]:
    db = session_factory()
    try:
        host = User(spotify_id="pb21-host", display_name="Host Descoberta")
        db.add(host)
        db.flush()
        raw_token = "pb21-host-session"
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        db.add(
            AppSession(
                user_id=host.id,
                session_token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
                expires_at=expires_at,
            )
        )
        room = MusicSession(
            code="DISC-0021",
            host_user_id=host.id,
            status="open",
            expires_at=expires_at,
        )
        db.add(room)
        db.flush()
        db.add(MusicSessionMember(session_id=room.id, user_id=host.id, role="host"))
        db.commit()
        return {"host_id": host.id, "room_id": room.id, "token": raw_token}
    finally:
        db.close()


def _act_as(client: TestClient, token: str) -> None:
    client.cookies.set(SESSION_COOKIE_NAME, token)


def test_ct_pb21_01_flag_desligada_oculta_e_rejeita_modo(client, session_factory, monkeypatch):
    seeded = _seed_host(session_factory)
    _act_as(client, seeded["token"])
    monkeypatch.setattr(settings, "discovery_mode_enabled", False)

    available = client.get("/rooms/consensus-modes")
    response = client.put("/rooms/DISC-0021/mode", json={"mode": "Descoberta"})

    assert available.status_code == 200
    assert available.json()["modes"] == ["Democrático", "Festa Segura"]
    assert response.status_code == 422
    assert "desabilitado" in response.json()["detail"]
    db = session_factory()
    try:
        assert db.get(MusicSession, seeded["room_id"]).mode is None
    finally:
        db.close()


def test_ct_pb21_02_flag_ligada_anuncia_e_persiste_modo(client, session_factory, monkeypatch):
    seeded = _seed_host(session_factory)
    _act_as(client, seeded["token"])
    monkeypatch.setattr(settings, "discovery_mode_enabled", True)

    available = client.get("/rooms/consensus-modes")
    response = client.put("/rooms/DISC-0021/mode", json={"mode": "Descoberta"})

    assert available.status_code == 200
    assert available.json()["modes"] == ["Democrático", "Festa Segura", "Descoberta"]
    assert response.status_code == 200
    assert response.json()["mode"] == "Descoberta"
    db = session_factory()
    try:
        assert db.get(MusicSession, seeded["room_id"]).mode == "Descoberta"
    finally:
        db.close()


def _candidate(track_id: str, artist_id: str, genre: str, release_date: str) -> CandidateTrack:
    return CandidateTrack(
        track_id=track_id,
        raw_data={
            "id": track_id,
            "name": track_id,
            "artists": [{"id": artist_id, "name": artist_id}],
            "genres": [genre],
            "popularity": 50,
            "album": {"release_date": release_date},
        },
        source_user_ids={1},
    )


def _known_profile() -> UserTasteProfile:
    profile = UserTasteProfile(1, {}, {})
    profile.artists = {"known-artist"}
    profile.genres = {"pop"}
    return profile


def test_ct_pb21_03_novidade_e_diversidade_superiores_e_mudam_ranking():
    discovery = CONSENSUS_MODES["discovery"]
    democratic = CONSENSUS_MODES["democratic"]
    assert discovery["individual"]["novelty"] > democratic["individual"]["novelty"]
    assert discovery["group"]["diversity"] > democratic["group"]["diversity"]
    assert sum(discovery["individual"].values()) == pytest.approx(1.0)
    assert sum(discovery["group"].values()) == pytest.approx(1.0)

    old_familiar = _candidate("old", "known-artist", "pop", "1995-01-01")
    new_diverse = _candidate("new", "new-artist", "experimental", "2026-06-01")
    context = ContextCriteria(occasion="", mood="", energy="")
    profile = _known_profile()

    democratic_order = _rank_candidates(
        [old_familiar, new_diverse], [profile], "Democrático", context
    )
    discovery_order = _rank_candidates(
        [old_familiar, new_diverse], [profile], "Descoberta", context
    )

    assert democratic_order[0].id == "old"
    assert discovery_order[0].id == "new"


def test_ct_pb21_04_veto_e_representacao_minima_continuam_ativos(monkeypatch):
    discovery = CONSENSUS_MODES["discovery"]
    vetoed = evaluate_candidate_fairness(
        {
            "group_score": 0.8,
            "average_score": 0.7,
            "min_user_score": 0.0,
            "coverage": 0.8,
            "individual_scores": [0.9, 0.0],
        },
        discovery,
    )
    assert vetoed["penalized_score"] == pytest.approx(0.2)

    selected = elevate_least_represented(
        [
            {"id": "a", "individual_scores": [1.0, 0.0], "penalized_score": 0.9},
            {"id": "b", "individual_scores": [0.9, 0.1], "penalized_score": 0.8},
            {"id": "representa-b", "individual_scores": [0.6, 1.0], "penalized_score": 0.71},
        ],
        target_size=2,
        num_users=2,
    )
    assert "representa-b" in {item["id"] for item in selected}

    called: dict[str, int] = {}

    def _record(scored, target_size, num_users):
        called.update(target_size=target_size, num_users=num_users)
        return scored

    monkeypatch.setattr("app.services.generation_service.elevate_least_represented", _record)
    _rank_candidates(
        [_candidate("new", "new-artist", "new-genre", "2026")],
        [_known_profile()],
        "Descoberta",
        ContextCriteria(occasion="", mood="", energy=""),
    )
    assert called == {"target_size": 1, "num_users": 1}


def test_ct_pb21_05_resultado_persiste_e_exibe_explicacao(session_factory):
    seeded = _seed_host(session_factory)
    db = session_factory()
    try:
        room = db.get(MusicSession, seeded["room_id"])
        room.mode = "Descoberta"
        run = PlaylistRun(session_id=room.id, status="completed")
        db.add(run)
        db.flush()
        db.add(
            PlaylistRunTrack(
                run_id=run.id,
                candidate_id="candidate-discovery",
                spotify_id="spotify-discovery",
                spotify_uri="spotify:track:discovery",
                name="Faixa nova",
                artist="Artista novo",
                source=json.dumps([seeded["host_id"]]),
                status="matched",
            )
        )
        db.flush()

        finalize_run_metrics(db, run)
        persisted = json.loads(run.explanation_json)
        result = build_room_result(db, room, run)

        assert DISCOVERY_EXPLANATION in persisted["why_items"]
        assert DISCOVERY_EXPLANATION in result.why_items
        assert "diversidade" in DISCOVERY_EXPLANATION
        assert "rejeição e justiça" in DISCOVERY_EXPLANATION
    finally:
        db.close()


def test_ct_pb21_06_frontend_consome_lista_do_servidor_e_descreve_modo():
    root = Path(__file__).resolve().parents[2]
    room_source = (root / "frontend" / "src" / "Room.jsx").read_text(encoding="utf-8")
    api_source = (root / "frontend" / "src" / "apiClient.js").read_text(encoding="utf-8")

    assert "getConsensusModes" in room_source
    assert "availableModes.map" in room_source
    assert "mais novidade e diversidade, preservando justiça" in room_source
    assert "'/rooms/consensus-modes'" in api_source
