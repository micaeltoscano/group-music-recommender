"""Contratos HTTP para o feedback pós-playlist (PB-20)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TrackFeedbackRequest(BaseModel):
    liked: bool = False
    disliked: bool = False
    more_like_this: bool = False
    never_again: bool = False


class TrackFeedbackResponse(TrackFeedbackRequest):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: int
    playlist_run_id: UUID
    spotify_track_id: str
    created_at: datetime
    updated_at: datetime
    future_use_notice: str


class PlaylistFeedbackRequest(BaseModel):
    representation_score: int = Field(ge=0, le=5)
    satisfaction_score: int = Field(ge=0, le=5)
    comments: str | None = Field(default=None, max_length=2000)


class PlaylistFeedbackResponse(PlaylistFeedbackRequest):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: int
    playlist_run_id: UUID
    created_at: datetime
    updated_at: datetime
    future_use_notice: str
