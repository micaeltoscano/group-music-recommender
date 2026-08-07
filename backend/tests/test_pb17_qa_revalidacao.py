"""QA (revalidação) — PB-17, sondagem adversarial de `llm_client.py`.

Testes independentes do QA, não escritos pelo implementador. Buscam caminhos
não cobertos por `test_pb17_llm_context.py`: envelopes de resposta do Ollama
fora do formato esperado (não é um dict), que podem escapar do tratamento de
exceções e violar o critério 2 do PB-17 ("resposta inválida rejeitada sem
interromper a geração").
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.auth import SESSION_COOKIE_NAME
from app.clients import llm_client
from app.db.base import Base
from app.db.models import AppSession, MusicSession, MusicSessionMember, PlaylistRun, User
from app.db.session import get_db
from app.main import app
from app.schemas.context import LLMContext


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def _mock_response(json_body, status_code: int = 200) -> httpx.Response:
    request = httpx.Request("POST", "http://localhost:11434/api/generate")
    return httpx.Response(status_code, json=json_body, request=request)


# --------------------------------------------------------------------------
# DEF-PB17-01: envelope JSON válido mas de tipo inesperado (não é dict)
# --------------------------------------------------------------------------

@pytest.mark.anyio
async def test_envelope_lista_nao_derruba_interpret_context():
    """Ollama pode (por bug, proxy, ou versão de API diferente) responder um
    corpo JSON válido que não é um objeto (`{"response": ...}`), e sim, por
    exemplo, uma lista. `_call_ollama` faz `body.get("response")` sem garantir
    que `body` é um dict — isso deveria cair no fallback (critério 2), não
    propagar uma exceção não tratada.
    """
    with patch(
        "httpx.AsyncClient.post",
        new=AsyncMock(return_value=_mock_response(["nao", "e", "um", "dict"])),
    ):
        # Não deve lançar AttributeError (ou qualquer exceção) — deve cair no
        # fallback determinístico, como qualquer outra falha do LLM.
        ctx = await llm_client.interpret_context("Festa", "animada")

    assert isinstance(ctx, LLMContext)


@pytest.mark.anyio
async def test_envelope_string_nao_derruba_interpret_context():
    """Mesma classe de defeito: corpo JSON é uma string pura, não um objeto."""
    with patch(
        "httpx.AsyncClient.post",
        new=AsyncMock(return_value=_mock_response("apenas uma string")),
    ):
        ctx = await llm_client.interpret_context("Festa", "animada")

    assert isinstance(ctx, LLMContext)


@pytest.mark.anyio
async def test_envelope_numero_nao_derruba_interpret_context():
    """Mesma classe de defeito: corpo JSON é um número puro."""
    with patch(
        "httpx.AsyncClient.post",
        new=AsyncMock(return_value=_mock_response(42)),
    ):
        ctx = await llm_client.interpret_context("Festa", "animada")

    assert isinstance(ctx, LLMContext)


# --------------------------------------------------------------------------
# Efeito em cascata: o mesmo cenário não deve derrubar a geração da playlist
# --------------------------------------------------------------------------

@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pb17-qa-reval.sqlite3'}",
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
    raw_token = "pb17-qa-reval-session"
    db = session_factory()
    try:
        host = User(spotify_id="pb17_qa_reval_host", display_name="Solo Host")
        db.add(host)
        db.flush()
        room = MusicSession(
            code="QAREV01",
            host_user_id=host.id,
            status="open",
            occasion="Festa",
            description="animada",
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
        snapshot=SimpleNamespace(top_tracks_json=_top_tracks(total), top_artists_json=[])
    )


@patch("app.services.generation_service.get_or_refresh_snapshot", new_callable=AsyncMock)
@patch("app.clients.spotify_client.get_valid_access_token", new_callable=AsyncMock)
@patch("app.clients.spotify_client.search_track", new_callable=AsyncMock)
@patch("app.clients.spotify_client.create_playlist", new_callable=AsyncMock)
@patch("app.clients.spotify_client.add_items_to_playlist", new_callable=AsyncMock)
def test_ollama_envelope_inesperado_nao_interrompe_geracao_da_playlist(
    mock_add_items,
    mock_create_playlist,
    mock_search,
    mock_get_token,
    mock_snapshot,
    client,
    session_factory,
    solo_room,
):
    """CT-PB17-02 (revalidação): 'resposta inválida' do LLM deve ser rejeitada
    SEM interromper a geração. Envelope de tipo inesperado (lista, não dict)
    é uma forma de resposta inválida — a geração deve concluir normalmente,
    não retornar 500/502.
    """
    mock_snapshot.return_value = _snapshot_result()
    mock_get_token.return_value = "host-access-token"
    mock_search.side_effect = _search_exact_track
    mock_create_playlist.return_value = {
        "id": "playlist-qa",
        "external_urls": {"spotify": "https://open.spotify.com/playlist/qa"},
    }
    mock_add_items.return_value = {"snapshot_id": "snapshot-created"}
    client.cookies.set(SESSION_COOKIE_NAME, solo_room.token)

    with patch(
        "httpx.AsyncClient.post",
        new=AsyncMock(return_value=_mock_response(["envelope", "inesperado"])),
    ):
        response = client.post(f"/rooms/{solo_room.code}/generate")

    assert response.status_code == 202, (
        f"Geração falhou com status {response.status_code} por causa de um "
        f"envelope de resposta do Ollama fora do formato esperado — o critério 2 "
        f"do PB-17 exige que isso NUNCA interrompa a geração. Corpo: {response.json()}"
    )
    assert response.json()["status"] == "completed"
