"""Add cached user music snapshots (PB-08).

Revision ID: 0005_pb08_music_snapshots
Revises: 0004_pb06_context_mode
Create Date: 2026-07-16
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_pb08_music_snapshots"
down_revision: Union[str, None] = "0004_pb06_context_mode"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_music_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("time_range", sa.String(length=32), nullable=False),
        sa.Column("top_tracks_json", sa.JSON(), nullable=False),
        sa.Column("top_artists_json", sa.JSON(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "time_range",
            name="uq_music_snapshot_user_range",
        ),
    )
    op.create_index(
        "ix_user_music_snapshots_user_id",
        "user_music_snapshots",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_user_music_snapshots_user_id",
        table_name="user_music_snapshots",
    )
    op.drop_table("user_music_snapshots")
