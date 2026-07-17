"""QA (revalidação rodada 3) — PB-16, pós-correção de DEF-PB16-04.

Sonda a correção de `build_room_result` (complemento de membros ausentes no
snapshot persistido) em busca de duplicatas, ordenação e interação com o
caminho de recomputo (run sem métricas persistidas).
"""

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.auth import SESSION_COOKIE_NAME
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
from app.main import app
from app.services import generation_service


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pb16_qa_r3.sqlite3'}",
        connect_args={"check_same_thread": False, "timeout": 30},
        future=True,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
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


def _authenticated_user(session_factory, spotify_id: str, display_name: str) -> str:
    raw_token = f"qa-session-for-{spotify_id}"
    db = session_factory()
    try:
        user = db.query(User).filter(User.spotify_id == spotify_id).first()
        if not user:
            user = User(spotify_id=spotify_id, display_name=display_name)
            db.add(user)
            db.flush()
        db.add(
            AppSession(
                user_id=user.id,
                session_token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
        )
        db.commit()
        return raw_token
    finally:
        db.close()


def _act_as(client: TestClient, token: str) -> None:
    client.cookies.set(SESSION_COOKIE_NAME, token)


def test_sem_duplicidade_quando_todos_membros_ja_representados(client, session_factory):
    """Regressão: a correção do DEF-PB16-04 não deve duplicar membros que já
    estavam no snapshot persistido (cenário normal, sem ninguém entrando depois).
    """
    db = session_factory()
    try:
        u1 = User(spotify_id="r3-u1", display_name="Alice")
        u2 = User(spotify_id="r3-u2", display_name="Bob")
        db.add_all([u1, u2])
        db.flush()
        room = MusicSession(
            code="VIBE-R3A1",
            host_user_id=u1.id,
            status="open",
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )
        db.add(room)
        db.flush()
        db.add_all(
            [
                MusicSessionMember(session_id=room.id, user_id=u1.id, role="host"),
                MusicSessionMember(session_id=room.id, user_id=u2.id, role="member"),
            ]
        )
        db.flush()
        run = PlaylistRun(session_id=room.id, status="running")
        db.add(run)
        db.flush()
        db.add(
            PlaylistRunTrack(
                run_id=run.id,
                candidate_id=uuid.uuid4().hex,
                name="Track A",
                artist="Art A",
                status="matched",
                match_confidence=1.0,
                spotify_uri="uri:a",
                source=json.dumps([u1.id, u2.id]),
            )
        )
        db.commit()
        run_id = run.id
    finally:
        db.close()

    db = session_factory()
    try:
        generation_service.complete_generation(db, run_id)
    finally:
        db.close()

    token = _authenticated_user(session_factory, "r3-u1", "Alice")
    _act_as(client, token)
    resp = client.get("/rooms/VIBE-R3A1/result")
    assert resp.status_code == 200
    data = resp.json()

    user_ids = [r["user_id"] for r in data["representation"]]
    assert len(user_ids) == len(set(user_ids)), "Representação não deve conter duplicatas."
    assert len(data["representation"]) == 2


def test_run_antigo_sem_metricas_persistidas_ainda_funciona(client, session_factory):
    """Caminho de recomputo (run concluído ANTES da migração/feature existir,
    sem compatibility_score/fairness_score/explanation_json) continua íntegro
    e já inclui todos os membros atuais por construção.
    """
    db = session_factory()
    try:
        u1 = User(spotify_id="r3-u1b", display_name="Alice")
        u2 = User(spotify_id="r3-u2b", display_name="Bob")
        db.add_all([u1, u2])
        db.flush()
        room = MusicSession(
            code="VIBE-R3B1",
            host_user_id=u1.id,
            status="open",
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )
        db.add(room)
        db.flush()
        db.add_all(
            [
                MusicSessionMember(session_id=room.id, user_id=u1.id, role="host"),
                MusicSessionMember(session_id=room.id, user_id=u2.id, role="member"),
            ]
        )
        db.flush()
        # Run concluído SEM métricas persistidas (simula dado legado pré-DEF-PB16-01).
        run = PlaylistRun(
            session_id=room.id,
            status="completed",
            spotify_playlist_url="https://open.spotify.com/playlist/legacy",
        )
        db.add(run)
        db.flush()
        db.add(
            PlaylistRunTrack(
                run_id=run.id,
                candidate_id=uuid.uuid4().hex,
                name="Track A",
                artist="Art A",
                status="matched",
                match_confidence=1.0,
                spotify_uri="uri:a",
                source=json.dumps([u1.id]),
            )
        )
        db.commit()
    finally:
        db.close()

    token = _authenticated_user(session_factory, "r3-u2b", "Bob")
    _act_as(client, token)
    resp = client.get("/rooms/VIBE-R3B1/result")
    assert resp.status_code == 200
    data = resp.json()
    names = {r["display_name"] for r in data["representation"]}
    assert names == {"Alice", "Bob"}
