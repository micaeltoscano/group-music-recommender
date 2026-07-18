"""Add the Last.fm track context cache (PB-18).

Revision ID: 0013_pb18_context_cache
Revises: 0012_pb17_context_rank
Create Date: 2026-07-18
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0013_pb18_context_cache"
down_revision: Union[str, None] = "0012_pb17_context_rank"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "track_context_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("spotify_track_id", sa.String(length=255), nullable=False),
        sa.Column("track_name", sa.Text(), nullable=False),
        sa.Column("artist_name", sa.Text(), nullable=False),
        sa.Column("lastfm_track_tags_json", sa.JSON(), nullable=False),
        sa.Column("lastfm_artist_tags_json", sa.JSON(), nullable=False),
        sa.Column("spotify_artist_genres_json", sa.JSON(), nullable=False),
        sa.Column("context_scores_json", sa.JSON(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_track_context_cache_spotify_track_id"),
        "track_context_cache",
        ["spotify_track_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_track_context_cache_spotify_track_id"),
        table_name="track_context_cache",
    )
    op.drop_table("track_context_cache")
