"""Rotas de salas efêmeras."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.session import get_db
from app.schemas.rooms import RoomMemberResponse, RoomResponse
from app.services.room_service import RoomCodeGenerationError, create_room

router = APIRouter()


@router.post("", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
def create_music_room(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoomResponse:
    """Cria uma sala e registra o usuário autenticado como host."""
    try:
        room, membership = create_room(db, current_user["id"])
    except RoomCodeGenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível criar a sala agora. Tente novamente.",
        ) from exc

    return RoomResponse(
        id=room.id,
        code=room.code,
        status="open",
        created_at=room.created_at,
        expires_at=room.expires_at,
        members=[
            RoomMemberResponse(
                user_id=current_user["id"],
                display_name=current_user["display_name"],
                image_url=current_user["image_url"],
                role="host",
                joined_at=membership.joined_at,
            )
        ],
    )
