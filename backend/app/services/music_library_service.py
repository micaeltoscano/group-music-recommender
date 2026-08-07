"""Persistência transacional da biblioteca pessoal limitada (PB-31)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Iterable, Mapping

from sqlalchemy.orm import Session

from app.db.models import (
    User,
    UserMusicLibrarySnapshot,
    UserMusicLibraryPlaylistState,
    UserMusicLibrarySource,
    UserMusicLibraryTrack,
    UserMusicSnapshot,
    UserPlaylistInventory,
)
from app.engine.music_library import (
    MUSIC_LIBRARY_LIMIT,
    TOP_TIME_RANGES,
    PlaylistTrackSignal,
    TopTrackSignal,
    compose_music_library,
)

PlaylistTracksById = Mapping[str, Iterable[Mapping[str, object]]]


def rebuild_music_library(
    db: Session,
    user_id: int,
    *,
    playlist_tracks_by_id: PlaylistTracksById,
    built_at: datetime | None = None,
) -> UserMusicLibrarySnapshot:
    """Substitui a biblioteca em uma transação usando apenas entradas já coletadas."""
    if db.get(User, user_id) is None:
        raise ValueError("Usuário não encontrado.")

    snapshots = {
        snapshot.time_range: snapshot
        for snapshot in db.query(UserMusicSnapshot)
        .filter(
            UserMusicSnapshot.user_id == user_id,
            UserMusicSnapshot.time_range.in_(TOP_TIME_RANGES),
        )
        .all()
    }
    top_signals: list[TopTrackSignal] = []
    for time_range in TOP_TIME_RANGES:
        snapshot = snapshots.get(time_range)
        if snapshot is None or not isinstance(snapshot.top_tracks_json, list):
            continue
        top_signals.extend(
            TopTrackSignal(track=track, time_range=time_range, rank=rank)
            for rank, track in enumerate(snapshot.top_tracks_json[:50], start=1)
            if isinstance(track, dict)
        )

    inventory = (
        db.query(UserPlaylistInventory)
        .filter(UserPlaylistInventory.user_id == user_id)
        .order_by(UserPlaylistInventory.spotify_playlist_id)
        .all()
    )
    playlist_signals: list[PlaylistTrackSignal] = []
    for playlist in inventory:
        raw_tracks = playlist_tracks_by_id.get(playlist.spotify_playlist_id, ())
        playlist_signals.extend(
            PlaylistTrackSignal(
                track=track,
                spotify_playlist_id=playlist.spotify_playlist_id,
                access_type=playlist.access_type,
                rank=rank,
                playlist_snapshot_id=playlist.snapshot_id,
            )
            for rank, track in enumerate(raw_tracks, start=1)
            if isinstance(track, dict)
        )

    composed = compose_music_library(top_signals, playlist_signals)
    if len(composed) > MUSIC_LIBRARY_LIMIT:  # defesa transacional contra regressão do compositor
        raise ValueError("A biblioteca excedeu o limite de 500 faixas.")

    current = (
        db.query(UserMusicLibrarySnapshot)
        .filter(UserMusicLibrarySnapshot.user_id == user_id)
        .one_or_none()
    )
    try:
        if current is not None:
            db.delete(current)
            db.flush()

        snapshot = UserMusicLibrarySnapshot(
            id=uuid.uuid4(),
            user_id=user_id,
            track_count=len(composed),
            built_at=built_at or datetime.now(timezone.utc),
        )
        db.add(snapshot)

        db.add_all(
            [
                UserMusicLibraryPlaylistState(
                    id=uuid.uuid4(),
                    snapshot_id=snapshot.id,
                    user_id=user_id,
                    spotify_playlist_id=playlist.spotify_playlist_id,
                    playlist_snapshot_id=playlist.snapshot_id,
                    access_type=playlist.access_type,
                    tracks_total=playlist.tracks_total,
                )
                for playlist in inventory
            ]
        )

        for composed_track in composed:
            track = UserMusicLibraryTrack(
                id=uuid.uuid4(),
                snapshot_id=snapshot.id,
                user_id=user_id,
                spotify_track_id=composed_track.track.spotify_track_id,
                spotify_uri=composed_track.track.spotify_uri,
                track_name=composed_track.track.track_name,
                artist_id=composed_track.track.artist_id,
                artist_name=composed_track.track.artist_name,
                position=composed_track.position,
            )
            db.add(track)
            db.add_all(
                [
                    UserMusicLibrarySource(
                        id=uuid.uuid4(),
                        library_track_id=track.id,
                        source_type=origin.source_type,
                        source_ref=origin.source_ref,
                        source_key=origin.source_key,
                        source_rank=origin.rank,
                        access_type=origin.access_type,
                        playlist_snapshot_id=origin.playlist_snapshot_id,
                    )
                    for origin in composed_track.origins
                ]
            )

        db.commit()
        db.refresh(snapshot)
        return snapshot
    except Exception:
        db.rollback()
        raise
