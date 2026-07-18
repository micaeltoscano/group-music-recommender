"""QA — Validação integrada da Sprint 3 (CT-S3-INT-01..05).

Testes de integração ponta a ponta do incremento da Sprint 3, escritos pela
autoridade de QA. Exercitam o fluxo real via API (`POST /rooms/{code}/generate`
e `GET /rooms/{code}/result`) com o Spotify/LLM mockados, cobrindo a parte
automatizável de cada caso integrado.

Limitação assumida: a criação de playlist em conta Spotify **real** (CT-S3-INT-01
"grupo real") é uma demonstração manual, fora deste arquivo. Aqui validamos o
pipeline completo com serviços externos mockados.
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
from app.db.models import (
    AppSession,
    MusicSession,
    MusicSessionMember,
    PlaylistRun,
    PlaylistRunTrack,
    User,
    VibeCheckAnswer,
)
from app.db.session import get_db
from app.main import app


# ---------------------------------------------------------------------------
# Infra
# ---------------------------------------------------------------------------

@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 's3-int.sqlite3'}",
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


def _make_room(
    session_factory,
    *,
    code: str,
    occasion: str = "Festa de aniversário",
    description: str = "algo bem animado pra dançar",
    mode: str = "Democrático",
    members: int = 2,
):
    """Cria sala + host + N-1 convidados, todos com sessão válida. Retorna tokens."""
    db = session_factory()
    try:
        host = User(spotify_id=f"{code}_host", display_name="Host")
        db.add(host)
        db.flush()
        room = MusicSession(
            code=code,
            host_user_id=host.id,
            status="open",
            occasion=occasion,
            description=description,
            mode=mode,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
        db.add(room)
        db.flush()
        db.add(MusicSessionMember(session_id=room.id, user_id=host.id, role="host"))

        host_token = f"{code}-host-token"
        db.add(
            AppSession(
                user_id=host.id,
                session_token_hash=hashlib.sha256(host_token.encode()).hexdigest(),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
        )

        member_ids = [host.id]
        member_tokens = {host.id: host_token}
        for i in range(1, members):
            guest = User(spotify_id=f"{code}_guest{i}", display_name=f"Guest{i}")
            db.add(guest)
            db.flush()
            db.add(MusicSessionMember(session_id=room.id, user_id=guest.id, role="member"))
            token = f"{code}-guest{i}-token"
            db.add(
                AppSession(
                    user_id=guest.id,
                    session_token_hash=hashlib.sha256(token.encode()).hexdigest(),
                    expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
                )
            )
            member_ids.append(guest.id)
            member_tokens[guest.id] = token

        db.commit()
        return SimpleNamespace(
            room_id=room.id,
            code=code,
            host_id=host.id,
            member_ids=member_ids,
            tokens=member_tokens,
        )
    finally:
        db.close()


def _top_tracks(prefix: str, genre: str, total: int = 25) -> list[dict]:
    return [
        {
            "id": f"{prefix}{i:02d}",
            "name": f"{prefix}{i:02d}",
            "artists": [{"id": f"art-{prefix}{i:02d}", "name": f"Art{prefix}{i:02d}"}],
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
            "id": f"sp-{name}",
            "uri": f"spotify:track:{name}",
            "name": name,
            "artists": [{"name": f"Art{name}"}],
            "is_playable": True,
        }
    ]


def _spotify_mocks(stack, *, snapshot_by_user=None, search=_search_exact):
    """Aplica os patches padrão de Spotify. `snapshot_by_user` mapeia user_id→payload."""
    default_tracks = _top_tracks("track", "dance pop", 25)

    async def _snapshot(db, user_id, *, time_range="medium_term"):
        del db, time_range
        payload = (
            snapshot_by_user.get(user_id) if snapshot_by_user else None
        ) or {"tracks": default_tracks, "artists": []}
        return SimpleNamespace(
            snapshot=SimpleNamespace(
                top_tracks_json=payload["tracks"],
                top_artists_json=payload["artists"],
            )
        )

    stack.enter_context(
        patch(
            "app.services.generation_service.get_or_refresh_snapshot",
            new=AsyncMock(side_effect=_snapshot),
        )
    )
    stack.enter_context(
        patch(
            "app.clients.spotify_client.get_valid_access_token",
            new=AsyncMock(return_value="host-token"),
        )
    )
    stack.enter_context(
        patch("app.clients.spotify_client.search_track", new=AsyncMock(side_effect=search))
    )
    create = stack.enter_context(
        patch(
            "app.clients.spotify_client.create_playlist",
            new=AsyncMock(
                return_value={
                    "id": "pl-int",
                    "external_urls": {"spotify": "https://open.spotify.com/playlist/int"},
                }
            ),
        )
    )
    add_items = stack.enter_context(
        patch(
            "app.clients.spotify_client.add_items_to_playlist",
            new=AsyncMock(return_value={"snapshot_id": "snap"}),
        )
    )
    return create, add_items


# ===========================================================================
# CT-S3-INT-01 — Fluxo e2e completo (parte automatizável, Spotify mockado)
# ===========================================================================

def test_ct_s3_int_01_fluxo_completo_gera_playlist_e_resultado(client, session_factory):
    from contextlib import ExitStack

    room = _make_room(session_factory, code="S3INT01", members=2)
    with ExitStack() as stack:
        _spotify_mocks(stack)
        client.cookies.set(SESSION_COOKIE_NAME, room.tokens[room.host_id])
        gen = client.post(f"/rooms/{room.code}/generate")
        assert gen.status_code == 202, gen.text
        assert gen.json()["status"] == "completed"

        # host lê o resultado explicável
        result = client.get(f"/rooms/{room.code}/result")
        assert result.status_code == 200, result.text
        body = result.json()

    # Persistência: playlist real (mock) registrada no run.
    db = session_factory()
    try:
        run = db.query(PlaylistRun).filter_by(session_id=room.room_id).one()
        assert run.status == "completed"
        assert run.spotify_playlist_url
        matched = (
            db.query(PlaylistRunTrack)
            .filter_by(run_id=run.id, status="matched")
            .count()
        )
        assert matched >= 20  # regra 20–30 do PB-15
    finally:
        db.close()

    # Resultado tem métricas/representação (formato do PB-16).
    assert body, "resultado vazio"


def test_ct_s3_int_01_nao_membro_nao_ve_resultado(client, session_factory):
    """Segurança: só membro vê o resultado (403 para externo)."""
    from contextlib import ExitStack

    room = _make_room(session_factory, code="S3INT1B", members=1)
    with ExitStack() as stack:
        _spotify_mocks(stack)
        client.cookies.set(SESSION_COOKIE_NAME, room.tokens[room.host_id])
        assert client.post(f"/rooms/{room.code}/generate").status_code == 202

    # cria usuário externo com sessão válida, mas não membro
    db = session_factory()
    try:
        outsider = User(spotify_id="s3int1b_outsider", display_name="Outsider")
        db.add(outsider)
        db.flush()
        token = "s3int1b-outsider-token"
        db.add(
            AppSession(
                user_id=outsider.id,
                session_token_hash=hashlib.sha256(token.encode()).hexdigest(),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
        )
        db.commit()
    finally:
        db.close()

    client.cookies.set(SESSION_COOKIE_NAME, token)
    assert client.get(f"/rooms/{room.code}/result").status_code == 403


# ===========================================================================
# CT-S3-INT-02 — Contexto consumido pelo motor (via API, ponta a ponta)
# ===========================================================================

def test_ct_s3_int_02_ocasiao_diferente_muda_a_ordem_das_faixas(client, session_factory):
    """Mesmos snapshots/modo; só a ocasião muda → a ordem final das faixas muda."""
    from contextlib import ExitStack

    # Pool misto para o contexto poder discriminar.
    mixed = _top_tracks("party", "dance pop", 20) + _top_tracks("study", "acoustic instrumental", 20)
    snap = {"tracks": mixed, "artists": []}

    def _run(code, occasion, description):
        room = _make_room(
            session_factory, code=code, occasion=occasion, description=description, members=1
        )
        with ExitStack() as stack:
            _spotify_mocks(stack, snapshot_by_user={room.host_id: snap})
            client.cookies.set(SESSION_COOKIE_NAME, room.tokens[room.host_id])
            assert client.post(f"/rooms/{room.code}/generate").status_code == 202
        db = session_factory()
        try:
            run = db.query(PlaylistRun).filter_by(session_id=room.room_id).one()
            tracks = (
                db.query(PlaylistRunTrack)
                .filter_by(run_id=run.id)
                .order_by(PlaylistRunTrack.selection_rank)
                .all()
            )
            return [t.candidate_id for t in tracks], json.loads(run.llm_context_json)
        finally:
            db.close()

    party_order, party_ctx = _run("S3INT02P", "Festa", "balada muito animada pra dançar")
    study_order, study_ctx = _run("S3INT02S", "Estudo", "foco total, trabalho concentrado")

    # Contexto interpretado difere.
    assert party_ctx != study_ctx
    # A ordem final das faixas difere de forma coerente.
    assert party_order != study_order
    assert party_order[0].startswith("party")
    assert study_order[0].startswith("study")


# ===========================================================================
# CT-S3-INT-03 — Vibe Check influencia o ranking (baixa tolerância a tristeza)
# ===========================================================================

def test_ct_s3_int_03_vibe_check_penaliza_faixas_tristes(client, session_factory):
    """Um membro com valence (tolerância a tristeza) baixa deve penalizar faixas
    'sad' na seleção final. Se o Vibe Check não chega ao motor, a ordem não muda
    e este caso reprova (CT-S3-INT-03)."""
    from contextlib import ExitStack

    # Pool: faixas alegres vs tristes, todas igualmente conhecidas.
    happy = _top_tracks("happy", "happy pop", 20)
    sad = _top_tracks("sad", "sad", 20)
    snap = {"tracks": happy + sad, "artists": []}

    def _run_with_valence(code, valence):
        room = _make_room(
            session_factory, code=code, occasion="Encontro", description="tranquilo", members=1
        )
        # grava resposta de Vibe Check do host: valence baixa = pouca tolerância a tristeza
        db = session_factory()
        try:
            db.add(
                VibeCheckAnswer(
                    session_id=room.room_id,
                    user_id=room.host_id,
                    energy=0.5,
                    valence=valence,
                    popularity=0.5,
                )
            )
            db.commit()
        finally:
            db.close()
        with ExitStack() as stack:
            _spotify_mocks(stack, snapshot_by_user={room.host_id: snap})
            client.cookies.set(SESSION_COOKIE_NAME, room.tokens[room.host_id])
            assert client.post(f"/rooms/{room.code}/generate").status_code == 202
        db = session_factory()
        try:
            run = db.query(PlaylistRun).filter_by(session_id=room.room_id).one()
            tracks = (
                db.query(PlaylistRunTrack)
                .filter_by(run_id=run.id)
                .order_by(PlaylistRunTrack.selection_rank)
                .all()
            )
            return [t.candidate_id for t in tracks]
        finally:
            db.close()

    low_tolerance = _run_with_valence("S3INT03L", valence=0.0)   # não gosta de triste
    high_tolerance = _run_with_valence("S3INT03H", valence=1.0)  # tolera triste

    # Com baixa tolerância, faixas 'sad' devem ficar mais para o fim do que com alta.
    def _sad_rank_sum(order):
        return sum(i for i, tid in enumerate(order) if tid.startswith("sad"))

    assert _sad_rank_sum(low_tolerance) > _sad_rank_sum(high_tolerance), (
        "Vibe Check (valence baixa) não penalizou faixas tristes: as preferências "
        "derivadas não chegam ao motor de ranqueamento (CT-S3-INT-03)."
    )


# ===========================================================================
# CT-S3-INT-05 — Falha de serviço externo não invalida o fluxo
# ===========================================================================

def test_ct_s3_int_05_llm_indisponivel_e_faixas_nao_encontradas(client, session_factory):
    """LLM fora + parte das buscas sem resultado → playlist ainda é criada com
    as faixas válidas; descartes ficam motivados; sem crash."""
    from contextlib import ExitStack

    tracks = _top_tracks("track", "dance pop", 28)
    snap = {"tracks": tracks, "artists": []}

    async def _flaky_search(_token, query, *, market="from_token", limit=3):
        del market, limit
        name = query.split()[0]
        # As 5 primeiras faixas não são encontradas.
        idx = int(name.removeprefix("track"))
        if idx < 5:
            return []
        return [
            {
                "id": f"sp-{name}",
                "uri": f"spotify:track:{name}",
                "name": name,
                "artists": [{"name": f"Art{name}"}],
                "is_playable": True,
            }
        ]

    room = _make_room(session_factory, code="S3INT05", members=1)
    with ExitStack() as stack:
        _spotify_mocks(stack, snapshot_by_user={room.host_id: snap}, search=_flaky_search)
        # LLM indisponível: httpx.post levanta erro → fallback determinístico.
        stack.enter_context(
            patch("httpx.AsyncClient.post", new=AsyncMock(side_effect=RuntimeError("ollama down")))
        )
        client.cookies.set(SESSION_COOKIE_NAME, room.tokens[room.host_id])
        gen = client.post(f"/rooms/{room.code}/generate")
        assert gen.status_code == 202, gen.text
        assert gen.json()["status"] == "completed"

    db = session_factory()
    try:
        run = db.query(PlaylistRun).filter_by(session_id=room.room_id).one()
        # fallback: contexto persistido mesmo sem LLM
        assert run.llm_context_json is not None
        not_found = (
            db.query(PlaylistRunTrack)
            .filter_by(run_id=run.id, status="discarded")
            .filter(PlaylistRunTrack.discard_reason.contains("No results"))
            .count()
        )
        assert not_found == 5, f"esperava 5 descartes 'não encontrado', obtive {not_found}"
        matched = (
            db.query(PlaylistRunTrack).filter_by(run_id=run.id, status="matched").count()
        )
        assert matched >= 20
    finally:
        db.close()


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
