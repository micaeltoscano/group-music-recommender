"""Coleta e política de cache dos snapshots musicais do usuário."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from httpx import HTTPError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients import spotify_client
from app.config import settings
from app.db.models import UserMusicSnapshot


class MusicDataUnavailable(RuntimeError):
    """Indica falha externa controlada sem snapshot disponível."""


class MusicDataRateLimited(RuntimeError):
    """Indica rate limit sem cache utilizável como fallback."""

    def __init__(self, retry_after: int) -> None:
        self.retry_after = retry_after
        super().__init__("Spotify temporariamente indisponível por limite de requisições.")


@dataclass(frozen=True)
class SnapshotResult:
    snapshot: UserMusicSnapshot
    cached: bool
    stale: bool
    warning: str | None = None


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _is_fresh(snapshot: UserMusicSnapshot, now: datetime) -> bool:
    age = now - _as_utc(snapshot.fetched_at)
    return age < timedelta(days=settings.music_snapshot_ttl_days)


def _find_snapshot(
    db: Session,
    user_id: int,
    time_range: str,
) -> UserMusicSnapshot | None:
    return db.scalar(
        select(UserMusicSnapshot).where(
            UserMusicSnapshot.user_id == user_id,
            UserMusicSnapshot.time_range == time_range,
        )
    )


async def get_or_refresh_snapshot(
    db: Session,
    user_id: int,
    *,
    time_range: str,
    force_refresh: bool = False,
    now: datetime | None = None,
) -> SnapshotResult:
    """Reusa cache fresco ou coleta um snapshot novo de maneira atômica."""
    fetched_at = _as_utc(now or datetime.now(timezone.utc))
    snapshot = _find_snapshot(db, user_id, time_range)
    if snapshot is not None and _is_fresh(snapshot, fetched_at) and not force_refresh:
        return SnapshotResult(snapshot=snapshot, cached=True, stale=False)

    try:
        access_token = await spotify_client.get_valid_access_token(db, user_id)
        top_tracks = await spotify_client.get_top_tracks(
            access_token,
            time_range=time_range,
            limit=settings.spotify_top_items_limit,
        )
        top_artists = await spotify_client.get_top_artists(
            access_token,
            time_range=time_range,
            limit=settings.spotify_top_items_limit,
        )
    except spotify_client.SpotifyRateLimited as exc:
        db.rollback()
        snapshot = _find_snapshot(db, user_id, time_range)
        if snapshot is not None:
            stale = not _is_fresh(snapshot, fetched_at)
            return SnapshotResult(
                snapshot=snapshot,
                cached=True,
                stale=stale,
                warning=(
                    "Spotify limitou temporariamente as requisições; "
                    "o último snapshot disponível foi reutilizado."
                ),
            )
        raise MusicDataRateLimited(exc.retry_after) from exc
    except spotify_client.ReauthenticationRequired:
        raise
    except (HTTPError, spotify_client.SpotifyInvalidResponse) as exc:
        db.rollback()
        raise MusicDataUnavailable("Não foi possível coletar os dados musicais agora.") from exc

    if snapshot is None:
        snapshot = UserMusicSnapshot(
            user_id=user_id,
            time_range=time_range,
            top_tracks_json=top_tracks,
            top_artists_json=top_artists,
            fetched_at=fetched_at,
        )
        db.add(snapshot)
    else:
        snapshot.top_tracks_json = top_tracks
        snapshot.top_artists_json = top_artists
        snapshot.fetched_at = fetched_at

    db.commit()
    db.refresh(snapshot)
    warning = None
    if not top_tracks and not top_artists:
        warning = "O Spotify não retornou top tracks nem top artists para este usuário."
    return SnapshotResult(snapshot=snapshot, cached=False, stale=False, warning=warning)
