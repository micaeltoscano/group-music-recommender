"""Add llm_context_json to playlist_runs (PB-17).

Revision ID: 0011_pb17_llm_context
Revises: 0010_pb16_run_metrics
Create Date: 2026-07-17
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011_pb17_llm_context"
down_revision: Union[str, None] = "0010_pb16_run_metrics"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("playlist_runs", sa.Column("llm_context_json", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("playlist_runs", "llm_context_json")
