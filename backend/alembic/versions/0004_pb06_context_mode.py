"""Add room context and consensus mode (PB-06).

Revision ID: 0004_pb06_context_mode
Revises: 0003_pb04_rooms
Create Date: 2026-07-16
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_pb06_context_mode"
down_revision: Union[str, None] = "0003_pb04_rooms"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "music_sessions",
        sa.Column("occasion", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "music_sessions",
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.add_column(
        "music_sessions",
        sa.Column("mode", sa.String(length=32), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("music_sessions", "mode")
    op.drop_column("music_sessions", "description")
    op.drop_column("music_sessions", "occasion")
