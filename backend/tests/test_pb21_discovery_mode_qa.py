"""QA (validador independente) — PB-21 (Modo Descoberta).

Sondagem adversarial da autoridade de QA, além dos testes do Dev:

- CT-PB21-01/02: portão da feature flag é **server-side** (não só na lista da
  API) e a rejeição não altera a sala; não-host não seleciona nem com a flag on.
- CT-PB21-03: propriedade de score — uma candidata nova/diversa pontua mais alto
  sob 'discovery' do que sob 'democratic'; e sobe de posição no ranking.
- CT-PB21-04: veto forte continua penalizando sob 'discovery' (penalidade 0.75).
- Backward-compat (mutação): o sinal de diversidade, agora sempre calculado, NÃO
  altera os modos existentes (peso de diversidade 0.0).
- CT-PB21-05: explicação de Descoberta só aparece nesse modo.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

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
    User,
)
from app.db.session import get_db
from app.engine.candidates import CandidateTrack
from app.engine.context_scoring import ContextCriteria
from app.engine.fairness import evaluate_candidate_fairness
from app.engine.scoring import calculate_group_score
from app.engine.taste import UserTasteProfile
from app.engine.weights import CONSENSUS_MODES
from app.main import app
from app.services.generation_service import _rank_candidates


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pb21-qa.sqlite3'}",
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


def _seed(session_factory, *, with_member=False):
    db = session_factory()
    try:
        host = User(spotify_id="pb21qa-host", display_name="Host")
        db.add(host)
        db.flush()
        exp = datetime.now(timezone.utc) + timedelta(hours=1)
        db.add(AppSession(user_id=host.id, session_token_hash=hashlib.sha256(b"host-t").hexdigest(),
                          expires_at=exp))
        room = MusicSession(code="DSCV-QA01", host_user_id=host.id, status="open", expires_at=exp)
        db.add(room)
        db.flush()
        db.add(MusicSessionMember(session_id=room.id, user_id=host.id, role="host"))
        out = {"host_id": host.id, "room_id": room.id, "code": "DSCV-QA01"}
        if with_member:
            m = User(spotify_id="pb21qa-member", display_name="Member")
            db.add(m)
            db.flush()
            db.add(AppSession(user_id=m.id, session_token_hash=hashlib.sha256(b"member-t").hexdigest(),
                              expires_at=exp))
            db.add(MusicSessionMember(session_id=room.id, user_id=m.id, role="member"))
            out["member_id"] = m.id
        db.commit()
        return out
    finally:
        db.close()


# ---------------------------------------------------------------------------
# CT-PB21-01 / 02 — portão server-side da flag
# ---------------------------------------------------------------------------

def test_flag_off_oculta_e_rejeita_sem_alterar_sala(client, session_factory, monkeypatch):
    monkeypatch.setattr(settings, "discovery_mode_enabled", False)
    ids = _seed(session_factory)
    client.cookies.set(SESSION_COOKIE_NAME, "host-t")

    modes = client.get("/rooms/consensus-modes").json()["modes"]
    assert "Descoberta" not in modes

    resp = client.put(f"/rooms/{ids['code']}/mode", json={"mode": "Descoberta"})
    assert resp.status_code == 422, resp.text

    db = session_factory()
    try:
        assert db.get(MusicSession, ids["room_id"]).mode is None, "modo não pode ter sido persistido"
    finally:
        db.close()


def test_flag_on_anuncia_e_persiste(client, session_factory, monkeypatch):
    monkeypatch.setattr(settings, "discovery_mode_enabled", True)
    ids = _seed(session_factory)
    client.cookies.set(SESSION_COOKIE_NAME, "host-t")

    assert "Descoberta" in client.get("/rooms/consensus-modes").json()["modes"]
    resp = client.put(f"/rooms/{ids['code']}/mode", json={"mode": "Descoberta"})
    assert resp.status_code == 200, resp.text

    db = session_factory()
    try:
        assert db.get(MusicSession, ids["room_id"]).mode == "Descoberta"
    finally:
        db.close()


def test_flag_on_mas_nao_host_nao_seleciona(client, session_factory, monkeypatch):
    monkeypatch.setattr(settings, "discovery_mode_enabled", True)
    ids = _seed(session_factory, with_member=True)
    client.cookies.set(SESSION_COOKIE_NAME, "member-t")
    resp = client.put(f"/rooms/{ids['code']}/mode", json={"mode": "Descoberta"})
    assert resp.status_code == 403, resp.text
    db = session_factory()
    try:
        assert db.get(MusicSession, ids["room_id"]).mode is None
    finally:
        db.close()


# ---------------------------------------------------------------------------
# CT-PB21-03 — novidade/diversidade recebem peso superior
# ---------------------------------------------------------------------------

def test_pesos_de_novidade_e_diversidade_sao_superiores():
    disc = CONSENSUS_MODES["discovery"]
    dem = CONSENSUS_MODES["democratic"]
    assert disc["individual"]["novelty"] > dem["individual"]["novelty"]
    assert disc["group"]["diversity"] > 0.0
    assert dem["group"]["diversity"] == 0.0


def _candidate(track_id, *, artist_id, genre, release):
    return CandidateTrack(
        track_id,
        {
            "id": track_id,
            "name": track_id,
            "artists": [{"id": artist_id, "name": artist_id}],
            "genres": [genre],
            "popularity": 50,
            "album": {"name": "Al", "release_date": release},
        },
        {1},
    )


def _profile_knowing(track_ids, artist_ids, genres):
    p = UserTasteProfile(1, {}, {})
    p.tracks = set(track_ids)
    p.artists = set(artist_ids)
    p.genres = set(genres)
    return p


def test_candidata_nova_e_diversa_pontua_mais_sob_descoberta():
    """Mesma candidata nova/diversa: group_score sob 'discovery' > sob 'democratic'."""
    novel = _candidate("novel", artist_id="unknown-art", genre="experimental", release="2026")
    profile = _profile_knowing({"fam"}, {"known-art"}, {"pop"})

    # diversidade real: artista/gênero desconhecidos → 1.0
    from app.engine.scoring import calculate_candidate_diversity_score
    div = calculate_candidate_diversity_score(novel, [profile])
    assert div == 1.0

    disc = calculate_group_score(novel, [profile], CONSENSUS_MODES["discovery"]["individual"],
                                 CONSENSUS_MODES["discovery"]["group"], context_score=0.5,
                                 diversity_score=div)["group_score"]
    dem = calculate_group_score(novel, [profile], CONSENSUS_MODES["democratic"]["individual"],
                                CONSENSUS_MODES["democratic"]["group"], context_score=0.5,
                                diversity_score=div)["group_score"]
    assert disc > dem, f"discovery {disc} deveria superar democratic {dem} para candidata nova/diversa"


def test_candidata_nova_sobe_no_ranking_sob_descoberta():
    """Num pool, a candidata nova/diversa ocupa posição melhor sob 'discovery'."""
    known_tracks = [f"fam{i}" for i in range(3)]
    profile = _profile_knowing(set(known_tracks), {"known-art"}, {"pop"})
    # 3 fortemente familiares (topo em ambos os modos)
    pool = [
        _candidate(tid, artist_id="known-art", genre="pop", release="2017")
        for tid in known_tracks
    ]
    # 3 "medianas": artista/gênero conhecidos, mas faixa não conhecida e antigas
    pool += [
        _candidate(f"weak{i}", artist_id="known-art", genre="pop", release="2016")
        for i in range(3)
    ]
    novel = _candidate("novel", artist_id="unknown-art", genre="experimental", release="2026")
    pool.append(novel)
    ctx = ContextCriteria(occasion="", mood="", energy="media")

    dem_rank = [c.id for c in _rank_candidates(pool, [profile], "Democrático", ctx)]
    disc_rank = [c.id for c in _rank_candidates(pool, [profile], "Descoberta", ctx)]
    assert disc_rank.index("novel") < dem_rank.index("novel"), (
        f"'novel' deveria subir sob discovery: dem={dem_rank.index('novel')} "
        f"disc={disc_rank.index('novel')}"
    )


# ---------------------------------------------------------------------------
# CT-PB21-04 — veto forte continua penalizando sob 'discovery'
# ---------------------------------------------------------------------------

def test_veto_forte_penaliza_sob_descoberta():
    disc = CONSENSUS_MODES["discovery"]
    vetoed = {"group_score": 0.8, "average_score": 0.5, "min_user_score": 0.0,
              "individual_scores": [0.9, 0.0]}  # 0.0 <= 0.05 → veto
    clean = {"group_score": 0.8, "average_score": 0.5, "min_user_score": 0.5,
             "individual_scores": [0.9, 0.5]}
    ev_vetoed = evaluate_candidate_fairness(vetoed, disc)
    ev_clean = evaluate_candidate_fairness(clean, disc)
    # penalidade 0.75 → penalized = 0.8 * 0.25 = 0.2
    assert ev_vetoed["penalized_score"] == pytest.approx(0.2, abs=1e-4)
    assert ev_vetoed["penalized_score"] < ev_clean["penalized_score"]


# ---------------------------------------------------------------------------
# Backward-compat (mutação): diversidade sempre calculada NÃO muda modos antigos
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", ["democratic", "safe_party"])
def test_diversidade_nao_altera_modos_existentes(mode):
    cand = _candidate("x", artist_id="a", genre="pop", release="2020")
    profile = _profile_knowing({"x"}, {"a"}, {"pop"})
    weights = CONSENSUS_MODES[mode]
    base = calculate_group_score(cand, [profile], weights["individual"], weights["group"],
                                 context_score=0.5, diversity_score=0.0)["group_score"]
    with_div = calculate_group_score(cand, [profile], weights["individual"], weights["group"],
                                     context_score=0.5, diversity_score=1.0)["group_score"]
    assert base == with_div, f"diversidade não deveria afetar o modo {mode} (peso 0.0)"


# ---------------------------------------------------------------------------
# CT-PB21-05 — explicação só no modo Descoberta
# ---------------------------------------------------------------------------

def test_explicacao_descoberta_presente_apenas_nesse_modo(session_factory):
    from app.services.result_service import DISCOVERY_EXPLANATION, build_room_result
    from app.db.models import PlaylistRun

    db = session_factory()
    try:
        host = User(spotify_id="pb21qa-exp", display_name="H")
        db.add(host)
        db.flush()
        exp = datetime.now(timezone.utc) + timedelta(hours=1)
        for code, mode in (("EXPD01", "Descoberta"), ("EXPO01", "Democrático")):
            room = MusicSession(code=code, host_user_id=host.id, status="completed",
                                mode=mode, expires_at=exp)
            db.add(room)
            db.flush()
            db.add(MusicSessionMember(session_id=room.id, user_id=host.id, role="host"))
            run = PlaylistRun(session_id=room.id, status="completed",
                              compatibility_score=0.5, fairness_score=0.5)
            db.add(run)
            db.flush()
            result = build_room_result(db, room, run)
            why_items = result.why_items or []
            if mode == "Descoberta":
                assert DISCOVERY_EXPLANATION in why_items, \
                    "explicação de Descoberta deveria aparecer"
            else:
                assert DISCOVERY_EXPLANATION not in why_items, \
                    "explicação de Descoberta não deveria aparecer em outro modo"
    finally:
        db.close()
