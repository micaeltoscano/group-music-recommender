"""Add bounded per-user music library with normalized sources (PB-31).

Revision ID: 0020_pb31_music_library
Revises: 0019_pb30_playlist_inventory
Create Date: 2026-07-31
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0020_pb31_music_library"
down_revision: Union[str, None] = "0019_pb30_playlist_inventory"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_music_library_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("track_count", sa.Integer(), nullable=False),
        sa.Column("built_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "track_count >= 0 AND track_count <= 500",
            name="ck_music_library_snapshot_track_count",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_music_library_snapshot_user"),
    )
    op.create_index(
        "ix_user_music_library_snapshots_user_id",
        "user_music_library_snapshots",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "user_music_library_tracks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("snapshot_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("spotify_track_id", sa.String(length=255), nullable=False),
        sa.Column("spotify_uri", sa.String(length=512), nullable=False),
        sa.Column("track_name", sa.Text(), nullable=True),
        sa.Column("artist_id", sa.String(length=255), nullable=True),
        sa.Column("artist_name", sa.Text(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "position >= 1 AND position <= 500",
            name="ck_music_library_track_position",
        ),
        sa.ForeignKeyConstraint(
            ["snapshot_id"],
            ["user_music_library_snapshots.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "snapshot_id",
            "position",
            name="uq_music_library_snapshot_position",
        ),
        sa.UniqueConstraint(
            "user_id",
            "spotify_track_id",
            name="uq_music_library_user_track",
        ),
    )
    op.create_index(
        "ix_user_music_library_tracks_snapshot_id",
        "user_music_library_tracks",
        ["snapshot_id"],
        unique=False,
    )
    op.create_index(
        "ix_user_music_library_tracks_user_id",
        "user_music_library_tracks",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "user_music_library_sources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("library_track_id", sa.Uuid(), nullable=False),
        sa.Column("source_type", sa.String(length=16), nullable=False),
        sa.Column("source_ref", sa.String(length=255), nullable=False),
        sa.Column("source_key", sa.String(length=512), nullable=False),
        sa.Column("source_rank", sa.Integer(), nullable=False),
        sa.Column("access_type", sa.String(length=16), nullable=True),
        sa.CheckConstraint(
            "(source_type = 'top' AND access_type IS NULL) OR "
            "(source_type = 'playlist' AND access_type IN ('owned', 'collaborative'))",
            name="ck_music_library_source_access",
        ),
        sa.CheckConstraint(
            "source_rank >= 1",
            name="ck_music_library_source_rank",
        ),
        sa.CheckConstraint(
            "source_type IN ('top', 'playlist')",
            name="ck_music_library_source_type",
        ),
        sa.ForeignKeyConstraint(
            ["library_track_id"],
            ["user_music_library_tracks.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "library_track_id",
            "source_key",
            name="uq_music_library_track_source",
        ),
    )
    op.create_index(
        "ix_user_music_library_sources_library_track_id",
        "user_music_library_sources",
        ["library_track_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_user_music_library_sources_library_track_id",
        table_name="user_music_library_sources",
    )
    op.drop_table("user_music_library_sources")
    op.drop_index(
        "ix_user_music_library_tracks_user_id",
        table_name="user_music_library_tracks",
    )
    op.drop_index(
        "ix_user_music_library_tracks_snapshot_id",
        table_name="user_music_library_tracks",
    )
    op.drop_table("user_music_library_tracks")
    op.drop_index(
        "ix_user_music_library_snapshots_user_id",
        table_name="user_music_library_snapshots",
    )
    op.drop_table("user_music_library_snapshots")
