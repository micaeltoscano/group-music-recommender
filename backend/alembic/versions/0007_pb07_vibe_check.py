"""Add vibe_check_answers table (PB-07).

Revision ID: 0007_pb07_vibe_check
Revises: 0006_pb13_playlist_runs
Create Date: 2026-07-17
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007_pb07_vibe_check"
down_revision: Union[str, None] = "0006_pb13_playlist_runs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vibe_check_answers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("energy", sa.Float(), nullable=False),
        sa.Column("valence", sa.Float(), nullable=False),
        sa.Column("popularity", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["music_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "user_id", name="uq_vibe_check_session_user"),
    )
    op.create_index(
        "ix_vibe_check_answers_session_id",
        "vibe_check_answers",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        "ix_vibe_check_answers_user_id",
        "vibe_check_answers",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_vibe_check_answers_user_id", table_name="vibe_check_answers")
    op.drop_index("ix_vibe_check_answers_session_id", table_name="vibe_check_answers")
    op.drop_table("vibe_check_answers")
