"""Regras de criação de salas efêmeras."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import MusicSession, MusicSessionMember

ROOM_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
ROOM_CODE_ATTEMPTS = 10
ROOM_LIFETIME = timedelta(hours=24)


class RoomCodeGenerationError(RuntimeError):
    """Indica que não foi possível reservar um código único para a sala."""


def _generate_room_code() -> str:
    """Gera um código legível de oito caracteres, agrupado em dois blocos."""
    raw = "".join(secrets.choice(ROOM_CODE_ALPHABET) for _ in range(8))
    return f"{raw[:4]}-{raw[4:]}"


def create_room(
    db: Session,
    host_user_id: int,
    *,
    now: datetime | None = None,
) -> tuple[MusicSession, MusicSessionMember]:
    """Cria sala e vínculo do host atomicamente, repetindo em colisões de código."""
    created_at = now or datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    else:
        created_at = created_at.astimezone(timezone.utc)

    for _ in range(ROOM_CODE_ATTEMPTS):
        room = MusicSession(
            code=_generate_room_code(),
            host_user_id=host_user_id,
            status="open",
            created_at=created_at,
            expires_at=created_at + ROOM_LIFETIME,
        )
        membership = MusicSessionMember(
            music_session=room,
            user_id=host_user_id,
            role="host",
            joined_at=created_at,
        )
        db.add(room)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            continue

        db.refresh(room)
        db.refresh(membership)
        return room, membership

    raise RoomCodeGenerationError("Não foi possível gerar um código único para a sala.")
