"""Inventário mínimo e privado de playlists do usuário (PB-30)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.clients import spotify_client
from app.db.models import User, UserPlaylistInventory


@dataclass(frozen=True)
class PlaylistInventorySkip:
    spotify_playlist_id: str | None
    reason: str


@dataclass(frozen=True)
class PlaylistInventoryResult:
    items: tuple[UserPlaylistInventory, ...]
    skipped: tuple[PlaylistInventorySkip, ...]


def _minimal_playlist_metadata(
    raw: object,
    *,
    user_spotify_id: str,
) -> tuple[str, str, int, str] | None:
    if not isinstance(raw, dict):
        return None
    playlist_id = raw.get("id")
    snapshot_id = raw.get("snapshot_id")
    owner = raw.get("owner")
    items_summary = raw.get("items")
    if items_summary is None:
        items_summary = raw.get("tracks")
    if (
        not isinstance(playlist_id, str)
        or not playlist_id.isalnum()
        or not isinstance(snapshot_id, str)
        or not snapshot_id
        or not isinstance(owner, dict)
        or not isinstance(items_summary, dict)
    ):
        return None
    owner_id = owner.get("id")
    tracks_total = items_summary.get("total")
    if not isinstance(tracks_total, int) or isinstance(tracks_total, bool) or tracks_total < 0:
        return None

    if owner_id == user_spotify_id:
        access_type = "owned"
    elif raw.get("collaborative") is True:
        access_type = "collaborative"
    else:
        return None
    return playlist_id, access_type, tracks_total, snapshot_id


async def refresh_playlist_inventory(
    db: Session,
    user_id: int,
    *,
    now: datetime | None = None,
) -> PlaylistInventoryResult:
    """Verifica playlists legíveis e promove o inventário somente após sucesso total."""
    user = db.get(User, user_id)
    if user is None:
        raise ValueError("Usuário não encontrado.")

    verified_at = now or datetime.now(timezone.utc)
    access_token = await spotify_client.get_valid_access_token(
        db,
        user_id,
        required_scopes=spotify_client.PLAYLIST_INVENTORY_SCOPES,
    )
    raw_playlists = await spotify_client.get_current_user_playlists(access_token)

    eligible: list[tuple[str, str, int, str]] = []
    skipped: list[PlaylistInventorySkip] = []
    seen: set[str] = set()
    for raw in raw_playlists:
        playlist_id = raw.get("id") if isinstance(raw, dict) else None
        metadata = _minimal_playlist_metadata(raw, user_spotify_id=user.spotify_id)
        if metadata is None:
            reason = "followed_not_eligible" if isinstance(playlist_id, str) else "invalid_metadata"
            skipped.append(PlaylistInventorySkip(playlist_id, reason))
            continue

        playlist_id, access_type, tracks_total, snapshot_id = metadata
        if playlist_id in seen:
            skipped.append(PlaylistInventorySkip(playlist_id, "duplicate"))
            continue
        seen.add(playlist_id)
        try:
            await spotify_client.get_playlist_items_page(
                access_token,
                playlist_id,
                limit=1,
                offset=0,
            )
        except spotify_client.SpotifyAccessForbidden:
            skipped.append(PlaylistInventorySkip(playlist_id, "content_forbidden"))
            continue
        eligible.append((playlist_id, access_type, tracks_total, snapshot_id))

    existing = {
        item.spotify_playlist_id: item
        for item in db.query(UserPlaylistInventory).filter_by(user_id=user_id).all()
    }
    eligible_ids: set[str] = set()
    try:
        for playlist_id, access_type, tracks_total, snapshot_id in eligible:
            eligible_ids.add(playlist_id)
            item = existing.get(playlist_id)
            if item is None:
                item = UserPlaylistInventory(
                    user_id=user_id,
                    spotify_playlist_id=playlist_id,
                    access_type=access_type,
                    tracks_total=tracks_total,
                    snapshot_id=snapshot_id,
                    verified_at=verified_at,
                )
                db.add(item)
            else:
                item.access_type = access_type
                item.tracks_total = tracks_total
                item.snapshot_id = snapshot_id
                item.verified_at = verified_at

        stale_query = db.query(UserPlaylistInventory).filter_by(user_id=user_id)
        if eligible_ids:
            stale_query = stale_query.filter(
                ~UserPlaylistInventory.spotify_playlist_id.in_(eligible_ids)
            )
        stale_query.delete(synchronize_session=False)
        db.commit()
    except Exception:
        db.rollback()
        raise

    items = tuple(
        db.query(UserPlaylistInventory)
        .filter_by(user_id=user_id)
        .order_by(UserPlaylistInventory.spotify_playlist_id)
        .all()
    )
    return PlaylistInventoryResult(items=items, skipped=tuple(skipped))
