"""QA (revalidação) — PB-16, pós-correção de DEF-PB16-01/02/03.

Testes independentes para confirmar as correções e sondar o novo
`result_service` em busca de regressões não cobertas pelos testes do
próprio implementador.
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
        f"sqlite:///{tmp_path / 'pb16_qa_reval.sqlite3'}",
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


def test_membro_que_entra_apos_conclusao_do_run_nao_aparece_na_representacao(client, session_factory):
    """BUG: `build_room_result` usa a representação PERSISTIDA (snapshot do
    momento da conclusão) sem reconciliar com os membros atuais da sala. Um
    integrante que entra depois do run concluído consulta /result e não se vê
    na representação -- quebra o critério 3 ("representação por integrante")
    para esse usuário, mesmo tendo acesso legítimo (é membro).
    """
    db = session_factory()
    try:
        u1 = User(spotify_id="late-u1", display_name="Alice")
        db.add(u1)
        db.flush()
        room = MusicSession(
            code="VIBE-LATE",
            host_user_id=u1.id,
            status="open",
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )
        db.add(room)
        db.flush()
        db.add(MusicSessionMember(session_id=room.id, user_id=u1.id, role="host"))
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
                source=json.dumps([u1.id]),
            )
        )
        db.commit()
        run_id = run.id
        room_id = room.id
    finally:
        db.close()

    # Conclui o run só com Alice na sala.
    db = session_factory()
    try:
        generation_service.complete_generation(db, run_id)
    finally:
        db.close()

    # Bob entra na sala DEPOIS da conclusão.
    db = session_factory()
    try:
        u2 = User(spotify_id="late-u2", display_name="Bob")
        db.add(u2)
        db.flush()
        db.add(MusicSessionMember(session_id=room_id, user_id=u2.id, role="member"))
        db.commit()
    finally:
        db.close()

    token = _authenticated_user(session_factory, "late-u2", "Bob")
    _act_as(client, token)
    resp = client.get("/rooms/VIBE-LATE/result")
    assert resp.status_code == 200
    data = resp.json()

    names = {r["display_name"] for r in data["representation"]}
    # Bob é membro da sala e consultou o próprio resultado do grupo, mas não
    # aparece na representação porque o payload persistido é um snapshot antigo.
    assert "Bob" in names, (
        "Bob é membro atual da sala mas ficou de fora da representação "
        "persistida no momento da conclusão do run (DEF-PB16-04)."
    )
