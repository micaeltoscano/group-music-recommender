"""Modelos ORM.

Escopo PB-01: apenas a tabela fundacional `users`, suficiente para exercitar a
migração inicial (upgrade/downgrade) e demonstrar a integração com o Postgres.
As demais tabelas do modelo de dados (sessões, salas, snapshots, etc.) serão
adicionadas nas histórias correspondentes.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, func, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
import uuid


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

    spotify_token: Mapped["SpotifyToken"] = relationship(back_populates="user", cascade="all, delete-orphan")
    sessions: Mapped[list["AppSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover - conveniência de debug
        return f"<User id={self.id} spotify_id={self.spotify_id!r}>"


class SpotifyToken(Base):
    """Armazena os tokens do Spotify do usuário (criptografados)."""
    __tablename__ = "spotify_tokens"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    access_token: Mapped[str] = mapped_column(Text, nullable=False)  # Armazenado criptografado
    refresh_token: Mapped[str] = mapped_column(Text, nullable=False) # Armazenado criptografado
    token_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    refresh_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reauth_required_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scopes: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="spotify_token")

    def __repr__(self) -> str:
        return f"<SpotifyToken user_id={self.user_id}>"


class AppSession(Base):
    """Sessões do aplicativo frontend via cookie."""
    __tablename__ = "app_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="sessions")

    def __repr__(self) -> str:
        return f"<AppSession id={self.id} user_id={self.user_id}>"
