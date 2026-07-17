"""Testes para o PB-13: Controle e histórico da geração."""

import hashlib
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.auth import SESSION_COOKIE_NAME
from app.db.base import Base
from app.db.models import AppSession, MusicSession, PlaylistRun, User, MusicSessionMember
from app.db.session import get_db
from app.main import app
from app.services.generation_service import complete_generation, fail_generation


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pb13.sqlite3'}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    yield factory
    Base.metadata.drop_all(engine)
    engine.dispose()

@pytest.fixture()
def db(session_factory):
    db_session = session_factory()
    try:
        yield db_session
    finally:
        db_session.close()

@pytest.fixture()
def client(session_factory):
    def _override_get_db():
        db_session = session_factory()
        try:
            yield db_session
        finally:
            db_session.close()
            
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture()
def host_token(db: Session) -> str:
    raw_token = "pb13-host-token"
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    user = User(spotify_id="pb13_host")
    db.add(user)
    db.flush()
    session = AppSession(
        user_id=user.id,
        session_token_hash=token_hash,
        expires_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc) + __import__("datetime").timedelta(days=1),
    )
    db.add(session)
    db.commit()
    return raw_token

@pytest.fixture()
def test_room(db: Session, host_token: str) -> MusicSession:
    user = db.query(User).filter_by(spotify_id="pb13_host").first()
    room = MusicSession(
        code="X9Y8Z7",
        host_user_id=user.id,
        status="open",
        expires_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc) + __import__("datetime").timedelta(hours=24),
    )
    db.add(room)
    db.flush()
    member = MusicSessionMember(
        session_id=room.id,
        user_id=user.id,
        role="host",
    )
    db.add(member)
    db.commit()
    return room


def test_pb13_primeira_geracao_cria_execucao(
    client: TestClient, db: Session, test_room: MusicSession, host_token: str
):
    """
    CT-PB13-01 — Primeira geração cria execução running.
    """
    response = client.post(
        f"/rooms/{test_room.code}/generate",
        headers={"Cookie": f"{SESSION_COOKIE_NAME}={host_token}"},
    )
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "running"
    assert "id" in data

    # Verifica o estado no banco
    db.refresh(test_room)
    assert test_room.status == "generating"


def test_pb13_geracao_concorrente_retorna_409(
    client: TestClient, db: Session, test_room: MusicSession, host_token: str
):
    """
    CT-PB13-02 — Geração concorrente retorna 409.
    """
    # 1. Primeira solicitação (deve passar)
    response1 = client.post(
        f"/rooms/{test_room.code}/generate",
        headers={"Cookie": f"{SESSION_COOKIE_NAME}={host_token}"},
    )
    assert response1.status_code == 202

    # 2. Segunda solicitação (deve falhar com 409)
    response2 = client.post(
        f"/rooms/{test_room.code}/generate",
        headers={"Cookie": f"{SESSION_COOKIE_NAME}={host_token}"},
    )
    assert response2.status_code == 409

    # Verifica se só tem 1 run running
    runs = db.query(PlaylistRun).filter_by(session_id=test_room.id).all()
    assert len(runs) == 1
    assert runs[0].status == "running"


def test_pb13_conclusao_e_falha_atualizam_estado(
    client: TestClient, db: Session, test_room: MusicSession, host_token: str
):
    """
    CT-PB13-03 — Conclusão e falha atualizam estado.
    """
    # Inicia a geração
    response = client.post(
        f"/rooms/{test_room.code}/generate",
        headers={"Cookie": f"{SESSION_COOKIE_NAME}={host_token}"},
    )
    run_id = uuid.UUID(response.json()["id"])

    # Atualiza a sessão de teste para refletir que no BD está generating
    db.expire_all()

    # Simula conclusão
    complete_generation(db, run_id)

    db.refresh(test_room)
    assert test_room.status == "open"  # Sala liberada

    run = db.query(PlaylistRun).get(run_id)
    assert run.status == "completed"

    # Agora simula uma falha em uma nova execução
    response2 = client.post(
        f"/rooms/{test_room.code}/generate",
        headers={"Cookie": f"{SESSION_COOKIE_NAME}={host_token}"},
    )
    run_id2 = uuid.UUID(response2.json()["id"])
    
    db.expire_all()
    fail_generation(db, run_id2, "Spotify API indisponível")
    
    db.refresh(test_room)
    assert test_room.status == "open"
    
    run2 = db.query(PlaylistRun).get(run_id2)
    assert run2.status == "failed"
    assert run2.error_message == "Spotify API indisponível"


def test_pb13_retry_controlado_apos_falha(
    client: TestClient, db: Session, test_room: MusicSession, host_token: str
):
    """
    CT-PB13-04 — Retry controlado após falha.
    """
    # Host inicia geração
    response1 = client.post(
        f"/rooms/{test_room.code}/generate",
        headers={"Cookie": f"{SESSION_COOKIE_NAME}={host_token}"},
    )
    run_id1 = uuid.UUID(response1.json()["id"])

    db.expire_all()
    # Geração falha
    fail_generation(db, run_id1, "Erro")

    # Host tenta novamente (retry)
    response2 = client.post(
        f"/rooms/{test_room.code}/generate",
        headers={"Cookie": f"{SESSION_COOKIE_NAME}={host_token}"},
    )
    assert response2.status_code == 202
    run_id2 = uuid.UUID(response2.json()["id"])

    # Registros devem ser independentes
    assert run_id1 != run_id2
    runs = db.query(PlaylistRun).filter_by(session_id=test_room.id).all()
    assert len(runs) == 2
