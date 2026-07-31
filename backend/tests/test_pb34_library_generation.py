"""PB-34 — API, geração/fallback, identidade nativa e privacidade agregada."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.auth import get_current_user
from app.db.base import Base
from app.db.models import User, UserMusicSnapshot, UserPlaylistInventory
from app.db.session import get_db
from app.engine.scoring import calculate_individual_score
from app.engine.taste import UserTasteProfile
from app.main import app
from app.services.library_application_service import load_library_generation_data
from app.services.library_sync_service import (
    LibrarySyncQuotaExceeded,
    LibrarySyncRateLimited,
    LibrarySyncUnavailable,
)
from app.services.music_library_service import rebuild_music_library
from app.services.result_service import _library_mix_explanation


NOW = datetime.now(timezone.utc)


def _track(track_id: str):
    return {
        "id": track_id,
        "uri": f"spotify:track:{track_id}",
        "name": track_id,
        "artists": [{"id": f"Artist{track_id}", "name": "Artista"}],
    }


@pytest.fixture()
def environment(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'pb34.sqlite3'}", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    db = factory()
    user = User(spotify_id="PB34", display_name="PB34")
    db.add(user)
    db.flush()
    db.add(
        UserMusicSnapshot(
            user_id=user.id,
            time_range="medium_term",
            top_tracks_json=[_track("Top01")],
            top_artists_json=[],
            fetched_at=NOW,
        )
    )
    db.add(
        UserPlaylistInventory(
            user_id=user.id,
            spotify_playlist_id="PrivatePlaylistId",
            access_type="owned",
            tracks_total=1,
            snapshot_id="PrivateSnapshotId",
            verified_at=NOW,
        )
    )
    db.commit()
    rebuild_music_library(
        db,
        user.id,
        playlist_tracks_by_id={"PrivatePlaylistId": [_track("Playlist01")]},
        built_at=NOW - timedelta(hours=2),
    )

    def override_db():
        session = factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: {
        "id": user.id,
        "spotify_id": user.spotify_id,
    }
    try:
        with TestClient(app) as client:
            yield client, factory, user.id
    finally:
        app.dependency_overrides.clear()
        db.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_ct_pb34_01_status_sanitizado_sem_lista_privada(environment):
    client, _factory, _user_id = environment
    response = client.get("/me/music-library")
    payload = response.json()

    assert response.status_code == 200
    assert payload["state"] == "ready"
    assert payload["track_count"] == 2
    assert payload["origins"] == {"top": 1, "playlist": 1}
    assert "PrivatePlaylistId" not in response.text
    assert "Playlist01" not in response.text
    assert set(payload) == {
        "state", "track_count", "age_seconds", "stale", "warning_code",
        "retry_after", "origins",
    }


def test_ct_pb34_02_refresh_fresco_e_idempotente(environment, monkeypatch):
    client, _factory, user_id = environment
    calls = []

    async def sync(_db, received_user_id):
        calls.append(received_user_id)

    monkeypatch.setattr("app.api.music.sync_music_library", sync)
    first = client.post("/me/refresh-music-library")
    second = client.post("/me/refresh-music-library")

    assert first.status_code == second.status_code == 200
    assert first.json()["track_count"] == second.json()["track_count"] == 2
    assert calls == [user_id, user_id]


def test_ct_pb34_02_rate_limit_e_acionavel(environment, monkeypatch):
    client, _factory, _user_id = environment

    async def limited(*_args, **_kwargs):
        raise LibrarySyncRateLimited(23)

    monkeypatch.setattr("app.api.music.sync_music_library", limited)
    response = client.post("/me/refresh-music-library")
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "23"
    assert response.json()["detail"]["code"] == "RATE_LIMITED"


@pytest.mark.parametrize(
    ("failure", "expected_status", "expected_code"),
    [
        (LibrarySyncQuotaExceeded(), 503, "QUOTA_EXCEEDED"),
        (LibrarySyncUnavailable("REAUTH_REQUIRED"), 401, "REAUTH_REQUIRED"),
    ],
)
def test_ct_pb34_02_quota_e_reauth_distintos(
    environment, monkeypatch, failure, expected_status, expected_code
):
    client, _factory, _user_id = environment

    async def fail(*_args, **_kwargs):
        raise failure

    monkeypatch.setattr("app.api.music.sync_music_library", fail)
    response = client.post("/me/refresh-music-library")
    assert response.status_code == expected_status
    assert response.json()["detail"]["code"] == expected_code


def test_ct_pb34_03_home_contem_estados_e_acoes_sem_tela_nova():
    from pathlib import Path

    root = Path(__file__).parents[2]
    home = (root / "frontend/src/Home.jsx").read_text(encoding="utf-8")
    api = (root / "frontend/src/apiClient.js").read_text(encoding="utf-8")
    assert "library-status-card" in home
    assert "Consultando biblioteca" in home
    assert "atualização recomendada" in home
    assert "refreshMusicLibrary" in home and "getMusicLibrary" in api


def test_ct_pb34_04_biblioteca_pronta_gera_pool_e_ausente_cai_para_top(environment):
    _client, factory, user_id = environment
    db = factory()
    try:
        ready = load_library_generation_data(db, [user_id])
        assert ready is not None
        assert len(ready.profiles[0].tracks) == 2
        assert {candidate.id for candidate in ready.candidates} == {"Top01", "Playlist01"}
        assert load_library_generation_data(db, [user_id, 999999]) is None
    finally:
        db.close()


def test_ct_pb34_05_nativa_reusa_id_uri_e_peso_de_playlist(environment):
    _client, factory, user_id = environment
    db = factory()
    try:
        data = load_library_generation_data(db, [user_id])
        candidate = next(item for item in data.candidates if item.id == "Playlist01")
        profile = UserTasteProfile(user_id, {"items": []}, {"items": []})
        score = calculate_individual_score(
            candidate,
            profile,
            {"track_affinity": 1.0, "artist_affinity": 0.0, "genre_affinity": 0.0,
             "popularity": 0.0, "novelty": 0.0},
        )
        assert candidate.raw_data["uri"] == "spotify:track:Playlist01"
        assert candidate.preference_by_user[user_id] == 0.45
        assert score == 0.45
    finally:
        db.close()


def test_ct_pb34_06_explicacao_e_somente_agregada():
    explanation = _library_mix_explanation({"top": 50, "playlist": 30, "context": 20})
    assert explanation == "Origens agregadas: 50% Tops, 30% playlists e 20% contexto."
    assert "PlaylistId" not in explanation
    assert "user" not in explanation.lower()
