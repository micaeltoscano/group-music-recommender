"""Modelos ORM do Vibe Check."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

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

    spotify_token: Mapped["SpotifyToken"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    sessions: Mapped[list["AppSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    hosted_music_sessions: Mapped[list["MusicSession"]] = relationship(
        back_populates="host",
        cascade="all, delete-orphan",
    )
    music_session_memberships: Mapped[list["MusicSessionMember"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    music_snapshots: Mapped[list["UserMusicSnapshot"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover - conveniência de debug
        return f"<User id={self.id} spotify_id={self.spotify_id!r}>"


class SpotifyToken(Base):
    """Armazena os tokens do Spotify do usuário (criptografados)."""
    __tablename__ = "spotify_tokens"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    access_token: Mapped[str] = mapped_column(Text, nullable=False)  # Armazenado criptografado
    refresh_token: Mapped[str] = mapped_column(Text, nullable=False) # Armazenado criptografado
    token_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    refresh_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    reauth_required_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
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
    session_token_hash: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="sessions")

    def __repr__(self) -> str:
        return f"<AppSession id={self.id} user_id={self.user_id}>"


class MusicSession(Base):
    """Sala efêmera criada por um host autenticado."""

    __tablename__ = "music_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(9), unique=True, nullable=False)
    host_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    occasion: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    mode: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    host: Mapped["User"] = relationship(back_populates="hosted_music_sessions")
    members: Mapped[list["MusicSessionMember"]] = relationship(
        back_populates="music_session",
        cascade="all, delete-orphan",
    )
    playlist_runs: Mapped[list["PlaylistRun"]] = relationship(
        back_populates="music_session",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover - conveniência de debug
        return f"<MusicSession id={self.id} code={self.code!r}>"


class MusicSessionMember(Base):
    """Vínculo entre uma sala e um integrante."""

    __tablename__ = "music_session_members"

    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("music_sessions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    music_session: Mapped["MusicSession"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="music_session_memberships")

    def __repr__(self) -> str:  # pragma: no cover - conveniência de debug
        return (
            f"<MusicSessionMember session_id={self.session_id} "
            f"user_id={self.user_id} role={self.role!r}>"
        )


class UserMusicSnapshot(Base):
    """Top tracks/artists temporários usados como entrada do motor."""

    __tablename__ = "user_music_snapshots"
    __table_args__ = (
        UniqueConstraint("user_id", "time_range", name="uq_music_snapshot_user_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    time_range: Mapped[str] = mapped_column(String(32), nullable=False)
    top_tracks_json: Mapped[list[dict[str, object]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    top_artists_json: Mapped[list[dict[str, object]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(back_populates="music_snapshots")

    def __repr__(self) -> str:  # pragma: no cover - conveniência de debug
        return (
            f"<UserMusicSnapshot id={self.id} user_id={self.user_id} "
            f"time_range={self.time_range!r}>"
        )


class PlaylistRun(Base):
    """Registro de uma execução de geração de playlist (PB-13)."""

    __tablename__ = "playlist_runs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("music_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="running")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    spotify_playlist_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    spotify_playlist_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    music_session: Mapped["MusicSession"] = relationship(back_populates="playlist_runs")
    tracks: Mapped[list["PlaylistRunTrack"]] = relationship(
        back_populates="playlist_run",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PlaylistRun id={self.id} session_id={self.session_id} status={self.status!r}>"


class PlaylistRunTrack(Base):
    """Faixa candidata resolvida e associada a uma execução de geração (PB-14)."""

    __tablename__ = "playlist_run_tracks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("playlist_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    candidate_id: Mapped[str] = mapped_column(String(255), nullable=False)
    spotify_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    spotify_uri: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    artist: Mapped[str] = mapped_column(Text, nullable=False)
    match_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    discard_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="matched")
    source: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON ou lista em string

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    
    playlist_run: Mapped["PlaylistRun"] = relationship(back_populates="tracks")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PlaylistRunTrack id={self.id} status={self.status!r}>"


class VibeCheckAnswer(Base):
    """Armazena as preferências derivadas de um usuário em uma sessão, extraídas do Vibe Check."""
    __tablename__ = "vibe_check_answers"
    __table_args__ = (
        UniqueConstraint("session_id", "user_id", name="uq_vibe_check_session_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("music_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    energy: Mapped[float] = mapped_column(Float, nullable=False)
    valence: Mapped[float] = mapped_column(Float, nullable=False)
    popularity: Mapped[float] = mapped_column(Float, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    
    music_session: Mapped["MusicSession"] = relationship()
    user: Mapped["User"] = relationship()

