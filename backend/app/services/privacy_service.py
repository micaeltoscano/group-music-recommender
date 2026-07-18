"""Operacoes de sessao e privacidade do usuario (PB-03)."""

from __future__ import annotations

import hashlib
import uuid

from sqlalchemy.orm import Session

from app.db.models import (
    AppSession,
    SpotifyToken,
    User,
    UserMusicSnapshot,
    VibeCheckAnswer,
)

ANONYMIZED_DISPLAY_NAME = "Usuário removido"


def _session_hash(raw_session_token: str) -> str:
    return hashlib.sha256(raw_session_token.encode()).hexdigest()


def invalidate_session(db: Session, raw_session_token: str | None) -> bool:
    """Invalida somente a sessao indicada e nao revela se ela existia."""

    if not raw_session_token:
        return False

    removed = (
        db.query(AppSession)
        .filter(AppSession.session_token_hash == _session_hash(raw_session_token))
        .delete(synchronize_session=False)
    )
    db.commit()
    return bool(removed)


def remove_personal_data(db: Session, user_id: int) -> None:
    """Remove dados pessoais e anonimiza a identidade preservando dados do grupo.

    A linha de ``users`` permanece como sujeito anonimo porque remove-la acionaria
    ``ON DELETE CASCADE`` nas salas hospedadas, apagando playlists e participacoes
    de terceiros. O Spotify ID e substituido por um valor aleatorio irreversivel,
    permitindo que a mesma conta crie uma identidade nova em login futuro.
    """

    user = db.get(User, user_id)
    if user is None:
        return

    try:
        db.query(SpotifyToken).filter(SpotifyToken.user_id == user_id).delete(
            synchronize_session=False
        )
        db.query(AppSession).filter(AppSession.user_id == user_id).delete(
            synchronize_session=False
        )
        db.query(UserMusicSnapshot).filter(UserMusicSnapshot.user_id == user_id).delete(
            synchronize_session=False
        )
        db.query(VibeCheckAnswer).filter(VibeCheckAnswer.user_id == user_id).delete(
            synchronize_session=False
        )

        user.spotify_id = f"deleted-{uuid.uuid4().hex}"
        user.display_name = ANONYMIZED_DISPLAY_NAME
        user.image_url = None
        db.commit()
    except Exception:
        db.rollback()
        raise
