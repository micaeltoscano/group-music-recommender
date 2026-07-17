"""
Relatório de Testes de QA - PB-15 (Criação da playlist no Spotify)

CT-PB15-01: Cap de 2 músicas por artista (respeita no máximo 2).
CT-PB15-02: Playlist final de 20 a 30 músicas.
CT-PB15-04: Falha parcial não deixa dados inconsistentes.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.services.generation_service import create_spotify_playlist_for_run
from app.db.models import PlaylistRun, PlaylistRunTrack

@pytest.fixture
def run_id():
    return uuid.uuid4()

@pytest.fixture
def mock_db(run_id):
    db = MagicMock()
    run = PlaylistRun(id=run_id, status="running")
    
    # Mock do db.query().with_for_update().filter().one() para retornar o run
    query_mock = MagicMock()
    query_mock.with_for_update.return_value = query_mock
    query_mock.filter.return_value = query_mock
    query_mock.one.return_value = run
    
    # Mock para buscar os tracks
    query_tracks_mock = MagicMock()
    query_tracks_mock.filter.return_value = query_tracks_mock
    query_tracks_mock.order_by.return_value = query_tracks_mock
    
    def side_effect(model):
        if model is PlaylistRun:
            return query_mock
        if model is PlaylistRunTrack:
            return query_tracks_mock
        return MagicMock()
        
    db.query.side_effect = side_effect
    db.run_instance = run
    db.query_tracks_mock = query_tracks_mock
    return db

@patch("app.clients.spotify_client.create_playlist", new_callable=AsyncMock)
@patch("app.clients.spotify_client.add_items_to_playlist", new_callable=AsyncMock)
def test_pb15_01_cap_per_artist(mock_add_items, mock_create, mock_db, run_id):
    """CT-PB15-01: Garante que no máximo 2 faixas do mesmo artista são incluídas."""
    # Criar 5 faixas do Artista A e 1 do Artista B
    tracks = [
        PlaylistRunTrack(id=uuid.uuid4(), run_id=run_id, artist="Artista A", spotify_uri="uri:1"),
        PlaylistRunTrack(id=uuid.uuid4(), run_id=run_id, artist="Artista A", spotify_uri="uri:2"),
        PlaylistRunTrack(id=uuid.uuid4(), run_id=run_id, artist="Artista A", spotify_uri="uri:3"),
        PlaylistRunTrack(id=uuid.uuid4(), run_id=run_id, artist="Artista A", spotify_uri="uri:4"),
        PlaylistRunTrack(id=uuid.uuid4(), run_id=run_id, artist="Artista A", spotify_uri="uri:5"),
        PlaylistRunTrack(id=uuid.uuid4(), run_id=run_id, artist="Artista B", spotify_uri="uri:6"),
    ]
    mock_db.query_tracks_mock.all.return_value = tracks
    
    mock_create.return_value = {"id": "playlist_123", "external_urls": {"spotify": "http://spotify.com/playlist_123"}}
    
    import asyncio
    asyncio.run(create_spotify_playlist_for_run(mock_db, run_id, "token", "spotify_user_id", "Name", "Desc"))
    
    # Verificações
    mock_create.assert_called_once()
    mock_add_items.assert_called_once()
    
    # Os URIs enviados devem ser apenas uri:1, uri:2, e uri:6
    called_uris = mock_add_items.call_args[1]["uris"]
    assert len(called_uris) == 3
    assert "uri:1" in called_uris
    assert "uri:2" in called_uris
    assert "uri:6" in called_uris
    assert "uri:3" not in called_uris


@patch("app.clients.spotify_client.create_playlist", new_callable=AsyncMock)
@patch("app.clients.spotify_client.add_items_to_playlist", new_callable=AsyncMock)
def test_pb15_02_max_30_tracks(mock_add_items, mock_create, mock_db, run_id):
    """CT-PB15-02: Garante que a playlist é fatiada em no máximo 30 músicas."""
    # Criar 40 faixas de artistas diferentes para não cair no cap de 2
    tracks = [
        PlaylistRunTrack(id=uuid.uuid4(), run_id=run_id, artist=f"Artista {i}", spotify_uri=f"uri:{i}")
        for i in range(40)
    ]
    mock_db.query_tracks_mock.all.return_value = tracks
    mock_create.return_value = {"id": "playlist_123", "external_urls": {"spotify": "http://spotify.com/playlist_123"}}
    
    import asyncio
    asyncio.run(create_spotify_playlist_for_run(mock_db, run_id, "token", "spotify_user_id", "Name", "Desc"))
    
    called_uris = mock_add_items.call_args[1]["uris"]
    assert len(called_uris) == 30


@patch("app.clients.spotify_client.create_playlist", new_callable=AsyncMock)
@patch("app.clients.spotify_client.add_items_to_playlist", new_callable=AsyncMock)
def test_pb15_04_partial_failure_persists_playlist_id(mock_add_items, mock_create, mock_db, run_id):
    """CT-PB15-04: Garante que se add_items falhar, o id da playlist já foi salvo."""
    tracks = [
        PlaylistRunTrack(id=uuid.uuid4(), run_id=run_id, artist="Artista 1", spotify_uri="uri:1"),
    ]
    mock_db.query_tracks_mock.all.return_value = tracks
    
    mock_create.return_value = {"id": "playlist_123", "external_urls": {"spotify": "http://url"}}
    mock_add_items.side_effect = Exception("Rede caiu ao adicionar itens")
    
    import asyncio
    with pytest.raises(Exception):
        asyncio.run(create_spotify_playlist_for_run(mock_db, run_id, "token", "spotify_user_id", "Name", "Desc"))
    
    # ID já deve ter sido gravado e commit efetuado antes do add_items
    assert mock_db.run_instance.spotify_playlist_id == "playlist_123"
    assert mock_db.run_instance.spotify_playlist_url == "http://url"
    mock_db.commit.assert_called()
