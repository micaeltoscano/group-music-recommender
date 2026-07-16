"""Schemas públicos das salas."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

ConsensusMode = Literal["Democrático", "Festa Segura"]


class RoomContextUpdate(BaseModel):
    """Contexto livre definido pelo host para a sala."""

    occasion: str | None = None
    description: str | None = None

    @field_validator("occasion", "description", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        normalized = value.strip()
        return normalized or None

    @field_validator("occasion")
    @classmethod
    def occasion_has_valid_length(cls, value: str | None) -> str | None:
        if value is not None and len(value) > 100:
            raise ValueError("A ocasião deve ter no máximo 100 caracteres.")
        return value

    @field_validator("description")
    @classmethod
    def description_has_valid_length(cls, value: str | None) -> str | None:
        if value is not None and len(value) > 1000:
            raise ValueError("A descrição deve ter no máximo 1000 caracteres.")
        return value

    @model_validator(mode="after")
    def has_occasion_or_description(self) -> "RoomContextUpdate":
        if self.occasion is None and self.description is None:
            raise ValueError("Informe a ocasião, a descrição ou ambas.")
        return self


class RoomModeUpdate(BaseModel):
    """Modo de consenso permitido no MVP."""

    mode: ConsensusMode


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
    occasion: str | None
    description: str | None
    mode: ConsensusMode | None
    created_at: datetime
    expires_at: datetime
    members: list[RoomMemberResponse]

    @field_validator("created_at", "expires_at")
    @classmethod
    def dates_are_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
