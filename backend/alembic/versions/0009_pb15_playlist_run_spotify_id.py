"""Add spotify_playlist_id and url to playlist_runs (PB-15).

Revision ID: 0009_pb15_playlist_run_spotify_id
Revises: 0008_pb14_playlist_run_tracks
Create Date: 2026-07-17
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009_pb15_playlist_run_spotify_id"
down_revision: Union[str, None] = "0008_pb14_playlist_run_tracks"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("playlist_runs", sa.Column("spotify_playlist_id", sa.String(length=255), nullable=True))
    op.add_column("playlist_runs", sa.Column("spotify_playlist_url", sa.String(length=1024), nullable=True))


def downgrade() -> None:
    op.drop_column("playlist_runs", "spotify_playlist_url")
    op.drop_column("playlist_runs", "spotify_playlist_id")
