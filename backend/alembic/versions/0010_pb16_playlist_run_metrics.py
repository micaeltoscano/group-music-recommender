"""Add compatibility/fairness scores and explanation to playlist_runs (PB-16).

Revision ID: 0010_pb16_run_metrics
Revises: 0009_pb15_playlist
Create Date: 2026-07-17
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010_pb16_run_metrics"
down_revision: Union[str, None] = "0009_pb15_playlist"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("playlist_runs", sa.Column("compatibility_score", sa.Integer(), nullable=True))
    op.add_column("playlist_runs", sa.Column("fairness_score", sa.Integer(), nullable=True))
    op.add_column("playlist_runs", sa.Column("explanation_json", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("playlist_runs", "explanation_json")
    op.drop_column("playlist_runs", "fairness_score")
    op.drop_column("playlist_runs", "compatibility_score")
