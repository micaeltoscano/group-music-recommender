"""Add post-playlist feedback tables (PB-20).

Revision ID: 0014_pb20_feedback
Revises: 0013_pb18_context_cache
Create Date: 2026-07-18
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0014_pb20_feedback"
down_revision: Union[str, None] = "0013_pb18_context_cache"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "member_track_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("playlist_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("spotify_track_id", sa.String(length=255), nullable=False),
        sa.Column("liked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("disliked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("more_like_this", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("never_again", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["playlist_run_id"], ["playlist_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "playlist_run_id",
            "spotify_track_id",
            name="uq_member_track_feedback_user_run_track",
        ),
    )
    op.create_index(
        op.f("ix_member_track_feedback_playlist_run_id"),
        "member_track_feedback",
        ["playlist_run_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_member_track_feedback_user_id"),
        "member_track_feedback",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "playlist_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("playlist_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("representation_score", sa.Integer(), nullable=False),
        sa.Column("satisfaction_score", sa.Integer(), nullable=False),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "representation_score BETWEEN 0 AND 5",
            name="ck_playlist_feedback_representation_score",
        ),
        sa.CheckConstraint(
            "satisfaction_score BETWEEN 0 AND 5",
            name="ck_playlist_feedback_satisfaction_score",
        ),
        sa.ForeignKeyConstraint(["playlist_run_id"], ["playlist_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "playlist_run_id", name="uq_playlist_feedback_user_run"
        ),
    )
    op.create_index(
        op.f("ix_playlist_feedback_playlist_run_id"),
        "playlist_feedback",
        ["playlist_run_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_playlist_feedback_user_id"),
        "playlist_feedback",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_playlist_feedback_user_id"), table_name="playlist_feedback")
    op.drop_index(
        op.f("ix_playlist_feedback_playlist_run_id"), table_name="playlist_feedback"
    )
    op.drop_table("playlist_feedback")
    op.drop_index(
        op.f("ix_member_track_feedback_user_id"), table_name="member_track_feedback"
    )
    op.drop_index(
        op.f("ix_member_track_feedback_playlist_run_id"),
        table_name="member_track_feedback",
    )
    op.drop_table("member_track_feedback")
