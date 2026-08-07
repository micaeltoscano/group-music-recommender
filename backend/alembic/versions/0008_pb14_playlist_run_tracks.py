"""Add playlist_run_tracks table (PB-14).

Revision ID: 0008_pb14_playlist_run_tracks
Revises: 0007_pb07_vibe_check
Create Date: 2026-07-17
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008_pb14_playlist_run_tracks"
down_revision: Union[str, None] = "0007_pb07_vibe_check"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "playlist_run_tracks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("candidate_id", sa.String(length=255), nullable=False),
        sa.Column("spotify_id", sa.String(length=255), nullable=True),
        sa.Column("spotify_uri", sa.String(length=255), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("artist", sa.Text(), nullable=False),
        sa.Column("match_confidence", sa.Float(), nullable=True),
        sa.Column("discard_reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("source", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["playlist_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_playlist_run_tracks_run_id",
        "playlist_run_tracks",
        ["run_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_playlist_run_tracks_run_id", table_name="playlist_run_tracks")
    op.drop_table("playlist_run_tracks")
