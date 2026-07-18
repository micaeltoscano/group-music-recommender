"""Cascata e cache de enriquecimento contextual das candidatas (PB-18)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.clients import lastfm_client
from app.config import settings
from app.db.models import TrackContextCache
from app.engine.candidates import CandidateTrack

TRACK_TAGS_SOURCE = "lastfm_track_tags"
ARTIST_TAGS_SOURCE = "lastfm_artist_tags_fallback"
SPOTIFY_GENRES_SOURCE = "spotify_genres"
CONSENSUS_SOURCE = "consensus_fallback"

SOURCE_CONFIDENCE = {
    TRACK_TAGS_SOURCE: 0.95,
    ARTIST_TAGS_SOURCE: 0.75,
    SPOTIFY_GENRES_SOURCE: 0.50,
    CONSENSUS_SOURCE: 0.20,
}


@dataclass(frozen=True)
class ContextEnrichment:
    track_tags: tuple[str, ...]
    artist_tags: tuple[str, ...]
    spotify_genres: tuple[str, ...]
    source: str
    confidence: float
    fetched_at: datetime

    @property
    def selected_tags(self) -> tuple[str, ...]:
        if self.source == TRACK_TAGS_SOURCE:
            return self.track_tags
        if self.source == ARTIST_TAGS_SOURCE:
            return self.artist_tags
        if self.source == SPOTIFY_GENRES_SOURCE:
            return self.spotify_genres
        return ()


def _normalise(values: object) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple, set)):
        return ()
    return tuple(
        sorted(
            {
                value.strip().lower()
                for value in values
                if isinstance(value, str) and value.strip()
            }
        )
    )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _from_cache(row: TrackContextCache) -> ContextEnrichment:
    return ContextEnrichment(
        track_tags=_normalise(row.lastfm_track_tags_json),
        artist_tags=_normalise(row.lastfm_artist_tags_json),
        spotify_genres=_normalise(row.spotify_artist_genres_json),
        source=row.source,
        confidence=row.confidence,
        fetched_at=_as_utc(row.fetched_at),
    )


def _valid_cache(db: Session, track_id: str, now: datetime) -> TrackContextCache | None:
    row = db.query(TrackContextCache).filter_by(spotify_track_id=track_id).one_or_none()
    if row is None:
        return None
    cutoff = now - timedelta(days=settings.lastfm_cache_ttl_days)
    return row if _as_utc(row.fetched_at) >= cutoff else None


async def _resolve_context(
    track_name: str,
    artist_name: str,
    spotify_genres: tuple[str, ...],
    now: datetime,
) -> ContextEnrichment:
    track_tags: tuple[str, ...] = ()
    artist_tags: tuple[str, ...] = ()

    if lastfm_client.is_configured() and track_name and artist_name:
        try:
            track_tags = _normalise(
                await lastfm_client.get_track_tags(artist_name, track_name)
            )
        except Exception:  # noqa: BLE001 - integração externa nunca bloqueia a geração.
            track_tags = ()

        if not track_tags:
            try:
                artist_tags = _normalise(await lastfm_client.get_artist_tags(artist_name))
            except Exception:  # noqa: BLE001 - último recurso do fallback obrigatório.
                artist_tags = ()

    if track_tags:
        source = TRACK_TAGS_SOURCE
    elif artist_tags:
        source = ARTIST_TAGS_SOURCE
    elif spotify_genres:
        source = SPOTIFY_GENRES_SOURCE
    else:
        source = CONSENSUS_SOURCE

    return ContextEnrichment(
        track_tags=track_tags,
        artist_tags=artist_tags,
        spotify_genres=spotify_genres,
        source=source,
        confidence=SOURCE_CONFIDENCE[source],
        fetched_at=now,
    )


def _identity(candidate: CandidateTrack) -> tuple[str, str]:
    track_name = str(candidate.raw_data.get("name") or "").strip()
    artists = candidate.raw_data.get("artists") or []
    artist_name = ""
    if isinstance(artists, list) and artists and isinstance(artists[0], dict):
        artist_name = str(artists[0].get("name") or "").strip()
    return track_name, artist_name


def _persist(
    db: Session,
    candidate: CandidateTrack,
    track_name: str,
    artist_name: str,
    result: ContextEnrichment,
) -> None:
    row = (
        db.query(TrackContextCache)
        .filter_by(spotify_track_id=candidate.id)
        .one_or_none()
    )
    if row is None:
        row = TrackContextCache(spotify_track_id=candidate.id)
        db.add(row)

    row.track_name = track_name
    row.artist_name = artist_name
    row.lastfm_track_tags_json = list(result.track_tags)
    row.lastfm_artist_tags_json = list(result.artist_tags)
    row.spotify_artist_genres_json = list(result.spotify_genres)
    row.source = result.source
    row.confidence = result.confidence
    row.context_scores_json = {
        "source": result.source,
        "confidence": result.confidence,
    }
    row.fetched_at = result.fetched_at


def _apply(candidate: CandidateTrack, result: ContextEnrichment) -> CandidateTrack:
    raw_data = dict(candidate.raw_data)
    raw_data["context_tags"] = list(result.selected_tags)
    raw_data["context_source"] = result.source
    raw_data["context_confidence"] = result.confidence
    return CandidateTrack(candidate.id, raw_data, set(candidate.source_user_ids))


async def enrich_candidates_context(
    db: Session,
    candidates: list[CandidateTrack],
) -> list[CandidateTrack]:
    """Enriquece candidatas sem permitir que o Last.fm interrompa a geração."""

    enriched: list[CandidateTrack] = []
    now = datetime.now(timezone.utc)
    for candidate in candidates:
        cached = _valid_cache(db, candidate.id, now)
        if cached is not None:
            enriched.append(_apply(candidate, _from_cache(cached)))
            continue

        track_name, artist_name = _identity(candidate)
        spotify_genres = _normalise(candidate.raw_data.get("genres", []))
        result = await _resolve_context(track_name, artist_name, spotify_genres, now)
        _persist(db, candidate, track_name, artist_name, result)
        enriched.append(_apply(candidate, result))

    db.commit()
    return enriched
