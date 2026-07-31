"""Add incremental sync metadata to the music library (PB-32).

Revision ID: 0021_pb32_library_sync
Revises: 0020_pb31_music_library
Create Date: 2026-07-31
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0021_pb32_library_sync"
down_revision: Union[str, None] = "0020_pb31_music_library"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_music_library_snapshots",
        sa.Column("last_sync_attempt_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "user_music_library_snapshots",
        sa.Column("last_sync_error_code", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "user_music_library_snapshots",
        sa.Column("last_sync_retry_after", sa.Integer(), nullable=True),
    )
    op.add_column(
        "user_music_library_sources",
        sa.Column("playlist_snapshot_id", sa.String(length=255), nullable=True),
    )
    op.create_table(
        "user_music_library_playlist_states",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("snapshot_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("spotify_playlist_id", sa.String(length=255), nullable=False),
        sa.Column("playlist_snapshot_id", sa.String(length=255), nullable=False),
        sa.Column("access_type", sa.String(length=16), nullable=False),
        sa.Column("tracks_total", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "access_type IN ('owned', 'collaborative')",
            name="ck_music_library_playlist_state_access",
        ),
        sa.CheckConstraint(
            "tracks_total >= 0",
            name="ck_music_library_playlist_state_total",
        ),
        sa.ForeignKeyConstraint(
            ["snapshot_id"], ["user_music_library_snapshots.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "snapshot_id",
            "spotify_playlist_id",
            name="uq_music_library_snapshot_playlist",
        ),
    )
    op.create_index(
        "ix_user_music_library_playlist_states_snapshot_id",
        "user_music_library_playlist_states",
        ["snapshot_id"],
        unique=False,
    )
    op.create_index(
        "ix_user_music_library_playlist_states_user_id",
        "user_music_library_playlist_states",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_user_music_library_playlist_states_user_id",
        table_name="user_music_library_playlist_states",
    )
    op.drop_index(
        "ix_user_music_library_playlist_states_snapshot_id",
        table_name="user_music_library_playlist_states",
    )
    op.drop_table("user_music_library_playlist_states")
    op.drop_column("user_music_library_sources", "playlist_snapshot_id")
    op.drop_column("user_music_library_snapshots", "last_sync_retry_after")
    op.drop_column("user_music_library_snapshots", "last_sync_error_code")
    op.drop_column("user_music_library_snapshots", "last_sync_attempt_at")
