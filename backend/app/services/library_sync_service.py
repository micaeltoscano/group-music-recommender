"""Sincronização incremental e resiliente da biblioteca musical (PB-32)."""

from __future__ import annotations

import asyncio
import weakref
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.clients import spotify_client
from app.config import settings
from app.db.models import (
    UserMusicLibraryPlaylistState,
    UserMusicLibrarySnapshot,
    UserMusicLibrarySource,
    UserMusicLibraryTrack,
)
from app.engine.music_library import TOP_TIME_RANGES
from app.services.music_library_service import rebuild_music_library
from app.services.music_service import (
    MusicDataRateLimited,
    MusicDataUnavailable,
    get_or_refresh_snapshot,
)
from app.services.playlist_inventory_service import refresh_playlist_inventory


class LibrarySyncUnavailable(RuntimeError):
    """Falha recuperável sem biblioteca anterior disponível."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__("Não foi possível sincronizar a biblioteca musical agora.")


class LibrarySyncRateLimited(LibrarySyncUnavailable):
    def __init__(self, retry_after: int) -> None:
        self.retry_after = retry_after
        super().__init__("RATE_LIMITED")


class LibrarySyncQuotaExceeded(LibrarySyncUnavailable):
    def __init__(self) -> None:
        super().__init__("QUOTA_EXCEEDED")


@dataclass(frozen=True)
class LibrarySyncResult:
    snapshot: UserMusicLibrarySnapshot
    cached: bool
    stale: bool
    warning_code: str | None = None
    retry_after: int | None = None


_LOOP_USER_LOCKS: weakref.WeakKeyDictionary[
    asyncio.AbstractEventLoop, dict[int, asyncio.Lock]
] = weakref.WeakKeyDictionary()
_POSTGRES_LOCK_NAMESPACE = 1_442_928_178


def _loop_user_lock(user_id: int) -> asyncio.Lock:
    """Mantém locks somente durante a vida do event loop que os criou."""
    loop = asyncio.get_running_loop()
    locks = _LOOP_USER_LOCKS.setdefault(loop, {})
    return locks.setdefault(user_id, asyncio.Lock())


@asynccontextmanager
async def _user_sync_lock(db: Session, user_id: int):
    """Serializa no processo e, em PostgreSQL, também entre workers."""
    local_lock = _loop_user_lock(user_id)
    async with local_lock:
        uses_postgres = db.get_bind().dialect.name == "postgresql"
        if uses_postgres:
            db.execute(
                text("SELECT pg_advisory_lock(:namespace, :user_id)"),
                {"namespace": _POSTGRES_LOCK_NAMESPACE, "user_id": user_id},
            )
        try:
            yield
        finally:
            if uses_postgres:
                db.execute(
                    text("SELECT pg_advisory_unlock(:namespace, :user_id)"),
                    {"namespace": _POSTGRES_LOCK_NAMESPACE, "user_id": user_id},
                )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _find_library(db: Session, user_id: int) -> UserMusicLibrarySnapshot | None:
    return (
        db.query(UserMusicLibrarySnapshot)
        .filter(UserMusicLibrarySnapshot.user_id == user_id)
        .one_or_none()
    )


def _is_fresh(snapshot: UserMusicLibrarySnapshot, now: datetime) -> bool:
    return now - _as_utc(snapshot.built_at) < timedelta(days=settings.music_library_ttl_days)


def _track_payload(track: UserMusicLibraryTrack) -> dict[str, object]:
    artists: list[dict[str, str]] = []
    if track.artist_id or track.artist_name:
        artists.append(
            {
                "id": track.artist_id or "",
                "name": track.artist_name or "",
            }
        )
    return {
        "id": track.spotify_track_id,
        "uri": track.spotify_uri,
        "name": track.track_name,
        "artists": artists,
    }


def _reusable_playlist_tracks(
    db: Session,
    user_id: int,
    snapshot: UserMusicLibrarySnapshot,
) -> dict[str, list[dict[str, object]]]:
    states = {
        state.spotify_playlist_id: state
        for state in db.query(UserMusicLibraryPlaylistState)
        .filter(UserMusicLibraryPlaylistState.snapshot_id == snapshot.id)
        .all()
    }
    rows = (
        db.query(UserMusicLibrarySource, UserMusicLibraryTrack)
        .join(
            UserMusicLibraryTrack,
            UserMusicLibrarySource.library_track_id == UserMusicLibraryTrack.id,
        )
        .filter(
            UserMusicLibraryTrack.user_id == user_id,
            UserMusicLibrarySource.source_type == "playlist",
        )
        .all()
    )
    by_playlist: dict[str, list[tuple[int, dict[str, object]]]] = {
        playlist_id: [] for playlist_id in states
    }
    for source, track in rows:
        by_playlist.setdefault(source.source_ref, []).append(
            (source.source_rank, _track_payload(track))
        )

    result: dict[str, list[dict[str, object]]] = {}
    for playlist_id, ranked in by_playlist.items():
        if not ranked:
            result[playlist_id] = []
            continue
        maximum_rank = max(rank for rank, _track in ranked)
        placeholders: list[dict[str, object]] = [{} for _ in range(maximum_rank)]
        for rank, payload in ranked:
            placeholders[rank - 1] = payload
        result[playlist_id] = placeholders
    return result


async def _download_changed_playlists(
    access_token: str,
    playlist_ids: list[str],
) -> tuple[dict[str, list[dict]], set[str]]:
    semaphore = asyncio.Semaphore(settings.music_library_external_concurrency)
    forbidden: set[str] = set()

    async def download(playlist_id: str) -> tuple[str, list[dict]]:
        async with semaphore:
            try:
                tracks = await spotify_client.get_playlist_tracks(
                    access_token,
                    playlist_id,
                    limit=50,
                )
            except spotify_client.SpotifyAccessForbidden:
                forbidden.add(playlist_id)
                return playlist_id, []
            return playlist_id, tracks

    tasks = [asyncio.create_task(download(playlist_id)) for playlist_id in playlist_ids]
    try:
        downloaded = await asyncio.gather(*tasks)
    except Exception:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise
    return dict(downloaded), forbidden


def _record_failure(
    db: Session,
    snapshot: UserMusicLibrarySnapshot,
    *,
    attempted_at: datetime,
    code: str,
    retry_after: int | None = None,
) -> None:
    snapshot.last_sync_attempt_at = attempted_at
    snapshot.last_sync_error_code = code
    snapshot.last_sync_retry_after = retry_after
    db.commit()


async def sync_music_library(
    db: Session,
    user_id: int,
    *,
    force_refresh: bool = False,
    now: datetime | None = None,
) -> LibrarySyncResult:
    """Sincroniza no máximo a cada sete dias e nunca promove estado parcial."""
    attempted_at = _as_utc(now or datetime.now(timezone.utc))
    current = _find_library(db, user_id)
    if current is not None and _is_fresh(current, attempted_at) and not force_refresh:
        return LibrarySyncResult(snapshot=current, cached=True, stale=False)

    async with _user_sync_lock(db, user_id):
        db.expire_all()
        current = _find_library(db, user_id)
        if current is not None and _is_fresh(current, attempted_at) and not force_refresh:
            return LibrarySyncResult(snapshot=current, cached=True, stale=False)

        prior_states = {
            state.spotify_playlist_id: state.playlist_snapshot_id
            for state in (
                db.query(UserMusicLibraryPlaylistState)
                .filter(
                    UserMusicLibraryPlaylistState.snapshot_id == current.id
                    if current is not None
                    else False
                )
                .all()
            )
        }
        reusable = (
            _reusable_playlist_tracks(db, user_id, current) if current is not None else {}
        )

        try:
            for time_range in TOP_TIME_RANGES:
                await get_or_refresh_snapshot(db, user_id, time_range=time_range, now=attempted_at)

            inventory_result = await refresh_playlist_inventory(
                db,
                user_id,
                now=attempted_at,
                verify_content_access=False,
            )
            changed = [
                item.spotify_playlist_id
                for item in inventory_result.items
                if prior_states.get(item.spotify_playlist_id) != item.snapshot_id
            ]
            playlist_tracks = {
                item.spotify_playlist_id: reusable.get(item.spotify_playlist_id, [])
                for item in inventory_result.items
                if item.spotify_playlist_id not in changed
            }
            if changed:
                access_token = await spotify_client.get_valid_access_token(
                    db,
                    user_id,
                    required_scopes=spotify_client.PLAYLIST_INVENTORY_SCOPES,
                )
                downloaded, _forbidden = await _download_changed_playlists(
                    access_token,
                    changed,
                )
                playlist_tracks.update(downloaded)

            promoted = rebuild_music_library(
                db,
                user_id,
                playlist_tracks_by_id=playlist_tracks,
                built_at=attempted_at,
            )
            promoted.last_sync_attempt_at = attempted_at
            promoted.last_sync_error_code = None
            promoted.last_sync_retry_after = None
            db.commit()
            db.refresh(promoted)
            db.expire(promoted, ["tracks", "playlist_states"])
            return LibrarySyncResult(snapshot=promoted, cached=False, stale=False)
        except (spotify_client.SpotifyRateLimited, MusicDataRateLimited) as exc:
            retry_after = exc.retry_after
            if current is None:
                raise LibrarySyncRateLimited(retry_after) from exc
            db.rollback()
            current = _find_library(db, user_id)
            assert current is not None
            _record_failure(
                db,
                current,
                attempted_at=attempted_at,
                code="RATE_LIMITED",
                retry_after=retry_after,
            )
            return LibrarySyncResult(
                snapshot=current,
                cached=True,
                stale=not _is_fresh(current, attempted_at),
                warning_code="RATE_LIMITED",
                retry_after=retry_after,
            )
        except spotify_client.SpotifyQuotaExceeded as exc:
            if current is None:
                raise LibrarySyncQuotaExceeded() from exc
            db.rollback()
            current = _find_library(db, user_id)
            assert current is not None
            _record_failure(db, current, attempted_at=attempted_at, code="QUOTA_EXCEEDED")
            return LibrarySyncResult(
                snapshot=current,
                cached=True,
                stale=not _is_fresh(current, attempted_at),
                warning_code="QUOTA_EXCEEDED",
            )
        except (
            spotify_client.ReauthenticationRequired,
            spotify_client.SpotifyAPIUnavailable,
            spotify_client.SpotifyInvalidResponse,
            MusicDataUnavailable,
        ) as exc:
            code = (
                "REAUTH_REQUIRED"
                if isinstance(exc, spotify_client.ReauthenticationRequired)
                else "SYNC_UNAVAILABLE"
            )
            if current is None:
                raise LibrarySyncUnavailable(code) from exc
            db.rollback()
            current = _find_library(db, user_id)
            assert current is not None
            _record_failure(db, current, attempted_at=attempted_at, code=code)
            return LibrarySyncResult(
                snapshot=current,
                cached=True,
                stale=not _is_fresh(current, attempted_at),
                warning_code=code,
            )
