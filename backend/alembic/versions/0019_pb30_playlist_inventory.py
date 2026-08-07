"""Add minimal per-user playlist inventory (PB-30).

Revision ID: 0019_pb30_playlist_inventory
Revises: 0018_pb29_vibe_status
Create Date: 2026-07-31
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0019_pb30_playlist_inventory"
down_revision: Union[str, None] = "0018_pb29_vibe_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_playlist_inventory",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("spotify_playlist_id", sa.String(length=255), nullable=False),
        sa.Column("access_type", sa.String(length=16), nullable=False),
        sa.Column("tracks_total", sa.Integer(), nullable=False),
        sa.Column("snapshot_id", sa.String(length=255), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "access_type IN ('owned', 'collaborative')",
            name="ck_playlist_inventory_access_type",
        ),
        sa.CheckConstraint(
            "tracks_total >= 0",
            name="ck_playlist_inventory_tracks_total",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "spotify_playlist_id",
            name="uq_playlist_inventory_user_playlist",
        ),
    )
    op.create_index(
        "ix_user_playlist_inventory_user_id",
        "user_playlist_inventory",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_user_playlist_inventory_user_id",
        table_name="user_playlist_inventory",
    )
    op.drop_table("user_playlist_inventory")
