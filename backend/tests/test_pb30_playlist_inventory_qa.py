"""Testes adversariais independentes de QA para o PB-30."""

from app.clients import spotify_client
from app.services.playlist_inventory_service import _minimal_playlist_metadata


def test_qa_pb30_oauth_includes_collaborative_playlist_scope():
    """Playlists colaborativas de terceiros exigem o escopo específico."""
    assert "playlist-read-collaborative" in spotify_client.SCOPES.split()


def test_qa_pb30_accepts_current_spotify_items_summary():
    """O payload atual usa ``items``; ``tracks`` é apenas o nome legado."""
    payload = {
        "id": "PlaylistCurrent01",
        "owner": {"id": "qa-user"},
        "collaborative": False,
        "items": {"total": 12},
        "snapshot_id": "snapshot-current",
    }

    assert _minimal_playlist_metadata(payload, user_spotify_id="qa-user") == (
        "PlaylistCurrent01",
        "owned",
        12,
        "snapshot-current",
    )


def test_qa_pb30_prefers_current_items_summary_over_legacy_tracks():
    """Quando ambos existem, o campo vigente precisa ser a fonte de verdade."""
    payload = {
        "id": "PlaylistTransition01",
        "owner": {"id": "qa-user"},
        "collaborative": False,
        "items": {"total": 12},
        "tracks": {"total": 99},
        "snapshot_id": "snapshot-transition",
    }

    metadata = _minimal_playlist_metadata(payload, user_spotify_id="qa-user")

    assert metadata == (
        "PlaylistTransition01",
        "owned",
        12,
        "snapshot-transition",
    )
