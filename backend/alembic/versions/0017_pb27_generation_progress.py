"""Persist shared generation progress (PB-27).

Revision ID: 0017_pb27_generation_progress
Revises: 0016_pb24_subgroup_balance
Create Date: 2026-07-18
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0017_pb27_generation_progress"
down_revision: Union[str, None] = "0016_pb24_subgroup_balance"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "playlist_runs",
        sa.Column(
            "progress_stage",
            sa.String(length=64),
            server_default="starting",
            nullable=False,
        ),
    )
    op.add_column(
        "playlist_runs",
        sa.Column(
            "progress_percent",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("playlist_runs", "progress_percent")
    op.drop_column("playlist_runs", "progress_stage")
