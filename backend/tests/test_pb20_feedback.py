"""Testes do Dev para PB-20 — feedback pós-playlist."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.auth import SESSION_COOKIE_NAME
from app.db.base import Base
from app.db.models import (
    AppSession,
    MemberTrackFeedback,
    MusicSession,
    MusicSessionMember,
    PlaylistFeedback,
    PlaylistRun,
    PlaylistRunTrack,
    User,
)
from app.db.session import get_db
from app.main import app
from app.services.result_service import build_room_result


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pb20.sqlite3'}",
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


def _hash(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def _seed(session_factory):
    db = session_factory()
    try:
        member = User(spotify_id="feedback-member", display_name="Luiza")
        second_member = User(spotify_id="feedback-member-2", display_name="Caio")
        outsider = User(spotify_id="feedback-outsider", display_name="Externo")
        db.add_all([member, second_member, outsider])
        db.flush()

        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        tokens = {
            "member": "feedback-member-session",
            "second_member": "feedback-second-member-session",
            "outsider": "feedback-outsider-session",
        }
        db.add_all(
            [
                AppSession(
                    user_id=user.id,
                    session_token_hash=_hash(tokens[key]),
                    expires_at=expires_at,
                )
                for key, user in (
                    ("member", member),
                    ("second_member", second_member),
                    ("outsider", outsider),
                )
            ]
        )

        room = MusicSession(
            code="FEED-2020",
            host_user_id=member.id,
            status="completed",
            expires_at=expires_at,
        )
        db.add(room)
        db.flush()
        db.add_all(
            [
                MusicSessionMember(session_id=room.id, user_id=member.id, role="host"),
                MusicSessionMember(
                    session_id=room.id, user_id=second_member.id, role="member"
                ),
            ]
        )

        run = PlaylistRun(session_id=room.id, status="completed")
        running_run = PlaylistRun(session_id=room.id, status="running")
        db.add_all([run, running_run])
        db.flush()
        db.add_all(
            [
                PlaylistRunTrack(
                    run_id=run.id,
                    candidate_id="candidate-1",
                    spotify_id="spotify-track-1",
                    spotify_uri="spotify:track:1",
                    name="Faixa Um",
                    artist="Artista Um",
                    status="matched",
                ),
                PlaylistRunTrack(
                    run_id=run.id,
                    candidate_id="candidate-discarded",
                    spotify_id="spotify-track-discarded",
                    name="Faixa descartada",
                    artist="Artista Dois",
                    status="discarded",
                ),
            ]
        )
        db.commit()
        return {
            "member_id": member.id,
            "second_member_id": second_member.id,
            "outsider_id": outsider.id,
            "run_id": run.id,
            "running_run_id": running_run.id,
            **tokens,
        }
    finally:
        db.close()


def _act_as(client: TestClient, token: str) -> None:
    client.cookies.set(SESSION_COOKIE_NAME, token)


def test_ct_pb20_01_registra_os_quatro_sinais_por_faixa(client, session_factory):
    seeded = _seed(session_factory)
    _act_as(client, seeded["member"])

    response = client.post(
        f"/playlist-runs/{seeded['run_id']}/tracks/spotify-track-1/feedback",
        json={
            "liked": True,
            "disliked": True,
            "more_like_this": True,
            "never_again": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["liked"] is True
    assert body["disliked"] is True
    assert body["more_like_this"] is True
    assert body["never_again"] is True
    assert "evoluções futuras" in body["future_use_notice"]

    db = session_factory()
    try:
        stored = db.query(MemberTrackFeedback).one()
        assert stored.spotify_track_id == "spotify-track-1"
        assert (stored.liked, stored.disliked, stored.more_like_this, stored.never_again) == (
            True,
            True,
            True,
            True,
        )
    finally:
        db.close()


def test_ct_pb20_02_registra_feedback_geral_e_valida_limites(client, session_factory):
    seeded = _seed(session_factory)
    _act_as(client, seeded["member"])

    response = client.post(
        f"/playlist-runs/{seeded['run_id']}/feedback",
        json={
            "representation_score": 4,
            "satisfaction_score": 5,
            "comments": "  O grupo ficou bem representado.  ",
        },
    )

    assert response.status_code == 200
    assert response.json()["representation_score"] == 4
    assert response.json()["satisfaction_score"] == 5

    db = session_factory()
    try:
        stored = db.query(PlaylistFeedback).one()
        assert stored.comments == "O grupo ficou bem representado."
    finally:
        db.close()

    invalid = client.post(
        f"/playlist-runs/{seeded['run_id']}/feedback",
        json={"representation_score": 6, "satisfaction_score": -1},
    )
    assert invalid.status_code == 422


def test_ct_pb20_03_associa_usuario_e_run_e_atualiza_sem_duplicar(client, session_factory):
    seeded = _seed(session_factory)
    _act_as(client, seeded["second_member"])

    track_url = f"/playlist-runs/{seeded['run_id']}/tracks/spotify-track-1/feedback"
    assert client.post(track_url, json={"liked": True}).status_code == 200
    assert client.post(track_url, json={"liked": False, "never_again": True}).status_code == 200

    overall_url = f"/playlist-runs/{seeded['run_id']}/feedback"
    assert client.post(
        overall_url,
        json={"representation_score": 1, "satisfaction_score": 2},
    ).status_code == 200
    assert client.post(
        overall_url,
        json={"representation_score": 3, "satisfaction_score": 4},
    ).status_code == 200

    db = session_factory()
    try:
        track_rows = db.query(MemberTrackFeedback).all()
        overall_rows = db.query(PlaylistFeedback).all()
        assert len(track_rows) == len(overall_rows) == 1
        assert track_rows[0].user_id == seeded["second_member_id"]
        assert track_rows[0].playlist_run_id == seeded["run_id"]
        assert track_rows[0].liked is False
        assert track_rows[0].never_again is True
        assert overall_rows[0].user_id == seeded["second_member_id"]
        assert overall_rows[0].playlist_run_id == seeded["run_id"]
        assert overall_rows[0].representation_score == 3
        assert overall_rows[0].satisfaction_score == 4
    finally:
        db.close()


def test_ct_pb20_04_nao_membro_recebe_403_e_nada_e_persistido(client, session_factory):
    seeded = _seed(session_factory)
    _act_as(client, seeded["outsider"])

    track_response = client.post(
        f"/playlist-runs/{seeded['run_id']}/tracks/spotify-track-1/feedback",
        json={"liked": True},
    )
    overall_response = client.post(
        f"/playlist-runs/{seeded['run_id']}/feedback",
        json={"representation_score": 5, "satisfaction_score": 5},
    )

    assert track_response.status_code == 403
    assert overall_response.status_code == 403
    db = session_factory()
    try:
        assert db.query(MemberTrackFeedback).count() == 0
        assert db.query(PlaylistFeedback).count() == 0
    finally:
        db.close()


def test_ct_pb20_05_interface_explica_uso_futuro_sem_ranking_atual():
    source = (
        Path(__file__).resolve().parents[2] / "frontend" / "src" / "Feedback.jsx"
    ).read_text(encoding="utf-8")

    assert "evoluções futuras" in source
    assert "não altera o ranking do MVP" in source
    assert all(label in source for label in ("CURTI", "NÃO CURTI", "MAIS ASSIM", "NUNCA MAIS"))


def test_feedback_rejeita_faixa_descartada_e_run_nao_concluido(client, session_factory):
    seeded = _seed(session_factory)
    _act_as(client, seeded["member"])

    discarded = client.post(
        f"/playlist-runs/{seeded['run_id']}/tracks/spotify-track-discarded/feedback",
        json={"disliked": True},
    )
    running = client.post(
        f"/playlist-runs/{seeded['running_run_id']}/feedback",
        json={"representation_score": 2, "satisfaction_score": 2},
    )

    assert discarded.status_code == 404
    assert running.status_code == 409


def test_feedback_exige_autenticacao(client, session_factory):
    seeded = _seed(session_factory)

    response = client.post(
        f"/playlist-runs/{seeded['run_id']}/feedback",
        json={"representation_score": 2, "satisfaction_score": 2},
    )
    assert response.status_code == 401


def test_resultado_expoe_identificadores_necessarios_para_o_feedback(session_factory):
    seeded = _seed(session_factory)
    db = session_factory()
    try:
        run = db.get(PlaylistRun, seeded["run_id"])
        room = db.get(MusicSession, run.session_id)
        result = build_room_result(db, room, run)

        assert result.run_id == seeded["run_id"]
        assert result.tracks[0].track_id == "spotify-track-1"
    finally:
        db.close()


def test_remocao_de_conta_apaga_feedback_pessoal_sem_apagar_o_de_terceiro(
    client, session_factory
):
    seeded = _seed(session_factory)
    for token in (seeded["member"], seeded["second_member"]):
        _act_as(client, token)
        assert client.post(
            f"/playlist-runs/{seeded['run_id']}/tracks/spotify-track-1/feedback",
            json={"liked": True},
        ).status_code == 200
        assert client.post(
            f"/playlist-runs/{seeded['run_id']}/feedback",
            json={"representation_score": 4, "satisfaction_score": 4},
        ).status_code == 200

    _act_as(client, seeded["member"])
    assert client.delete("/auth/me").status_code == 204

    db = session_factory()
    try:
        assert db.query(MemberTrackFeedback).count() == 1
        assert db.query(PlaylistFeedback).count() == 1
        assert db.query(MemberTrackFeedback).one().user_id == seeded["second_member_id"]
        assert db.query(PlaylistFeedback).one().user_id == seeded["second_member_id"]
    finally:
        db.close()
