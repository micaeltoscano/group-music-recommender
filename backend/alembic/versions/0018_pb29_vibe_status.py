"""Persist answered/skipped Vibe Check state (PB-29).

Revision ID: 0018_pb29_vibe_status
Revises: 0017_pb27_generation_progress
Create Date: 2026-07-18
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0018_pb29_vibe_status"
down_revision: Union[str, None] = "0017_pb27_generation_progress"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "vibe_check_answers",
        sa.Column("status", sa.String(length=16), server_default="answered", nullable=False),
    )
    op.alter_column("vibe_check_answers", "energy", existing_type=sa.Float(), nullable=True)
    op.alter_column("vibe_check_answers", "valence", existing_type=sa.Float(), nullable=True)
    op.alter_column("vibe_check_answers", "popularity", existing_type=sa.Float(), nullable=True)


def downgrade() -> None:
    op.execute(
        "UPDATE vibe_check_answers "
        "SET energy = 0.5, valence = 0.5, popularity = 0.5 "
        "WHERE status = 'skipped'"
    )
    op.alter_column("vibe_check_answers", "popularity", existing_type=sa.Float(), nullable=False)
    op.alter_column("vibe_check_answers", "valence", existing_type=sa.Float(), nullable=False)
    op.alter_column("vibe_check_answers", "energy", existing_type=sa.Float(), nullable=False)
    op.drop_column("vibe_check_answers", "status")
