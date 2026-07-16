"""Schemas públicos das salas."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class RoomMemberResponse(BaseModel):
    """Dados não sensíveis de um integrante retornados ao cliente."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    display_name: str | None
    image_url: str | None
    role: Literal["host", "member"]
    joined_at: datetime

    @field_validator("joined_at")
    @classmethod
    def joined_at_is_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class RoomResponse(BaseModel):
    """Estado inicial de uma sala recém-criada."""

    id: UUID
    code: str
    status: Literal["open"]
    created_at: datetime
    expires_at: datetime
    members: list[RoomMemberResponse]

    @field_validator("created_at", "expires_at")
    @classmethod
    def dates_are_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
