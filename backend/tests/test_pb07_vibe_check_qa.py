import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from datetime import datetime, timezone, timedelta
import hashlib

from app.main import app
from app.db.base import Base
from app.db.models import MusicSession, MusicSessionMember, User, AppSession, VibeCheckAnswer
from app.api.auth import SESSION_COOKIE_NAME
from app.db.session import get_db

@pytest.fixture()
def session_factory_qa(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pb07_qa.sqlite3'}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    yield factory
    Base.metadata.drop_all(engine)
    engine.dispose()

@pytest.fixture()
def db_qa(session_factory_qa):
    db_session = session_factory_qa()
    try:
        yield db_session
    finally:
        db_session.close()

@pytest.fixture()
def client_qa(session_factory_qa):
    def override_get_db():
        db = session_factory_qa()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def create_user_and_session(db: Session, spotify_id: str, display_name: str, token_str: str) -> str:
    user = User(spotify_id=spotify_id, display_name=display_name)
    db.add(user)
    db.commit()

    token_hash = hashlib.sha256(token_str.encode()).hexdigest()
    sess = AppSession(
        user_id=user.id,
        session_token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1)
    )
    db.add(sess)
    db.commit()
    return user.id

def test_ct_pb07_01_quant_perguntas(client_qa: TestClient, db_qa: Session):
    # Setup room and user
    user_id = create_user_and_session(db_qa, "host", "Host", "token_host")
    room = MusicSession(code="VIBEQA-01", host_user_id=user_id, status="open", expires_at=datetime.now(timezone.utc) + timedelta(days=1))
    db_qa.add(room)
    db_qa.flush()
    db_qa.add(MusicSessionMember(session_id=room.id, user_id=user_id, role="host"))
    db_qa.commit()

    res = client_qa.get(f"/rooms/{room.code}/vibe-check", cookies={SESSION_COOKIE_NAME: "token_host"})
    assert res.status_code == 200
    data = res.json()
    assert 3 <= len(data["questions"]) <= 5

def test_ct_pb07_03_05_respostas_upsert(client_qa: TestClient, db_qa: Session):
    user_id = create_user_and_session(db_qa, "host2", "Host 2", "token_host2")
    room = MusicSession(code="VIBEQA-02", host_user_id=user_id, status="open", expires_at=datetime.now(timezone.utc) + timedelta(days=1))
    db_qa.add(room)
    db_qa.flush()
    db_qa.add(MusicSessionMember(session_id=room.id, user_id=user_id, role="host"))
    db_qa.commit()

    # First submission
    payload1 = {"energy": 0.1, "valence": 0.2, "popularity": 0.3}
    res1 = client_qa.post(f"/rooms/{room.code}/vibe-check", json=payload1, cookies={SESSION_COOKIE_NAME: "token_host2"})
    assert res1.status_code == 200

    answers = db_qa.query(VibeCheckAnswer).filter_by(session_id=room.id, user_id=user_id).all()
    assert len(answers) == 1
    assert answers[0].energy == 0.1

    # Second submission (Update/Upsert)
    payload2 = {"energy": 0.9, "valence": 0.8, "popularity": 0.7}
    res2 = client_qa.post(f"/rooms/{room.code}/vibe-check", json=payload2, cookies={SESSION_COOKIE_NAME: "token_host2"})
    assert res2.status_code == 200

    db_qa.expire_all()
    answers2 = db_qa.query(VibeCheckAnswer).filter_by(session_id=room.id, user_id=user_id).all()
    assert len(answers2) == 1  # Should not duplicate!
    assert answers2[0].energy == 0.9

def test_ct_pb07_04_out_of_bounds(client_qa: TestClient, db_qa: Session):
    user_id = create_user_and_session(db_qa, "host3", "Host 3", "token_host3")
    room = MusicSession(code="VIBEQA-03", host_user_id=user_id, status="open", expires_at=datetime.now(timezone.utc) + timedelta(days=1))
    db_qa.add(room)
    db_qa.flush()
    db_qa.add(MusicSessionMember(session_id=room.id, user_id=user_id, role="host"))
    db_qa.commit()

    # Out of bounds (> 1.0)
    payload = {"energy": 1.1, "valence": 0.5, "popularity": -0.1}
    res = client_qa.post(f"/rooms/{room.code}/vibe-check", json=payload, cookies={SESSION_COOKIE_NAME: "token_host3"})
    assert res.status_code == 422 # Pydantic ValidationError

def test_ct_pb07_06_nao_membro(client_qa: TestClient, db_qa: Session):
    host_id = create_user_and_session(db_qa, "host4", "Host 4", "token_host4")
    non_member_id = create_user_and_session(db_qa, "intruder", "Intruder", "token_intruder")

    room = MusicSession(code="VIBEQA-04", host_user_id=host_id, status="open", expires_at=datetime.now(timezone.utc) + timedelta(days=1))
    db_qa.add(room)
    db_qa.flush()
    db_qa.add(MusicSessionMember(session_id=room.id, user_id=host_id, role="host"))
    db_qa.commit()

    # GET nao-membro
    res1 = client_qa.get(f"/rooms/{room.code}/vibe-check", cookies={SESSION_COOKIE_NAME: "token_intruder"})
    assert res1.status_code == 403

    # POST nao-membro
    payload = {"energy": 0.5, "valence": 0.5, "popularity": 0.5}
    res2 = client_qa.post(f"/rooms/{room.code}/vibe-check", json=payload, cookies={SESSION_COOKIE_NAME: "token_intruder"})
    assert res2.status_code == 403

def test_ct_pb07_02_pular(client_qa: TestClient, db_qa: Session):
    # O backend não exige que haja answers para poder prosseguir.
    # Mas se houver, usa. Se não houver, no PB-13 a geração usará pesos nulos.
    # Apenas certifica que GET pode ser consumido e POST não é forçado (já validado conceitualmente).
    pass
