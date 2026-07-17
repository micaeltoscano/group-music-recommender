"""Serviço para controle da execução de geração de playlist (PB-13)."""

import uuid

from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from app.db.models import MusicSession, PlaylistRun
from app.services.room_service import RoomHostRequiredError, RoomNotFoundError


class GenerationConflictError(Exception):
    """Lançada quando já há uma geração em andamento."""


def start_generation(db: Session, code: str, host_id: int) -> PlaylistRun:
    """
    Inicia uma nova geração. Faz o lock do banco para impedir concorrência.
    Retorna o PlaylistRun recém criado no estado running.
    """
    try:
        # Lock pessimista para a linha da sala.
        room = db.query(MusicSession).with_for_update().filter(MusicSession.code == code).one()
    except NoResultFound as exc:
        raise RoomNotFoundError(f"Sala '{code}' não encontrada.") from exc

    if room.host_user_id != host_id:
        raise RoomHostRequiredError("Apenas o host pode iniciar a geração.")

    if room.status == "generating":
        raise GenerationConflictError("Uma geração já está em andamento para esta sala.")

    # Altera estado da sala
    room.status = "generating"

    # Registra o histórico da execução
    run = PlaylistRun(
        session_id=room.id,
        status="running",
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    return run


def complete_generation(db: Session, run_id: uuid.UUID) -> None:
    """Marca a execução como completed e libera a sala."""
    run = db.query(PlaylistRun).with_for_update().filter(PlaylistRun.id == run_id).one()
    run.status = "completed"

    room = db.query(MusicSession).with_for_update().filter(MusicSession.id == run.session_id).one()
    room.status = "open"

    db.commit()


def fail_generation(db: Session, run_id: uuid.UUID, error_message: str) -> None:
    """Marca a execução como failed e libera a sala para novas tentativas."""
    run = db.query(PlaylistRun).with_for_update().filter(PlaylistRun.id == run_id).one()
    run.status = "failed"
    run.error_message = error_message

    room = db.query(MusicSession).with_for_update().filter(MusicSession.id == run.session_id).one()
    room.status = "open"

    db.commit()
