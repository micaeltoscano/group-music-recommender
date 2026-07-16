"""Contratos públicos dos snapshots musicais."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, field_validator

MusicTimeRange = Literal["short_term", "medium_term", "long_term"]


class MusicSnapshotResponse(BaseModel):
    snapshot_id: UUID
    user_id: int
    time_range: MusicTimeRange
    top_tracks: list[dict[str, Any]]
    top_artists: list[dict[str, Any]]
    fetched_at: datetime
    cached: bool
    stale: bool
    warning: str | None = None

    @field_validator("fetched_at")
    @classmethod
    def fetched_at_is_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
