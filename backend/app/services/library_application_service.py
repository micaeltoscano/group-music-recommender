"""Leitura sanitizada e adaptação da biblioteca para o motor (PB-34)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import (
    UserMusicLibrarySnapshot,
    UserMusicLibrarySource,
    UserMusicLibraryTrack,
)
from app.engine.candidates import CandidateTrack
from app.engine.weighted_library import (
    LibraryOriginSignal,
    LibraryTrackSignal,
    WeightedTasteProfile,
    build_weighted_profile,
    merge_weighted_candidates,
)
from app.schemas.music import MusicLibraryOriginCounts, MusicLibraryStatusResponse


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def music_library_status(
    db: Session, user_id: int, *, now: datetime | None = None
) -> MusicLibraryStatusResponse:
    checked_at = _utc(now or datetime.now(timezone.utc))
    snapshot = db.query(UserMusicLibrarySnapshot).filter_by(user_id=user_id).one_or_none()
    if snapshot is None:
        return MusicLibraryStatusResponse(
            state="missing",
            track_count=0,
            age_seconds=None,
            stale=False,
            origins=MusicLibraryOriginCounts(top=0, playlist=0),
        )
    age_seconds = max(0, int((checked_at - _utc(snapshot.built_at)).total_seconds()))
    stale = age_seconds >= settings.music_library_ttl_days * 86400
    sources = (
        db.query(UserMusicLibrarySource.source_type, UserMusicLibrarySource.library_track_id)
        .join(
            UserMusicLibraryTrack,
            UserMusicLibrarySource.library_track_id == UserMusicLibraryTrack.id,
        )
        .filter(UserMusicLibraryTrack.snapshot_id == snapshot.id)
        .all()
    )
    return MusicLibraryStatusResponse(
        state="stale" if stale else "ready",
        track_count=snapshot.track_count,
        age_seconds=age_seconds,
        stale=stale,
        warning_code=snapshot.last_sync_error_code,
        retry_after=snapshot.last_sync_retry_after,
        origins=MusicLibraryOriginCounts(
            top=len({track_id for source_type, track_id in sources if source_type == "top"}),
            playlist=len(
                {track_id for source_type, track_id in sources if source_type == "playlist"}
            ),
        ),
    )


def _library_signals(snapshot: UserMusicLibrarySnapshot) -> list[LibraryTrackSignal]:
    return [
        LibraryTrackSignal(
            spotify_track_id=track.spotify_track_id,
            spotify_uri=track.spotify_uri,
            track_name=track.track_name,
            artist_id=track.artist_id,
            artist_name=track.artist_name,
            origins=tuple(
                LibraryOriginSignal(
                    source_type=origin.source_type,
                    source_ref=origin.source_ref,
                    rank=origin.source_rank,
                    access_type=origin.access_type,
                )
                for origin in track.origins
            ),
        )
        for track in snapshot.tracks
    ]


@dataclass(frozen=True)
class LibraryGenerationData:
    profiles: tuple[WeightedTasteProfile, ...]
    candidates: tuple[CandidateTrack, ...]


def load_library_generation_data(
    db: Session, user_ids: list[int]
) -> LibraryGenerationData | None:
    """Retorna None quando qualquer membro ainda precisa do fallback Top histórico."""
    snapshots = {
        snapshot.user_id: snapshot
        for snapshot in db.query(UserMusicLibrarySnapshot)
        .filter(UserMusicLibrarySnapshot.user_id.in_(user_ids))
        .all()
    }
    if any(user_id not in snapshots for user_id in user_ids):
        return None
    profiles = tuple(
        build_weighted_profile(user_id, _library_signals(snapshots[user_id]))
        for user_id in user_ids
    )
    merged = merge_weighted_candidates(profiles)
    candidates = tuple(
        CandidateTrack(
            track_id=item.track.spotify_track_id,
            raw_data={
                "id": item.track.spotify_track_id,
                "uri": item.track.spotify_uri,
                "name": item.track.track_name,
                "artists": [
                    {"id": item.track.artist_id, "name": item.track.artist_name}
                ] if item.track.artist_id or item.track.artist_name else [],
                "library_origin_counts": {
                    "top": sum(origin.source_type == "top" for origin in item.track.origins),
                    "playlist": sum(
                        origin.source_type == "playlist" for origin in item.track.origins
                    ),
                },
            },
            source_user_ids=set(item.source_user_ids),
            origin="spotify_library",
            preference_by_user={
                contribution.user_id: contribution.preference_weight
                for contribution in item.contributors
            },
        )
        for item in merged
    )
    return LibraryGenerationData(profiles=profiles, candidates=candidates)
