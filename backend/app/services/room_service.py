"""Regras de criação, entrada e consulta de salas efêmeras."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import MusicSession, MusicSessionMember, User
from app.config import settings

ROOM_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
ROOM_CODE_ATTEMPTS = 10
ROOM_LIFETIME = timedelta(hours=24)
MAX_ROOM_MEMBERS = 5
BASE_CONSENSUS_MODES = ("Democrático", "Festa Segura")
DISCOVERY_MODE = "Descoberta"


class RoomCodeGenerationError(RuntimeError):
    """Indica que não foi possível reservar um código único para a sala."""


class RoomNotFoundError(LookupError):
    """Indica que o código informado não identifica uma sala."""


class RoomExpiredError(RuntimeError):
    """Indica que a janela de participação da sala terminou."""


class RoomFullError(RuntimeError):
    """Indica que a sala já atingiu o limite de integrantes."""


class RoomAccessDeniedError(PermissionError):
    """Indica tentativa de consultar uma sala sem ser integrante."""


class RoomHostRequiredError(PermissionError):
    """Indica tentativa de alteração da sala por quem não é o host."""


class RoomModeUnavailableError(ValueError):
    """Indica tentativa de selecionar um modo conhecido, mas desabilitado."""


def available_consensus_modes() -> list[str]:
    """Retorna os modos habilitados pela configuração atual do produto."""

    modes = list(BASE_CONSENSUS_MODES)
    if settings.discovery_mode_enabled:
        modes.append(DISCOVERY_MODE)
    return modes


def _generate_room_code() -> str:
    """Gera um código legível de oito caracteres, agrupado em dois blocos."""
    raw = "".join(secrets.choice(ROOM_CODE_ALPHABET) for _ in range(8))
    return f"{raw[:4]}-{raw[4:]}"


def normalize_room_code(code: str) -> str:
    """Normaliza o código digitado sem aceitar caracteres além dos oito símbolos."""
    raw = "".join(character for character in code.upper().strip() if character.isalnum())
    if len(raw) != 8:
        return code.upper().strip()
    return f"{raw[:4]}-{raw[4:]}"


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _room_for_join_statement(code: str):
    """Monta a leitura com lock que serializa ingressos na mesma sala no Postgres."""
    return (
        select(MusicSession)
        .where(MusicSession.code == normalize_room_code(code))
        .with_for_update()
    )


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


def join_room(
    db: Session,
    code: str,
    user_id: int,
    *,
    now: datetime | None = None,
) -> tuple[MusicSession, MusicSessionMember]:
    """Associa um usuário à sala de forma idempotente e respeitando o limite.

    O lock da linha da sala mantém a sequência contar/inserir atômica entre
    transações concorrentes no PostgreSQL, banco alvo da aplicação.
    """
    joined_at = _as_utc(now or datetime.now(timezone.utc))
    room = db.execute(_room_for_join_statement(code)).scalar_one_or_none()
    if room is None:
        db.rollback()
        raise RoomNotFoundError("Sala não encontrada.")

    if _as_utc(room.expires_at) <= joined_at:
        db.rollback()
        raise RoomExpiredError("Esta sala expirou.")

    membership = db.get(MusicSessionMember, (room.id, user_id))
    if membership is not None:
        db.commit()
        return room, membership

    member_count = db.scalar(
        select(func.count())
        .select_from(MusicSessionMember)
        .where(MusicSessionMember.session_id == room.id)
    )
    if member_count is not None and member_count >= MAX_ROOM_MEMBERS:
        db.rollback()
        raise RoomFullError("A sala já atingiu o limite de cinco integrantes.")

    membership = MusicSessionMember(
        session_id=room.id,
        user_id=user_id,
        role="member",
        joined_at=joined_at,
    )
    db.add(membership)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        membership = db.get(MusicSessionMember, (room.id, user_id))
        if membership is None:
            raise
        return room, membership

    db.refresh(membership)
    return room, membership


def get_room_for_member(db: Session, code: str, user_id: int) -> MusicSession:
    """Obtém a sala quando o usuário autenticado pertence a ela."""
    room = db.scalar(
        select(MusicSession).where(MusicSession.code == normalize_room_code(code))
    )
    if room is None:
        raise RoomNotFoundError("Sala não encontrada.")

    membership = db.get(MusicSessionMember, (room.id, user_id))
    if membership is None:
        raise RoomAccessDeniedError("Apenas integrantes podem consultar esta sala.")
    return room


def _get_room_for_host(db: Session, code: str, user_id: int) -> MusicSession:
    """Obtém uma sala apenas quando o usuário autenticado é seu host."""
    room = get_room_for_member(db, code, user_id)
    if room.host_user_id != user_id:
        raise RoomHostRequiredError("Somente o host pode alterar esta sala.")
    return room


def update_room_context(
    db: Session,
    code: str,
    user_id: int,
    *,
    occasion: str | None,
    description: str | None,
) -> MusicSession:
    """Substitui ocasião/descrição depois de validar o papel de host."""
    room = _get_room_for_host(db, code, user_id)
    room.occasion = occasion
    room.description = description
    db.commit()
    db.refresh(room)
    return room


def update_room_mode(
    db: Session,
    code: str,
    user_id: int,
    *,
    mode: str,
) -> MusicSession:
    """Persiste um modo já validado pelo contrato da API."""
    room = _get_room_for_host(db, code, user_id)
    if mode not in available_consensus_modes():
        raise RoomModeUnavailableError(
            "O modo Descoberta está desabilitado na configuração do produto."
        )
    room.mode = mode
    db.commit()
    db.refresh(room)
    return room


def list_room_members(
    db: Session,
    room_id: UUID,
) -> list[tuple[MusicSessionMember, User]]:
    """Lista integrantes e apenas seus dados públicos em ordem estável."""
    rows = db.execute(
        select(MusicSessionMember, User)
        .join(User, User.id == MusicSessionMember.user_id)
        .where(MusicSessionMember.session_id == room_id)
        .order_by(MusicSessionMember.joined_at, MusicSessionMember.user_id)
    )
    return list(rows.tuples())
