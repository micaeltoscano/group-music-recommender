"""initial: cria a tabela users

Migração inicial da fundação técnica (PB-01). Cria apenas a tabela fundacional
`users`, suficiente para validar upgrade/downgrade e a conexão com o Postgres.

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-12

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("spotify_id", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("image_url", sa.String(length=1024), nullable=True),
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
    )
    op.create_index("ix_users_spotify_id", "users", ["spotify_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_spotify_id", table_name="users")
    op.drop_table("users")
