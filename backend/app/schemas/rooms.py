"""Schemas públicos das salas."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

ConsensusMode = Literal["Democrático", "Festa Segura", "Descoberta"]


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
    """Modo de consenso conhecido; disponibilidade é validada no servidor."""

    mode: ConsensusMode


class ConsensusModesResponse(BaseModel):
    """Modos que podem ser selecionados na configuração atual."""

    modes: list[ConsensusMode]


class RoomMemberResponse(BaseModel):
    """Dados não sensíveis de um integrante retornados ao cliente."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    display_name: str | None
    image_url: str | None
    role: Literal["host", "member"]
    vibe_status: Literal["pending", "answered", "skipped"] = "pending"
    joined_at: datetime

    @field_validator("joined_at")
    @classmethod
    def joined_at_is_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class RoomGenerationResponse(BaseModel):
    """Estado agregado da última execução, compartilhável com a sala."""

    run_id: UUID
    status: Literal["running", "completed", "failed"]
    stage: str
    progress_percent: int
    error_message: str | None
    playlist_url: str | None
    updated_at: datetime

    @field_validator("updated_at")
    @classmethod
    def updated_at_is_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class VibeSummaryResponse(BaseModel):
    """Contagem agregada, sem os valores privados das respostas."""

    total: int
    pending: int
    answered: int
    skipped: int


class RoomResponse(BaseModel):
    """Estado inicial de uma sala recém-criada."""

    id: UUID
    code: str
    status: Literal["open", "generating"]
    occasion: str | None
    description: str | None
    mode: ConsensusMode | None
    created_at: datetime
    expires_at: datetime
    members: list[RoomMemberResponse]
    generation: RoomGenerationResponse | None = None
    vibe_summary: VibeSummaryResponse

    @field_validator("created_at", "expires_at")
    @classmethod
    def dates_are_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class PlaylistRunResponse(BaseModel):
    """Resposta de uma execução de geração de playlist."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    status: Literal["running", "completed", "failed"]
    error_message: str | None
    spotify_playlist_id: str | None
    spotify_playlist_url: str | None
    progress_stage: str
    progress_percent: int
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at")
    @classmethod
    def dates_are_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class TrackResultResponse(BaseModel):
    """Metadados e justificativas por faixa."""

    track_id: str | None
    name: str
    artist: str
    spotify_url: str | None
    reason: str
    contributed_by: list[str]
    is_bridge: bool = False


class MemberRepresentation(BaseModel):
    """Representação de um integrante na playlist final."""

    user_id: int
    display_name: str | None
    percentage: int


class RoomResultResponse(BaseModel):
    """Payload de resultado com métricas agregadas e sem vazar rejeições."""

    run_id: UUID
    playlist_url: str | None
    compatibility_score: int
    fairness_score: int
    discovery_percentage: int
    representation: list[MemberRepresentation]
    tracks: list[TrackResultResponse]
    why_items: list[str]
