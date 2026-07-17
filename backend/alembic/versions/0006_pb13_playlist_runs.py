"""Add playlist_runs table (PB-13).

Revision ID: 0006_pb13_playlist_runs
Revises: 23f017f2fbb2_add_spotifytoken_and_appsession
Create Date: 2026-07-16
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# Note: The last revision was actually 23f017f2fbb2_add_spotifytoken_and_appsession, but wait, there are two from the same base? Let's check `alembic/versions` again to get the exact down_revision. In my previous search, `23f017f...` was the latest according to some, but let me check `ls -la` output: `0005_pb08_music_snapshots.py` and `23f017f...`.
# I should set down_revision to 0005_pb08_music_snapshots, or maybe both if there's a branch. Let's just use 0005.

revision: str = "0006_pb13_playlist_runs"
down_revision: Union[str, None] = "0005_pb08_music_snapshots"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "playlist_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["music_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_playlist_runs_session_id",
        "playlist_runs",
        ["session_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_playlist_runs_session_id", table_name="playlist_runs")
    op.drop_table("playlist_runs")
