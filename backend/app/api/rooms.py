"""Rotas de salas efêmeras."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.models import MusicSession
from app.db.session import get_db
from app.schemas.rooms import RoomMemberResponse, RoomResponse
from app.services.room_service import (
    RoomAccessDeniedError,
    RoomCodeGenerationError,
    RoomExpiredError,
    RoomFullError,
    RoomNotFoundError,
    create_room,
    get_room_for_member,
    join_room,
    list_room_members,
)

router = APIRouter()


def _room_response(db: Session, room: MusicSession) -> RoomResponse:
    members = [
        RoomMemberResponse(
            user_id=user.id,
            display_name=user.display_name,
            image_url=user.image_url,
            role=membership.role,
            joined_at=membership.joined_at,
        )
        for membership, user in list_room_members(db, room.id)
    ]
    return RoomResponse(
        id=room.id,
        code=room.code,
        status=room.status,
        created_at=room.created_at,
        expires_at=room.expires_at,
        members=members,
    )


@router.post("", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
def create_music_room(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoomResponse:
    """Cria uma sala e registra o usuário autenticado como host."""
    try:
        room, _ = create_room(db, current_user["id"])
    except RoomCodeGenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível criar a sala agora. Tente novamente.",
        ) from exc

    return _room_response(db, room)


@router.post("/{code}/join", response_model=RoomResponse)
def join_music_room(
    code: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoomResponse:
    """Entra em uma sala existente ou devolve o estado atual se já for membro."""
    try:
        room, _ = join_room(db, code, current_user["id"])
    except RoomNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RoomExpiredError as exc:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(exc)) from exc
    except RoomFullError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _room_response(db, room)


@router.get("/{code}", response_model=RoomResponse)
def read_music_room(
    code: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoomResponse:
    """Retorna o estado público da sala somente para integrantes."""
    try:
        room = get_room_for_member(db, code, current_user["id"])
    except RoomNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RoomAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return _room_response(db, room)
