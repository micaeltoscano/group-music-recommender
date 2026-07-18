"""Mark bridge tracks in playlist results (PB-23).

Revision ID: 0015_pb23_bridge_tracks
Revises: 0014_pb20_feedback
Create Date: 2026-07-18
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0015_pb23_bridge_tracks"
down_revision: Union[str, None] = "0014_pb20_feedback"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "playlist_run_tracks",
        sa.Column("is_bridge", sa.Boolean(), server_default=sa.false(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("playlist_run_tracks", "is_bridge")
