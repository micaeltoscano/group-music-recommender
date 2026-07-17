import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from uuid import uuid4
import hashlib
from datetime import datetime, timezone, timedelta

from app.main import app
from app.db.base import Base
from app.db.models import MusicSession, MusicSessionMember, VibeCheckAnswer, User, AppSession
from app.api.auth import SESSION_COOKIE_NAME
from app.db.session import get_db

@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pb07.sqlite3'}",
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
    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()
            
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture()
def user_token(db: Session):
    user = User(spotify_id="host_123", display_name="Host User")
    db.add(user)
    db.commit()
    
    token = "test_token_777"
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    sess = AppSession(
        user_id=user.id,
        session_token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1)
    )
    db.add(sess)
    db.commit()
    return token


def test_get_vibe_check_questions(client: TestClient, db: Session, user_token: str):
    # Mocking room and membership
    room = MusicSession(
        code="VIBE-007", 
        host_user_id=1, 
        status="open",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1)
    )
    db.add(room)
    db.commit()

    member = MusicSessionMember(session_id=room.id, user_id=1, role="host")
    db.add(member)
    db.commit()

    response = client.get(
        f"/rooms/{room.code}/vibe-check",
        cookies={SESSION_COOKIE_NAME: user_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "questions" in data
    assert len(data["questions"]) == 3
    assert data["questions"][0]["id"] == "energy"


def test_post_vibe_check_upsert(client: TestClient, db: Session, user_token: str):
    room = MusicSession(
        code="VIBE-008", 
        host_user_id=1, 
        status="open",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1)
    )
    db.add(room)
    db.commit()

    member = MusicSessionMember(session_id=room.id, user_id=1, role="host")
    db.add(member)
    db.commit()

    # First submission
    payload = {"energy": 0.5, "valence": 0.8, "popularity": 1.0}
    res1 = client.post(
        f"/rooms/{room.code}/vibe-check",
        json=payload,
        cookies={SESSION_COOKIE_NAME: user_token}
    )
    assert res1.status_code == 200
    assert "salvo com sucesso" in res1.json()["message"]

    answers = db.query(VibeCheckAnswer).filter_by(session_id=room.id, user_id=1).all()
    assert len(answers) == 1
    assert answers[0].energy == 0.5

    # Second submission (should update)
    payload2 = {"energy": 0.1, "valence": 0.9, "popularity": 0.6}
    res2 = client.post(
        f"/rooms/{room.code}/vibe-check",
        json=payload2,
        cookies={SESSION_COOKIE_NAME: user_token}
    )
    assert res2.status_code == 200

    db.expire_all()
    answers = db.query(VibeCheckAnswer).filter_by(session_id=room.id, user_id=1).all()
    assert len(answers) == 1
    assert answers[0].energy == 0.1


def test_vibe_check_not_member(client: TestClient, db: Session, user_token: str):
    # Room exists but user is not member
    room = MusicSession(
        code="VIBE-009", 
        host_user_id=2, 
        status="open",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1)
    )
    db.add(room)
    db.commit()

    response = client.get(
        f"/rooms/{room.code}/vibe-check",
        cookies={SESSION_COOKIE_NAME: user_token}
    )
    assert response.status_code == 403
    assert "Você não é membro desta sala" in response.json()["detail"]
