"""Preserve contextual ranking order for playlist tracks (PB-17).

Revision ID: 0012_pb17_context_rank
Revises: 0011_pb17_llm_context
Create Date: 2026-07-17
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0012_pb17_context_rank"
down_revision: Union[str, None] = "0011_pb17_llm_context"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "playlist_run_tracks",
        sa.Column("selection_rank", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("playlist_run_tracks", "selection_rank")
