"""Testes de QA para PB-16 (Resultado e explicabilidade)."""

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
from app.db.models import AppSession, MusicSession, MusicSessionMember, PlaylistRun, PlaylistRunTrack, User
from app.db.session import get_db
from app.main import app

@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pb16_qa.sqlite3'}",
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

@pytest.fixture
def mock_db_with_run(session_factory):
    db = session_factory()
    try:
        # Criar usuários - ids gerados via autoincrement
        u1 = User(spotify_id="u1", display_name="Alice")
        u2 = User(spotify_id="u2", display_name="Bob")
        u3 = User(spotify_id="u3", display_name="Charlie")
        db.add_all([u1, u2, u3])
        db.flush()
        
        # Criar sala
        room = MusicSession(
            code="VIBE16",
            host_user_id=u1.id,
            status="open",
            expires_at=datetime.now(timezone.utc) + timedelta(days=1)
        )
        db.add(room)
        db.flush()
        
        # Adicionar membros
        m1 = MusicSessionMember(session_id=room.id, user_id=u1.id, role="host")
        m2 = MusicSessionMember(session_id=room.id, user_id=u2.id, role="member")
        m3 = MusicSessionMember(session_id=room.id, user_id=u3.id, role="member")
        db.add_all([m1, m2, m3])
        db.flush()
        
        # Criar playlist run concluída
        run = PlaylistRun(
            session_id=room.id,
            status="completed",
            spotify_playlist_url="https://open.spotify.com/playlist/test"
        )
        db.add(run)
        db.flush()
        
        # Criar algumas faixas
        tracks = [
            PlaylistRunTrack(
                run_id=run.id, candidate_id="lastfm:discovery-a", name="Track A", artist="Art A",
                status="matched", match_confidence=1.0, spotify_uri="uri:a", 
                source=json.dumps([u1.id, u2.id])
            ),
            PlaylistRunTrack(
                run_id=run.id, candidate_id="lastfm:discovery-b", name="Track B", artist="Art B",
                status="matched", match_confidence=1.0, spotify_uri="uri:b", 
                source=json.dumps([u2.id, u3.id])
            ),
            PlaylistRunTrack(
                run_id=run.id, candidate_id=uuid.uuid4().hex, name="Track C", artist="Art C", 
                status="matched", match_confidence=1.0, spotify_uri="uri:c", 
                source=json.dumps([u1.id])
            ),
            PlaylistRunTrack( # Simular uma música sem source válida ou com um erro de formatação
                run_id=run.id, candidate_id=uuid.uuid4().hex, name="Track D", artist="Art D", 
                status="matched", match_confidence=1.0, spotify_uri="uri:d", 
                source="invalid"
            ),
        ]
        db.add_all(tracks)
        db.commit()
    finally:
        db.close()


def test_pb16_link_playlist_and_metrics(client: TestClient, session_factory, mock_db_with_run):
    """
    CT-PB16-01 — Link da playlist presente
    CT-PB16-02 — Compatibilidade e fairness exibidos
    CT-PB16-03 — Representação por integrante
    CT-PB16-04 — Justificativa por música
    """
    # Autenticar como user 1 ("Alice", u1). Esse ID é o token mockado
    token = _authenticated_user(session_factory, "u1", "Alice")
    _act_as(client, token)
    
    response = client.get("/rooms/VIBE16/result")
    assert response.status_code == 200
    data = response.json()
    
    # CT-PB16-01
    assert data["playlist_url"] == "https://open.spotify.com/playlist/test"
    
    # CT-PB16-02
    assert "compatibility_score" in data
    assert "fairness_score" in data
    assert data["discovery_percentage"] == 50
    assert isinstance(data["compatibility_score"], int)
    
    # CT-PB16-03
    representation = data["representation"]
    assert len(representation) == 3
    names = {r["display_name"] for r in representation}
    assert "Alice" in names
    
    # CT-PB16-04
    tracks = data["tracks"]
    assert len(tracks) == 4
    for track in tracks:
        assert "reason" in track
        assert "contributed_by" in track
        assert "name" in track
        
        
def test_pb16_privacy_no_rejection_exposed(client: TestClient, session_factory, mock_db_with_run):
    """
    CT-PB16-05 — Privacidade: não expor rejeições de terceiros
    """
    token = _authenticated_user(session_factory, "u1", "Alice")
    _act_as(client, token)
    
    response = client.get("/rooms/VIBE16/result")
    assert response.status_code == 200
    data = response.json()
    
    # Checar os motivos de cada faixa e garantir que não tem palavras que indicam "fulano vetou"
    tracks = data["tracks"]
    for track in tracks:
        reason = track["reason"].lower()
        assert "rejeito" not in reason
        assert "vetou" not in reason
        assert "bloqueou" not in reason


def test_pb16_access_denied_for_non_members(client: TestClient, session_factory, mock_db_with_run):
    """
    CT-PB16-06 — Acesso restrito a membros
    """
    # Usuário não membro
    token = _authenticated_user(session_factory, "intruder", "Intruso")
    _act_as(client, token)
    
    response = client.get("/rooms/VIBE16/result")
    assert response.status_code == 403
    
    # Usuário sem sessão
    client.cookies.clear()
    response = client.get("/rooms/VIBE16/result")
    assert response.status_code == 401
