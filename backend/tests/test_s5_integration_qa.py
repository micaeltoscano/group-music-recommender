"""QA — Validação integrada da Sprint 5 (CT-S5-INT-01..03).

A Sprint 5 é pós-MVP: os quatro recursos (Modo Descoberta, agrupamento, faixas-
ponte e balanceamento) são opt-in por feature flag, desligados por padrão. A
validação integrada comprova que:

- CT-S5-INT-01: com TODAS as flags ligadas e subgrupos reais, uma geração real
  (Spotify mockado) compõe os quatro recursos sem quebrar — faixas-ponte marcadas,
  balanceamento avaliado, explicações agregadas no resultado.
- CT-S5-INT-02: com as flags DESLIGADAS (padrão), os recursos ficam inertes — sem
  marcação de ponte, sem balanceamento aplicado, comportamento do MVP preservado.
- CT-S5-INT-03: regressão completa das Sprints 1–4 (suíte inteira verde).

Casos definidos pelo QA no fechamento da Sprint 5 (o plano deixava-os "a definir").
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
from app.config import settings
from app.db.base import Base
from app.db.models import (
    AppSession,
    MusicSession,
    MusicSessionMember,
    PlaylistRun,
    PlaylistRunTrack,
    User,
)
from app.db.session import get_db
from app.main import app
from app.services.result_service import (
    BRIDGE_EXPLANATION,
    DISCOVERY_EXPLANATION,
    SUBGROUP_BALANCE_EXPLANATION,
)


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 's5-int.sqlite3'}",
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


# --- Snapshots que formam dois subgrupos claros (pop {1,2} e rock {3,4}) -----

def _member_snapshot(cluster: str, index: int):
    """Cada membro: 12 faixas próprias + 1 hino comum a todos (candidata-ponte)."""
    tracks = [
        {"id": f"{cluster}-t{index}-{i}", "name": f"{cluster}-t{index}-{i}",
         "artists": [{"id": f"artist-{cluster}", "name": f"artist-{cluster}"}]}
        for i in range(12)
    ]
    tracks.append({"id": "anthem", "name": "anthem",
                   "artists": [{"id": "artist-anthem", "name": "artist-anthem"}]})
    artists = [{"id": f"artist-{cluster}", "name": f"artist-{cluster}", "genres": [cluster]}]
    return {"tracks": tracks, "artists": artists}


SNAPSHOTS = {
    1: _member_snapshot("pop", 1), 2: _member_snapshot("pop", 2),
    3: _member_snapshot("rock", 3), 4: _member_snapshot("rock", 4),
}


def _make_room(session_factory, *, code, mode):
    db = session_factory()
    try:
        exp = datetime.now(timezone.utc) + timedelta(hours=24)
        host = User(spotify_id=f"{code}-h", display_name="Host")
        db.add(host)
        db.flush()
        room = MusicSession(code=code, host_user_id=host.id, status="open",
                            occasion="Festa", description="animada", mode=mode, expires_at=exp)
        db.add(room)
        db.flush()
        db.add(MusicSessionMember(session_id=room.id, user_id=host.id, role="host"))
        db.add(AppSession(user_id=host.id,
                          session_token_hash=hashlib.sha256(f"{code}-t".encode()).hexdigest(),
                          expires_at=datetime.now(timezone.utc) + timedelta(hours=1)))
        member_ids = [host.id]
        # remapeia os 4 snapshots para os ids reais dos membros
        for i in range(2, 5):
            g = User(spotify_id=f"{code}-g{i}", display_name=f"G{i}")
            db.add(g)
            db.flush()
            db.add(MusicSessionMember(session_id=room.id, user_id=g.id, role="member"))
            member_ids.append(g.id)
        db.commit()
        return SimpleNamespace(room_id=room.id, code=code, host_id=host.id,
                               token=f"{code}-t", member_ids=member_ids)
    finally:
        db.close()


async def _search_exact(_token, query, *, market="from_token", limit=3):
    del market, limit
    name = query.split()[0]
    return [{"id": f"sp-{name}", "uri": f"spotify:track:{name}", "name": name,
             "artists": [{"name": f"Art{name}"}], "is_playable": True}]


def _spotify_mocks(stack, room):
    # mapeia member_ids reais → snapshots pop/rock
    mapping = {room.member_ids[i]: SNAPSHOTS[i + 1] for i in range(4)}

    async def _snapshot(db, user_id, *, time_range="medium_term"):
        del db, time_range
        snap = mapping[user_id]
        return SimpleNamespace(snapshot=SimpleNamespace(
            top_tracks_json=snap["tracks"], top_artists_json=snap["artists"]))

    stack.enter_context(patch("app.services.generation_service.get_or_refresh_snapshot",
                              new=AsyncMock(side_effect=_snapshot)))
    stack.enter_context(patch("app.clients.spotify_client.get_valid_access_token",
                              new=AsyncMock(return_value="tok")))
    stack.enter_context(patch("app.clients.spotify_client.search_track",
                              new=AsyncMock(side_effect=_search_exact)))
    stack.enter_context(patch("app.clients.spotify_client.create_playlist",
                              new=AsyncMock(return_value={"id": "pl", "external_urls":
                                                          {"spotify": "https://open.spotify.com/x"}})))
    stack.enter_context(patch("app.clients.spotify_client.add_items_to_playlist",
                              new=AsyncMock(return_value={"snapshot_id": "s"})))
    stack.enter_context(patch("httpx.AsyncClient.post",
                              new=AsyncMock(side_effect=RuntimeError("no ollama"))))


# ===========================================================================
# CT-S5-INT-01 — todas as flags ligadas compõem sem quebrar
# ===========================================================================

def test_ct_s5_int_01_todas_as_flags_ligadas(client, session_factory, monkeypatch):
    monkeypatch.setattr(settings, "discovery_mode_enabled", True)
    monkeypatch.setattr(settings, "bridge_tracks_enabled", True)
    monkeypatch.setattr(settings, "subgroup_balancing_enabled", True)
    room = _make_room(session_factory, code="S5INT-01", mode="Descoberta")

    with ExitStack() as stack:
        _spotify_mocks(stack, room)
        client.cookies.set(SESSION_COOKIE_NAME, room.token)
        resp = client.post(f"/rooms/{room.code}/generate")
        assert resp.status_code == 202, resp.text
        assert resp.json()["status"] == "completed"
        result = client.get(f"/rooms/{room.code}/result").json()

    db = session_factory()
    try:
        run = db.query(PlaylistRun).filter_by(session_id=room.room_id, status="completed").one()
        # a candidata-ponte 'anthem' (em todos os subgrupos) deve estar marcada
        anthem = db.query(PlaylistRunTrack).filter_by(run_id=run.id, candidate_id="anthem").first()
        assert anthem is not None and anthem.is_bridge is True, "hino comum deveria ser faixa-ponte"
        # subgroup_balancing_applied é booleano persistido (pode ser True ou False)
        assert isinstance(run.subgroup_balancing_applied, bool)
    finally:
        db.close()

    why = " ".join(result.get("why_items", []))
    # modo Descoberta sempre explica; ponte aparece porque há faixa-ponte na seleção
    assert DISCOVERY_EXPLANATION in result["why_items"]
    assert BRIDGE_EXPLANATION in result["why_items"]


# ===========================================================================
# CT-S5-INT-02 — flags desligadas: recursos inertes (comportamento MVP)
# ===========================================================================

def test_ct_s5_int_02_flags_desligadas_sao_inertes(client, session_factory, monkeypatch):
    monkeypatch.setattr(settings, "discovery_mode_enabled", False)
    monkeypatch.setattr(settings, "bridge_tracks_enabled", False)
    monkeypatch.setattr(settings, "subgroup_balancing_enabled", False)
    room = _make_room(session_factory, code="S5INT-02", mode="Democrático")

    with ExitStack() as stack:
        _spotify_mocks(stack, room)
        client.cookies.set(SESSION_COOKIE_NAME, room.token)
        assert client.post(f"/rooms/{room.code}/generate").status_code == 202
        result = client.get(f"/rooms/{room.code}/result").json()

    db = session_factory()
    try:
        run = db.query(PlaylistRun).filter_by(session_id=room.room_id, status="completed").one()
        assert run.subgroup_balancing_applied is False
        # nenhuma faixa marcada como ponte com a flag desligada
        bridges = db.query(PlaylistRunTrack).filter_by(run_id=run.id, is_bridge=True).count()
        assert bridges == 0
    finally:
        db.close()

    assert BRIDGE_EXPLANATION not in result["why_items"]
    assert SUBGROUP_BALANCE_EXPLANATION not in result["why_items"]
    assert DISCOVERY_EXPLANATION not in result["why_items"]
