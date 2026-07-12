"""Modelos ORM.

Escopo PB-01: apenas a tabela fundacional `users`, suficiente para exercitar a
migração inicial (upgrade/downgrade) e demonstrar a integração com o Postgres.
As demais tabelas do modelo de dados (sessões, salas, snapshots, etc.) serão
adicionadas nas histórias correspondentes.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    """Usuário identificado pela conta Spotify.

    Os campos de autenticação/token pertencem a histórias futuras (PB-02) e não
    fazem parte desta tabela na fundação técnica.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    spotify_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:  # pragma: no cover - conveniência de debug
        return f"<User id={self.id} spotify_id={self.spotify_id!r}>"
