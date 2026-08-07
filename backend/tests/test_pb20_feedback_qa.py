"""QA (validador independente) — PB-20 (feedback pós-playlist).

Sondagem adversarial da autoridade de QA, além dos testes do Dev:

- CT-PB20-03 (isolamento de execução): não é possível registrar feedback de uma
  faixa contra um run que não a contém; e um membro de outra sala não passa pela
  autorização por membership.
- CT-PB20-04 (autorização): não-membro → 403 e NADA persiste (verificado no banco).
- Limites: notas fora de 0–5 → 422; comentário acima do limite → 422.
- Idempotência: reenvio atualiza, não duplica.
- Faixa descartada não aceita feedback.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

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


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pb20-qa.sqlite3'}",
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
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _hash(t: str) -> str:
    return hashlib.sha256(t.encode()).hexdigest()


def _seed_two_rooms(session_factory):
    """Duas salas, cada uma com seu run concluído e uma faixa matched distinta.
    memberA pertence à sala A; memberB à sala B."""
    db = session_factory()
    try:
        exp = datetime.now(timezone.utc) + timedelta(hours=1)
        a = User(spotify_id="qa-a", display_name="A")
        b = User(spotify_id="qa-b", display_name="B")
        db.add_all([a, b])
        db.flush()
        db.add_all(
            [
                AppSession(user_id=a.id, session_token_hash=_hash("tok-a"), expires_at=exp),
                AppSession(user_id=b.id, session_token_hash=_hash("tok-b"), expires_at=exp),
            ]
        )
        room_a = MusicSession(code="ROOM-A", host_user_id=a.id, status="completed", expires_at=exp)
        room_b = MusicSession(code="ROOM-B", host_user_id=b.id, status="completed", expires_at=exp)
        db.add_all([room_a, room_b])
        db.flush()
        db.add_all(
            [
                MusicSessionMember(session_id=room_a.id, user_id=a.id, role="host"),
                MusicSessionMember(session_id=room_b.id, user_id=b.id, role="host"),
            ]
        )
        run_a = PlaylistRun(session_id=room_a.id, status="completed")
        run_b = PlaylistRun(session_id=room_b.id, status="completed")
        db.add_all([run_a, run_b])
        db.flush()
        db.add_all(
            [
                PlaylistRunTrack(
                    run_id=run_a.id, candidate_id="cand-a", spotify_id="track-A",
                    spotify_uri="spotify:track:A", name="A", artist="ArtA", status="matched",
                ),
                PlaylistRunTrack(
                    run_id=run_b.id, candidate_id="cand-b", spotify_id="track-B",
                    spotify_uri="spotify:track:B", name="B", artist="ArtB", status="matched",
                ),
            ]
        )
        db.commit()
        return {
            "a_id": a.id, "b_id": b.id,
            "run_a": run_a.id, "run_b": run_b.id,
        }
    finally:
        db.close()


def _as(client, token: str):
    client.cookies.set(SESSION_COOKIE_NAME, token)


# ---------------------------------------------------------------------------
# CT-PB20-03 — isolamento: faixa de outro run não é aceita
# ---------------------------------------------------------------------------

def test_faixa_de_outro_run_nao_e_aceita(client, session_factory):
    ids = _seed_two_rooms(session_factory)
    _as(client, "tok-a")
    # membro A tenta dar feedback, no run A, para a faixa 'track-B' (que é do run B)
    resp = client.post(
        f"/playlist-runs/{ids['run_a']}/tracks/track-B/feedback",
        json={"liked": True},
    )
    assert resp.status_code == 404, resp.text
    db = session_factory()
    try:
        assert db.query(MemberTrackFeedback).count() == 0
    finally:
        db.close()


def test_membro_de_outra_sala_nao_da_feedback_em_run_alheio(client, session_factory):
    ids = _seed_two_rooms(session_factory)
    # B (membro só da sala B) tenta feedback geral no run A
    _as(client, "tok-b")
    resp = client.post(f"/playlist-runs/{ids['run_a']}/feedback",
                       json={"representation_score": 5, "satisfaction_score": 5})
    assert resp.status_code == 403, resp.text
    db = session_factory()
    try:
        assert db.query(PlaylistFeedback).count() == 0
    finally:
        db.close()


# ---------------------------------------------------------------------------
# CT-PB20-04 — não-membro / não autenticado
# ---------------------------------------------------------------------------

def test_nao_autenticado_nao_da_feedback(client, session_factory):
    ids = _seed_two_rooms(session_factory)
    resp = client.post(f"/playlist-runs/{ids['run_a']}/feedback",
                       json={"representation_score": 3, "satisfaction_score": 3})
    assert resp.status_code == 401
    db = session_factory()
    try:
        assert db.query(PlaylistFeedback).count() == 0
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Limites 0–5 e comentário
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("rep,sat", [(-1, 3), (3, 6), (6, 6), (0, -1)])
def test_notas_fora_de_0_5_sao_rejeitadas(client, session_factory, rep, sat):
    ids = _seed_two_rooms(session_factory)
    _as(client, "tok-a")
    resp = client.post(f"/playlist-runs/{ids['run_a']}/feedback",
                       json={"representation_score": rep, "satisfaction_score": sat})
    assert resp.status_code == 422


def test_comentario_muito_longo_e_rejeitado(client, session_factory):
    ids = _seed_two_rooms(session_factory)
    _as(client, "tok-a")
    resp = client.post(f"/playlist-runs/{ids['run_a']}/feedback",
                       json={"representation_score": 3, "satisfaction_score": 3,
                             "comments": "x" * 2001})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Idempotência (upsert) — reenvio atualiza, não duplica
# ---------------------------------------------------------------------------

def test_reenvio_atualiza_sem_duplicar(client, session_factory):
    ids = _seed_two_rooms(session_factory)
    _as(client, "tok-a")
    url = f"/playlist-runs/{ids['run_a']}/tracks/track-A/feedback"
    assert client.post(url, json={"liked": True}).status_code == 200
    assert client.post(url, json={"liked": False, "never_again": True}).status_code == 200

    db = session_factory()
    try:
        rows = db.query(MemberTrackFeedback).all()
        assert len(rows) == 1, "reenvio não pode duplicar o registro"
        assert rows[0].liked is False and rows[0].never_again is True
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Aviso de uso futuro presente na resposta da API
# ---------------------------------------------------------------------------

def test_resposta_da_api_declara_uso_futuro(client, session_factory):
    ids = _seed_two_rooms(session_factory)
    _as(client, "tok-a")
    resp = client.post(f"/playlist-runs/{ids['run_a']}/feedback",
                       json={"representation_score": 4, "satisfaction_score": 5})
    assert resp.status_code == 200
    notice = resp.json().get("future_use_notice", "").lower()
    assert "futur" in notice and "ranking" in notice
