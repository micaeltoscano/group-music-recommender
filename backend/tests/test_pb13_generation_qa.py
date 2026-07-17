import hashlib
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.auth import SESSION_COOKIE_NAME
from app.db.models import AppSession, MusicSession, PlaylistRun, User, MusicSessionMember
from tests.test_pb13_generation import session_factory, db, client, host_token, test_room

@pytest.fixture()
def member_token(db: Session, test_room: MusicSession) -> str:
    """Cria um token para um membro que não é o host."""
    raw_token = "pb13-member-token"
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    user = User(spotify_id="pb13_member")
    db.add(user)
    db.flush()
    
    session = AppSession(
        user_id=user.id,
        session_token_hash=token_hash,
        expires_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc) + __import__("datetime").timedelta(days=1),
    )
    db.add(session)
    
    member = MusicSessionMember(
        session_id=test_room.id,
        user_id=user.id,
        role="member",
    )
    db.add(member)
    db.commit()
    return raw_token

def test_pb13_qa_only_host_generates(client: TestClient, db: Session, test_room: MusicSession, member_token: str):
    """CT-PB13-05 — Só host dispara geração. Membro comum recebe 403."""
    response = client.post(
        f"/rooms/{test_room.code}/generate",
        headers={"Cookie": f"{SESSION_COOKIE_NAME}={member_token}"},
    )
    assert response.status_code == 403
    assert "Only the host" in response.json()["detail"] or response.status_code == 403
    
    # Nenhuma run deve ter sido criada
    runs = db.query(PlaylistRun).filter_by(session_id=test_room.id).all()
    assert len(runs) == 0
