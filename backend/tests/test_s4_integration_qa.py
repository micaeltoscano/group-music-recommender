"""QA — Validação integrada da Sprint 4 (CT-S4-INT-01..05).

Dirige o fluxo real via API (`POST /rooms/{code}/generate`,
`GET /rooms/{code}/result`, rotas de feedback e `POST /auth/logout`) com
Spotify/LLM/Last.fm mockados. Cobre a parte automatizável de cada caso.

Limitação assumida: CT-S4-INT-02 ("sequenciador na playlist real") exige conta
Spotify real e é demonstração manual — fora deste arquivo, como CT-S3-INT-01.
"""

from __future__ import annotations

import hashlib
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.auth import SESSION_COOKIE_NAME
from app.clients import lastfm_client
from app.config import settings
from app.db.base import Base
from app.db.models import (
    AppSession,
    MemberTrackFeedback,
    MusicSession,
    MusicSessionMember,
    PlaylistFeedback,
    PlaylistRun,
    PlaylistRunTrack,
    TrackContextCache,
    User,
)
from app.db.session import get_db
from app.main import app
from app.services.context_enrichment_service import (
    CONSENSUS_SOURCE,
    SPOTIFY_GENRES_SOURCE,
    TRACK_TAGS_SOURCE,
)


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 's4-int.sqlite3'}",
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
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _make_room(session_factory, *, code, genre="dance pop", members=1):
    db = session_factory()
    try:
        host = User(spotify_id=f"{code}_host", display_name="Host")
        db.add(host)
        db.flush()
        room = MusicSession(
            code=code, host_user_id=host.id, status="open",
            occasion="Festa", description="animada",
            mode="Democrático",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
        db.add(room)
        db.flush()
        db.add(MusicSessionMember(session_id=room.id, user_id=host.id, role="host"))
        token = f"{code}-host-token"
        db.add(
            AppSession(
                user_id=host.id,
                session_token_hash=hashlib.sha256(token.encode()).hexdigest(),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
        )
        db.commit()
        return SimpleNamespace(room_id=room.id, code=code, host_id=host.id, token=token, genre=genre)
    finally:
        db.close()


def _top_tracks(genre, total=25):
    return [
        {
            "id": f"track{i:02d}",
            "name": f"Track{i:02d}",
            "artists": [{"id": f"art{i:02d}", "name": f"Art{i:02d}"}],
            "genres": [genre],
            "popularity": 70,
            "album": {"release_date": "2026"},
        }
        for i in range(total)
    ]


async def _search_exact(_token, query, *, market="from_token", limit=3):
    del market, limit
    name = query.split()[0]
    return [
        {
            "id": f"sp-{name}", "uri": f"spotify:track:{name}",
            "name": name, "artists": [{"name": f"Art{name}"}], "is_playable": True,
        }
    ]


def _spotify_mocks(stack, genre="dance pop"):
    tracks = _top_tracks(genre)

    async def _snapshot(db, user_id, *, time_range="medium_term"):
        del db, user_id, time_range
        return SimpleNamespace(
            snapshot=SimpleNamespace(top_tracks_json=tracks, top_artists_json=[])
        )

    stack.enter_context(patch("app.services.generation_service.get_or_refresh_snapshot",
                              new=AsyncMock(side_effect=_snapshot)))
    stack.enter_context(patch("app.clients.spotify_client.get_valid_access_token",
                              new=AsyncMock(return_value="host-token")))
    stack.enter_context(patch("app.clients.spotify_client.search_track",
                              new=AsyncMock(side_effect=_search_exact)))
    stack.enter_context(patch("app.clients.spotify_client.create_playlist",
                              new=AsyncMock(return_value={
                                  "id": "pl-s4",
                                  "external_urls": {"spotify": "https://open.spotify.com/playlist/s4"},
                              })))
    stack.enter_context(patch("app.clients.spotify_client.add_items_to_playlist",
                              new=AsyncMock(return_value={"snapshot_id": "snap"})))
    # LLM indisponível por padrão → fallback determinístico (não interfere no foco S4).
    stack.enter_context(patch("httpx.AsyncClient.post",
                              new=AsyncMock(side_effect=RuntimeError("no ollama"))))


# ===========================================================================
# CT-S4-INT-01 — Last.fm enriquece o contexto; falha cai na cascata
# ===========================================================================

def test_ct_s4_int_01_lastfm_enriquece_e_persiste_cache(client, session_factory, monkeypatch):
    monkeypatch.setattr(settings, "lastfm_api_key", "fake-key")
    room = _make_room(session_factory, code="S4INT01")

    async def _track_tags(artist, track):
        return ["feel good", "summer"]

    with ExitStack() as stack:
        _spotify_mocks(stack)
        stack.enter_context(patch.object(lastfm_client, "get_track_tags", _track_tags))
        client.cookies.set(SESSION_COOKIE_NAME, room.token)
        resp = client.post(f"/rooms/{room.code}/generate")
        assert resp.status_code == 202, resp.text
        assert resp.json()["status"] == "completed"

    db = session_factory()
    try:
        rows = db.query(TrackContextCache).all()
        assert rows, "cache do Last.fm deveria ter sido populado"
        assert all(r.source == TRACK_TAGS_SOURCE for r in rows)
        assert all(r.confidence == 0.95 for r in rows)
        # tags do Last.fm foram anexadas às faixas
        assert any("feel good" in (r.lastfm_track_tags_json or []) for r in rows)
    finally:
        db.close()


def test_ct_s4_int_01_falha_do_lastfm_cai_na_cascata_sem_quebrar(client, session_factory, monkeypatch):
    monkeypatch.setattr(settings, "lastfm_api_key", "fake-key")
    room = _make_room(session_factory, code="S4INT1B", genre="indie rock")

    async def _boom(*args, **kwargs):
        raise RuntimeError("lastfm down")

    with ExitStack() as stack:
        _spotify_mocks(stack, genre="indie rock")
        stack.enter_context(patch.object(lastfm_client, "get_track_tags", _boom))
        stack.enter_context(patch.object(lastfm_client, "get_artist_tags", _boom))
        client.cookies.set(SESSION_COOKIE_NAME, room.token)
        resp = client.post(f"/rooms/{room.code}/generate")
        assert resp.status_code == 202, resp.text
        assert resp.json()["status"] == "completed"

    db = session_factory()
    try:
        rows = db.query(TrackContextCache).all()
        assert rows
        # sem tags do Last.fm → cascata para gêneros Spotify (há genre) ou consenso
        assert all(r.source in {SPOTIFY_GENRES_SOURCE, CONSENSUS_SOURCE} for r in rows)
    finally:
        db.close()


# ===========================================================================
# CT-S4-INT-03 — feedback vinculado à execução real
# ===========================================================================

def test_ct_s4_int_03_feedback_vinculado_ao_run_real(client, session_factory):
    room = _make_room(session_factory, code="S4INT03")
    with ExitStack() as stack:
        _spotify_mocks(stack)
        client.cookies.set(SESSION_COOKIE_NAME, room.token)
        assert client.post(f"/rooms/{room.code}/generate").status_code == 202

    db = session_factory()
    try:
        run = db.query(PlaylistRun).filter_by(session_id=room.room_id, status="completed").one()
        run_id = str(run.id)
        matched = (
            db.query(PlaylistRunTrack)
            .filter_by(run_id=run.id, status="matched")
            .first()
        )
        track_sid = matched.spotify_id
    finally:
        db.close()

    client.cookies.set(SESSION_COOKIE_NAME, room.token)
    # feedback por faixa
    r1 = client.post(f"/playlist-runs/{run_id}/tracks/{track_sid}/feedback",
                     json={"liked": True, "more_like_this": True})
    assert r1.status_code == 200, r1.text
    # feedback geral
    r2 = client.post(f"/playlist-runs/{run_id}/feedback",
                     json={"representation_score": 4, "satisfaction_score": 5})
    assert r2.status_code == 200, r2.text

    db = session_factory()
    try:
        tf = db.query(MemberTrackFeedback).filter_by(playlist_run_id=run.id).all()
        pf = db.query(PlaylistFeedback).filter_by(playlist_run_id=run.id).all()
        assert len(tf) == 1 and tf[0].user_id == room.host_id and tf[0].liked is True
        assert len(pf) == 1 and pf[0].representation_score == 4 and pf[0].satisfaction_score == 5
    finally:
        db.close()


# ===========================================================================
# CT-S4-INT-05 — logout durante fluxo ativo: ações seguintes negadas
# ===========================================================================

def test_ct_s4_int_05_logout_invalida_e_nega_acoes_seguintes(client, session_factory):
    room = _make_room(session_factory, code="S4INT05")
    with ExitStack() as stack:
        _spotify_mocks(stack)
        client.cookies.set(SESSION_COOKIE_NAME, room.token)
        assert client.post(f"/rooms/{room.code}/generate").status_code == 202
        # resultado acessível enquanto logado
        assert client.get(f"/rooms/{room.code}/result").status_code == 200

    db = session_factory()
    try:
        run_id = str(
            db.query(PlaylistRun).filter_by(session_id=room.room_id, status="completed").one().id
        )
    finally:
        db.close()

    # logout no meio do uso
    client.cookies.set(SESSION_COOKIE_NAME, room.token)
    assert client.post("/auth/logout").status_code == 204

    # a sessão foi removida do banco
    db = session_factory()
    try:
        assert db.query(AppSession).filter_by(user_id=room.host_id).count() == 0
    finally:
        db.close()

    # ações seguintes com o mesmo token são negadas (401)
    client.cookies.set(SESSION_COOKIE_NAME, room.token)
    assert client.get(f"/rooms/{room.code}/result").status_code == 401
    assert client.get("/auth/me").status_code == 401
    assert client.post(f"/playlist-runs/{run_id}/feedback",
                       json={"representation_score": 3, "satisfaction_score": 3}).status_code == 401
    # nada de feedback foi persistido
    db = session_factory()
    try:
        assert db.query(PlaylistFeedback).count() == 0
    finally:
        db.close()
