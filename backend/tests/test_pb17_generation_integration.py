"""Integração do PB-17 (interpretação de contexto) no pipeline de geração (PB-15).

Confirma que `execute_generation` persiste `llm_context_json` no run e que a
geração **nunca** é interrompida por falha do LLM — inclusive quando o Ollama
real está indisponível (caso comum em ambiente de teste/CI, sem mock nenhum).
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.auth import SESSION_COOKIE_NAME
from app.db.base import Base
from app.db.models import AppSession, MusicSession, MusicSessionMember, PlaylistRun, User
from app.db.session import get_db
from app.main import app


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pb17-flow.sqlite3'}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(engine)
    try:
        yield factory
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def client(session_factory):
    def _override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def solo_room(session_factory):
    raw_token = "pb17-solo-host-session"
    db = session_factory()
    try:
        host = User(spotify_id="pb17_solo_host", display_name="Solo Host")
        db.add(host)
        db.flush()
        room = MusicSession(
            code="CTX-001",
            host_user_id=host.id,
            status="open",
            occasion="Festa de aniversário",
            description="quero algo bem animado pra dançar a noite toda",
            mode="Democrático",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
        db.add(room)
        db.flush()
        db.add(MusicSessionMember(session_id=room.id, user_id=host.id, role="host"))
        db.add(
            AppSession(
                user_id=host.id,
                session_token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
        )
        db.commit()
        return SimpleNamespace(token=raw_token, host_id=host.id, room_id=room.id, code=room.code)
    finally:
        db.close()


def _top_tracks(total: int = 25) -> list[dict]:
    return [
        {
            "id": f"track{i:02d}",
            "name": f"Track{i:02d}",
            "artists": [{"id": f"artist{i:02d}", "name": f"Artist{i:02d}"}],
            "popularity": 70,
            "album": {"release_date": "2026"},
        }
        for i in range(total)
    ]


def _top_artists(total: int = 25) -> list[dict]:
    return [
        {
            "id": f"artist{i:02d}",
            "name": f"Artist{i:02d}",
            "genres": ["dance pop" if i < 30 else "acoustic instrumental"],
        }
        for i in range(total)
    ]


async def _search_exact_track(_token, query, *, market="from_token", limit=3):
    del market, limit
    track_name, artist_name = query.split()
    suffix = track_name.removeprefix("Track")
    return [
        {
            "id": f"spotify{suffix}",
            "uri": f"spotify:track:{suffix}",
            "name": track_name,
            "artists": [{"name": artist_name}],
            "is_playable": True,
        }
    ]


def _snapshot_result(total: int = 25):
    return SimpleNamespace(
        snapshot=SimpleNamespace(
            top_tracks_json=_top_tracks(total),
            top_artists_json=_top_artists(total),
        )
    )


@patch("app.services.generation_service.get_or_refresh_snapshot", new_callable=AsyncMock)
@patch("app.clients.spotify_client.get_valid_access_token", new_callable=AsyncMock)
@patch("app.clients.spotify_client.search_track", new_callable=AsyncMock)
@patch("app.clients.spotify_client.create_playlist", new_callable=AsyncMock)
@patch("app.clients.spotify_client.add_items_to_playlist", new_callable=AsyncMock)
def test_geracao_persiste_contexto_mesmo_sem_llm_real_disponivel(
    mock_add_items,
    mock_create_playlist,
    mock_search,
    mock_get_token,
    mock_snapshot,
    client,
    session_factory,
    solo_room,
):
    """CT-PB17-03 (integração): sem Ollama real no ambiente de teste, a geração
    conclui normalmente (fallback determinístico) e persiste o contexto no run.
    """
    mock_snapshot.return_value = _snapshot_result(40)
    mock_get_token.return_value = "host-access-token"
    mock_search.side_effect = _search_exact_track
    mock_create_playlist.return_value = {
        "id": "playlist-ctx",
        "external_urls": {"spotify": "https://open.spotify.com/playlist/ctx"},
    }
    mock_add_items.return_value = {"snapshot_id": "snapshot-created"}
    client.cookies.set(SESSION_COOKIE_NAME, solo_room.token)

    response = client.post(f"/rooms/{solo_room.code}/generate")

    assert response.status_code == 202
    assert response.json()["status"] == "completed"
    sent_uris = mock_add_items.await_args.kwargs["uris"]
    # PB-19 passou a sequenciar a seleção final: preserva as 30 candidatas de
    # maior ranking e a abertura forte, mas não a ordem linear antiga.
    assert len(sent_uris) == 30
    assert sent_uris[0] == "spotify:track:00"
    assert set(sent_uris) == {f"spotify:track:{index:02d}" for index in range(30)}

    db = session_factory()
    try:
        run = db.query(PlaylistRun).filter_by(session_id=solo_room.room_id).one()
        assert run.status == "completed"
        assert run.llm_context_json is not None
        context = json.loads(run.llm_context_json)
        assert context["occasion"] == "Festa de aniversário"
        # Fallback determinístico reconhece "animado" -> energy alta (via
        # heurística de palavras da descrição).
        assert context["energy"] in ("media", "alta")
        assert sorted(track.selection_rank for track in run.tracks) == list(range(1, 41))
    finally:
        db.close()
