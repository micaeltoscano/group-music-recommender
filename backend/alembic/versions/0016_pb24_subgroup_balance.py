"""Persist subgroup balancing usage (PB-24).

Revision ID: 0016_pb24_subgroup_balance
Revises: 0015_pb23_bridge_tracks
Create Date: 2026-07-18
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0016_pb24_subgroup_balance"
down_revision: Union[str, None] = "0015_pb23_bridge_tracks"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "playlist_runs",
        sa.Column(
            "subgroup_balancing_applied",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("playlist_runs", "subgroup_balancing_applied")
