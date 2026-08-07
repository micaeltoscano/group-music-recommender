"""Rotas autenticadas de coleta e cache de dados musicais."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.clients.spotify_client import ReauthenticationRequired
from app.db.session import get_db
from app.schemas.music import MusicLibraryStatusResponse, MusicSnapshotResponse, MusicTimeRange
from app.services.library_application_service import music_library_status
from app.services.library_sync_service import (
    LibrarySyncQuotaExceeded,
    LibrarySyncRateLimited,
    LibrarySyncUnavailable,
    sync_music_library,
)
from app.services.music_service import (
    MusicDataRateLimited,
    MusicDataUnavailable,
    SnapshotResult,
    get_or_refresh_snapshot,
)

router = APIRouter()


@router.get("/music-library", response_model=MusicLibraryStatusResponse)
def read_my_music_library(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MusicLibraryStatusResponse:
    return music_library_status(db, current_user["id"])


@router.post("/refresh-music-library", response_model=MusicLibraryStatusResponse)
async def refresh_my_music_library(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MusicLibraryStatusResponse:
    try:
        await sync_music_library(db, current_user["id"])
    except LibrarySyncRateLimited as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": exc.code, "message": "Spotify temporariamente limitado."},
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc
    except LibrarySyncQuotaExceeded as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": exc.code, "message": "Quota Spotify indisponível no momento."},
        ) from exc
    except LibrarySyncUnavailable as exc:
        http_status = (
            status.HTTP_401_UNAUTHORIZED
            if exc.code == "REAUTH_REQUIRED"
            else status.HTTP_502_BAD_GATEWAY
        )
        raise HTTPException(
            status_code=http_status,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc
    return music_library_status(db, current_user["id"])


def _snapshot_response(result: SnapshotResult) -> MusicSnapshotResponse:
    snapshot = result.snapshot
    return MusicSnapshotResponse(
        snapshot_id=snapshot.id,
        user_id=snapshot.user_id,
        time_range=snapshot.time_range,
        top_tracks=snapshot.top_tracks_json,
        top_artists=snapshot.top_artists_json,
        fetched_at=snapshot.fetched_at,
        cached=result.cached,
        stale=result.stale,
        warning=result.warning,
    )


async def _load_snapshot(
    db: Session,
    user_id: int,
    *,
    time_range: MusicTimeRange,
    force_refresh: bool,
) -> MusicSnapshotResponse:
    try:
        result = await get_or_refresh_snapshot(
            db,
            user_id,
            time_range=time_range,
            force_refresh=force_refresh,
        )
    except ReauthenticationRequired as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Autorize novamente sua conta Spotify.",
                "reauth_required": True,
                "login_url": "/auth/login",
            },
        ) from exc
    except MusicDataRateLimited as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Spotify temporariamente limitado. Tente novamente mais tarde.",
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc
    except MusicDataUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    return _snapshot_response(result)


@router.get("/top", response_model=MusicSnapshotResponse)
async def read_my_top_items(
    time_range: MusicTimeRange = "medium_term",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MusicSnapshotResponse:
    """Retorna o snapshot atual, coletando-o quando ausente ou vencido."""
    return await _load_snapshot(
        db,
        current_user["id"],
        time_range=time_range,
        force_refresh=False,
    )


@router.post("/refresh-music-snapshot", response_model=MusicSnapshotResponse)
async def refresh_my_top_items(
    time_range: MusicTimeRange = "medium_term",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MusicSnapshotResponse:
    """Força nova coleta, mantendo o último snapshot se houver rate limit."""
    return await _load_snapshot(
        db,
        current_user["id"],
        time_range=time_range,
        force_refresh=True,
    )
