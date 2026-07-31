"""Composição pura e determinística da biblioteca pessoal (PB-31)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

MUSIC_LIBRARY_LIMIT = 500
TOP_TRACK_LIMIT_PER_RANGE = 50
TOP_TIME_RANGES = ("short_term", "medium_term", "long_term")
PLAYLIST_ACCESS_TYPES = frozenset({"owned", "collaborative"})


@dataclass(frozen=True)
class MinimalTrack:
    spotify_track_id: str
    spotify_uri: str
    track_name: str | None
    artist_id: str | None
    artist_name: str | None


@dataclass(frozen=True)
class TopTrackSignal:
    track: Mapping[str, object]
    time_range: str
    rank: int


@dataclass(frozen=True)
class PlaylistTrackSignal:
    track: Mapping[str, object]
    spotify_playlist_id: str
    access_type: str
    rank: int
    playlist_snapshot_id: str | None = None


@dataclass(frozen=True)
class LibraryOrigin:
    source_type: str
    source_ref: str
    rank: int
    access_type: str | None = None
    playlist_snapshot_id: str | None = None

    @property
    def source_key(self) -> str:
        return f"{self.source_type}:{self.source_ref}:{self.rank}"


@dataclass(frozen=True)
class ComposedLibraryTrack:
    track: MinimalTrack
    position: int
    origins: tuple[LibraryOrigin, ...]


def _optional_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _minimal_track(raw: Mapping[str, object]) -> MinimalTrack | None:
    spotify_track_id = raw.get("id")
    spotify_uri = raw.get("uri")
    if (
        not isinstance(spotify_track_id, str)
        or not spotify_track_id.isalnum()
        or spotify_uri != f"spotify:track:{spotify_track_id}"
    ):
        return None

    artist_id: str | None = None
    artist_name: str | None = None
    artists = raw.get("artists")
    if isinstance(artists, list) and artists and isinstance(artists[0], dict):
        artist_id = _optional_text(artists[0].get("id"))
        artist_name = _optional_text(artists[0].get("name"))

    return MinimalTrack(
        spotify_track_id=spotify_track_id,
        spotify_uri=spotify_uri,
        track_name=_optional_text(raw.get("name")),
        artist_id=artist_id,
        artist_name=artist_name,
    )


def compose_music_library(
    top_signals: Iterable[TopTrackSignal],
    playlist_signals: Iterable[PlaylistTrackSignal],
    *,
    limit: int = MUSIC_LIBRARY_LIMIT,
) -> tuple[ComposedLibraryTrack, ...]:
    """Prioriza Tops e preenche playlists em round-robin sem ultrapassar ``limit``."""
    if not 0 <= limit <= MUSIC_LIBRARY_LIMIT:
        raise ValueError("O limite da biblioteca deve estar entre 0 e 500.")

    selected: dict[str, MinimalTrack] = {}
    selection_order: list[str] = []
    origins: dict[str, dict[str, LibraryOrigin]] = {}

    def consume(track: MinimalTrack, origin: LibraryOrigin) -> None:
        track_origins = origins.setdefault(track.spotify_track_id, {})
        if track.spotify_track_id in selected:
            track_origins.setdefault(origin.source_key, origin)
            return
        if len(selection_order) >= limit:
            return
        selected[track.spotify_track_id] = track
        selection_order.append(track.spotify_track_id)
        track_origins[origin.source_key] = origin

    range_order = {time_range: index for index, time_range in enumerate(TOP_TIME_RANGES)}
    normalized_tops: list[tuple[int, int, str, MinimalTrack, TopTrackSignal]] = []
    for signal in top_signals:
        if signal.time_range not in range_order or not 1 <= signal.rank <= TOP_TRACK_LIMIT_PER_RANGE:
            continue
        track = _minimal_track(signal.track)
        if track is None:
            continue
        normalized_tops.append(
            (range_order[signal.time_range], signal.rank, track.spotify_track_id, track, signal)
        )

    for _range_index, _rank, _track_id, track, signal in sorted(
        normalized_tops,
        key=lambda item: item[:3],
    ):
        consume(
            track,
            LibraryOrigin(
                source_type="top",
                source_ref=signal.time_range,
                rank=signal.rank,
            ),
        )

    grouped_playlists: dict[
        str,
        list[tuple[int, str, MinimalTrack, PlaylistTrackSignal]],
    ] = {}
    for signal in playlist_signals:
        if (
            not signal.spotify_playlist_id.isalnum()
            or signal.access_type not in PLAYLIST_ACCESS_TYPES
            or signal.rank < 1
        ):
            continue
        track = _minimal_track(signal.track)
        if track is None:
            continue
        grouped_playlists.setdefault(signal.spotify_playlist_id, []).append(
            (signal.rank, track.spotify_track_id, track, signal)
        )

    ordered_playlist_ids = sorted(grouped_playlists)
    ordered_playlists = {
        playlist_id: sorted(
            grouped_playlists[playlist_id],
            key=lambda item: item[:2],
        )
        for playlist_id in ordered_playlist_ids
    }
    rounds = max((len(items) for items in ordered_playlists.values()), default=0)
    for round_index in range(rounds):
        for playlist_id in ordered_playlist_ids:
            items = ordered_playlists[playlist_id]
            if round_index >= len(items):
                continue
            _rank, _track_id, track, signal = items[round_index]
            consume(
                track,
                LibraryOrigin(
                    source_type="playlist",
                    source_ref=playlist_id,
                    rank=signal.rank,
                    access_type=signal.access_type,
                    playlist_snapshot_id=signal.playlist_snapshot_id,
                ),
            )

    return tuple(
        ComposedLibraryTrack(
            track=selected[track_id],
            position=position,
            origins=tuple(
                origins[track_id][key]
                for key in sorted(origins[track_id])
            ),
        )
        for position, track_id in enumerate(selection_order, start=1)
    )
