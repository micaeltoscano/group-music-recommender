"""Testes exploratórios de QA para PB-16 (Resultado e explicabilidade).

Complementam `test_pb16_resultado_qa.py` com edge cases e verificação
independente dos critérios de aceitação, incluindo privacidade e o
comportamento das métricas de compatibilidade/fairness.
"""

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone

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
)
from app.db.session import get_db
from app.main import app
from app.services import generation_service


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pb16_explor.sqlite3'}",
        connect_args={"check_same_thread": False, "timeout": 30},
        future=True,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
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


def _authenticated_user(session_factory, spotify_id: str, display_name: str) -> str:
    raw_token = f"qa-session-for-{spotify_id}"
    db = session_factory()
    try:
        user = db.query(User).filter(User.spotify_id == spotify_id).first()
        if not user:
            user = User(spotify_id=spotify_id, display_name=display_name)
            db.add(user)
            db.flush()
        db.add(
            AppSession(
                user_id=user.id,
                session_token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
        )
        db.commit()
        return raw_token
    finally:
        db.close()


def _act_as(client: TestClient, token: str) -> None:
    client.cookies.set(SESSION_COOKIE_NAME, token)


def _seed_room(session_factory, *, code, run_status, tracks_spec, playlist_url):
    """Cria sala VIBE com Alice(host), Bob, Charlie e um run com o status pedido."""
    db = session_factory()
    try:
        u1 = User(spotify_id=f"{code}-u1", display_name="Alice")
        u2 = User(spotify_id=f"{code}-u2", display_name="Bob")
        u3 = User(spotify_id=f"{code}-u3", display_name="Charlie")
        db.add_all([u1, u2, u3])
        db.flush()

        room = MusicSession(
            code=code,
            host_user_id=u1.id,
            status="open",
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )
        db.add(room)
        db.flush()

        db.add_all(
            [
                MusicSessionMember(session_id=room.id, user_id=u1.id, role="host"),
                MusicSessionMember(session_id=room.id, user_id=u2.id, role="member"),
                MusicSessionMember(session_id=room.id, user_id=u3.id, role="member"),
            ]
        )
        db.flush()

        run = PlaylistRun(session_id=room.id, status=run_status, spotify_playlist_url=playlist_url)
        db.add(run)
        db.flush()

        ids = {"u1": u1.id, "u2": u2.id, "u3": u3.id}
        run_id = run.id
        for i, (name, source_users) in enumerate(tracks_spec):
            if source_users == "invalid":
                source = "invalid"
            else:
                source = json.dumps([ids[key] for key in source_users])
            db.add(
                PlaylistRunTrack(
                    run_id=run.id,
                    candidate_id=uuid.uuid4().hex,
                    name=name,
                    artist=f"Art {i}",
                    status="matched",
                    match_confidence=1.0,
                    spotify_uri=f"uri:{i}",
                    source=source,
                )
            )
        db.commit()
        ids["run_id"] = run_id
        return ids
    finally:
        db.close()


# --------------------------------------------------------------------------
# Edge cases de estado do run (critério 1/2: só resultado de execução concluída)
# --------------------------------------------------------------------------

@pytest.mark.parametrize("run_status", ["running", "failed"])
def test_run_nao_concluido_retorna_404(client, session_factory, run_status):
    _seed_room(
        session_factory,
        code="VIBEX1",
        run_status=run_status,
        tracks_spec=[("T", ["u1"])],
        playlist_url="https://open.spotify.com/playlist/x",
    )
    token = _authenticated_user(session_factory, "VIBEX1-u1", "Alice")
    _act_as(client, token)
    resp = client.get("/rooms/VIBEX1/result")
    assert resp.status_code == 404


def test_sala_inexistente_retorna_404(client, session_factory):
    token = _authenticated_user(session_factory, "ghost", "Ghost")
    _act_as(client, token)
    resp = client.get("/rooms/NAOEXISTE/result")
    assert resp.status_code == 404


# --------------------------------------------------------------------------
# Critério 3: representação por integrante coerente com as fontes
# --------------------------------------------------------------------------

def test_representacao_percentuais_coerentes(client, session_factory):
    # u1 em 2 de 4, u2 em 2 de 4, u3 em 1 de 4
    _seed_room(
        session_factory,
        code="VIBER1",
        run_status="completed",
        tracks_spec=[
            ("A", ["u1", "u2"]),
            ("B", ["u2", "u3"]),
            ("C", ["u1"]),
            ("D", "invalid"),
        ],
        playlist_url="https://open.spotify.com/playlist/r",
    )
    token = _authenticated_user(session_factory, "VIBER1-u1", "Alice")
    _act_as(client, token)
    resp = client.get("/rooms/VIBER1/result")
    assert resp.status_code == 200
    data = resp.json()

    pct = {r["display_name"]: r["percentage"] for r in data["representation"]}
    assert pct == {"Alice": 50, "Bob": 50, "Charlie": 25}
    # métricas presentes e inteiras (critério 2 — só presença/formato)
    assert isinstance(data["compatibility_score"], int)
    assert isinstance(data["fairness_score"], int)


def test_source_malformado_nao_quebra_e_cai_no_agregado(client, session_factory):
    _seed_room(
        session_factory,
        code="VIBEM1",
        run_status="completed",
        tracks_spec=[("D", "invalid")],
        playlist_url="https://open.spotify.com/playlist/m",
    )
    token = _authenticated_user(session_factory, "VIBEM1-u1", "Alice")
    _act_as(client, token)
    resp = client.get("/rooms/VIBEM1/result")
    assert resp.status_code == 200
    track = resp.json()["tracks"][0]
    assert track["contributed_by"] == []
    assert track["reason"]  # há um motivo agregado, sem nomear ninguém


# --------------------------------------------------------------------------
# Critério 5 / R-08: comportamento de privacidade das explicações
# --------------------------------------------------------------------------

def test_privacidade_nenhum_texto_de_rejeicao(client, session_factory):
    """CT-PB16-05: nenhuma faixa expõe rejeição/veto de terceiros."""
    _seed_room(
        session_factory,
        code="VIBEP1",
        run_status="completed",
        tracks_spec=[("A", ["u1", "u2"]), ("C", ["u1"]), ("D", "invalid")],
        playlist_url="https://open.spotify.com/playlist/p",
    )
    token = _authenticated_user(session_factory, "VIBEP1-u2", "Bob")
    _act_as(client, token)
    resp = client.get("/rooms/VIBEP1/result")
    assert resp.status_code == 200
    blob = json.dumps(resp.json()).lower()
    for termo in ("rejeit", "vetou", "veto", "bloqueou", "odeia", "não tolera", "baixa tolerância"):
        assert termo not in blob


def test_justificativa_agregada_nao_nomeia_individuo(client, session_factory):
    """DEF-PB16-03 resolvido: a justificativa (`reason`) de uma faixa de fonte
    única é agregada e NÃO nomeia o integrante. O crédito positivo por integrante
    permanece em `contributed_by` (decisão de produto — grupo consensual).
    """
    _seed_room(
        session_factory,
        code="VIBEP2",
        run_status="completed",
        tracks_spec=[("C", ["u1"])],  # fonte única (Alice)
        playlist_url="https://open.spotify.com/playlist/p2",
    )
    # Bob (outro integrante) consulta o resultado
    token = _authenticated_user(session_factory, "VIBEP2-u2", "Bob")
    _act_as(client, token)
    resp = client.get("/rooms/VIBEP2/result")
    assert resp.status_code == 200
    track = resp.json()["tracks"][0]
    # `reason` não expõe o nome individual...
    assert "Alice" not in track["reason"]
    # ...mas o crédito positivo permanece disponível em contributed_by (by-design).
    assert "Alice" in track["contributed_by"]


# --------------------------------------------------------------------------
# DEF-PB16-01: métricas são calculadas e PERSISTIDAS pela execução (não fabricadas)
# --------------------------------------------------------------------------

def test_metricas_persistidas_pela_execucao_refletem_distribuicao(client, session_factory):
    """A conclusão do run persiste compatibility/fairness/explanation no próprio
    run; o endpoint apenas lê. Distribuição desigual => fairness (Jain) < 100.
    """
    # Todas as 3 faixas vêm só de Alice (u1): u1=100%, Bob e Charlie=0%.
    seeded = _seed_room(
        session_factory,
        code="VIBEF1",
        run_status="running",  # ainda não concluído
        tracks_spec=[("A", ["u1"]), ("B", ["u1"]), ("C", ["u1"])],
        playlist_url="https://open.spotify.com/playlist/f1",
    )

    # Antes de concluir: métricas não existem
    db = session_factory()
    try:
        run = db.query(PlaylistRun).filter(PlaylistRun.id == seeded["run_id"]).one()
        assert run.compatibility_score is None
        assert run.fairness_score is None
        assert run.explanation_json is None
    finally:
        db.close()

    # Conclui a execução (persiste as métricas)
    db = session_factory()
    try:
        generation_service.complete_generation(db, seeded["run_id"])
    finally:
        db.close()

    # Depois de concluir: métricas persistidas e coerentes
    db = session_factory()
    try:
        run = db.query(PlaylistRun).filter(PlaylistRun.id == seeded["run_id"]).one()
        assert run.status == "completed"
        assert run.compatibility_score == 0  # nenhuma faixa com 2+ contribuintes
        # Jain para [3,0,0] = 3^2 / (3 * 3^2) = 1/3 -> 33
        assert run.fairness_score == 33
        stored = json.loads(run.explanation_json)
        assert "representation" in stored and "why_items" in stored
    finally:
        db.close()

    # O endpoint devolve exatamente o que foi persistido
    token = _authenticated_user(session_factory, "VIBEF1-u2", "Bob")
    _act_as(client, token)
    resp = client.get("/rooms/VIBEF1/result")
    assert resp.status_code == 200
    data = resp.json()
    assert data["compatibility_score"] == 0
    assert data["fairness_score"] == 33
    pct = {r["display_name"]: r["percentage"] for r in data["representation"]}
    assert pct == {"Alice": 100, "Bob": 0, "Charlie": 0}
    # why_items reflete a realidade: há integrantes sem representação
    assert any("sem faixa" in w for w in data["why_items"])
