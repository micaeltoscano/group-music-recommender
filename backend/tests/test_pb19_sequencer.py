"""Testes do Dev para o PB-19 — Playlist Experience Sequencer."""

from __future__ import annotations

import asyncio
import uuid
from collections import Counter
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.db.models import PlaylistRun, PlaylistRunTrack
from app.engine.sequencer import SequencerTrack, sequence_tracks
from app.services.generation_service import create_spotify_playlist_for_run


def _track(
    track_id: str,
    artist: str,
    acceptance: float,
    risk: float,
    position: int,
) -> SequencerTrack:
    return SequencerTrack(track_id, artist, acceptance, risk, position)


def _artists(tracks: list[SequencerTrack]) -> list[str]:
    return [track.artist.strip().casefold() for track in tracks]


# ---------------------------------------------------------------------------
# CT-PB19-01 — sem duas faixas do mesmo artista consecutivas
# ---------------------------------------------------------------------------


def test_sequenciador_evitar_artistas_consecutivos_quando_ha_solucao():
    tracks = [
        _track("a1", "Artist A", 1.00, 0.05, 1),
        _track("a2", "Artist A", 0.90, 0.20, 2),
        _track("b1", "Artist B", 0.85, 0.30, 3),
        _track("b2", "Artist B", 0.75, 0.50, 4),
        _track("c1", "Artist C", 0.70, 0.70, 5),
        _track("c2", "Artist C", 0.60, 0.90, 6),
    ]

    ordered = sequence_tracks(tracks)
    artists = _artists(ordered)

    assert all(current != following for current, following in zip(artists, artists[1:]))
    assert {track.track_id for track in ordered} == {track.track_id for track in tracks}


def test_abertura_nao_cria_adjacencia_inevitavel_no_final():
    tracks = [
        _track("a1", "A", 0.80, 0.20, 2),
        _track("a2", "A", 0.70, 0.30, 3),
        _track("b1", "B", 1.00, 0.10, 1),
    ]

    ordered = sequence_tracks(tracks)

    assert _artists(ordered) == ["a", "b", "a"]


# ---------------------------------------------------------------------------
# CT-PB19-02 — abertura de alta aceitação
# ---------------------------------------------------------------------------


def test_primeira_faixa_tem_maior_aceitacao():
    tracks = [
        _track("medium", "B", 0.70, 0.30, 2),
        _track("strong", "A", 0.98, 0.10, 1),
        _track("risky", "C", 0.30, 0.95, 3),
    ]

    ordered = sequence_tracks(tracks)

    assert ordered[0].track_id == "strong"
    assert ordered[0].acceptance == max(track.acceptance for track in tracks)


# ---------------------------------------------------------------------------
# CT-PB19-03 — maior risco no meio
# ---------------------------------------------------------------------------


def test_faixas_de_maior_risco_ficam_na_regiao_intermediaria():
    tracks = [
        _track(
            f"track-{index}",
            f"Artist {index}",
            acceptance=1.0 - (index * 0.08),
            risk=index * 0.1,
            position=index + 1,
        )
        for index in range(9)
    ]

    ordered = sequence_tracks(tracks)
    positions = {track.track_id: index for index, track in enumerate(ordered)}

    assert 2 <= positions["track-8"] <= 6
    assert 2 <= positions["track-7"] <= 6
    assert positions["track-8"] not in {0, len(ordered) - 1}


# ---------------------------------------------------------------------------
# CT-PB19-04 — cap de duas por artista
# ---------------------------------------------------------------------------


def test_cap_de_duas_faixas_por_artista_e_preservado():
    tracks = [
        _track(f"a{index}", "Artist A", 1.0 - index * 0.05, index * 0.1, index)
        for index in range(1, 5)
    ] + [
        _track(f"b{index}", "Artist B", 0.8 - index * 0.05, index * 0.1, index + 4)
        for index in range(1, 4)
    ] + [_track("c1", "Artist C", 0.5, 0.5, 8)]

    ordered = sequence_tracks(tracks, max_per_artist=2)
    counts = Counter(_artists(ordered))

    assert counts == {"artist a": 2, "artist b": 2, "artist c": 1}
    assert {track.track_id for track in ordered if track.artist == "Artist A"} == {"a1", "a2"}


# ---------------------------------------------------------------------------
# CT-PB19-05 — entradas mínimas e melhor esforço
# ---------------------------------------------------------------------------


def test_entrada_vazia_ou_pequena_nao_falha():
    single = _track("only", "Solo", 0.7, 0.4, 1)

    assert sequence_tracks([]) == []
    assert sequence_tracks([single]) == [single]


def test_artista_unico_degrada_graciosamente_e_respeita_cap():
    tracks = [
        _track(f"solo-{index}", "Solo", 1.0 - index * 0.1, index * 0.1, index + 1)
        for index in range(5)
    ]

    ordered = sequence_tracks(tracks)

    assert [track.track_id for track in ordered] == ["solo-0", "solo-1"]


def test_resultado_e_deterministico_em_empates():
    tracks = [
        _track(f"track-{index}", f"Artist {index % 3}", 0.5, 0.5, 0)
        for index in range(8)
    ]

    first = sequence_tracks(tracks)
    second = sequence_tracks(list(reversed(tracks)))

    assert [track.track_id for track in first] == [track.track_id for track in second]


def test_parametros_de_limite_invalidos_sao_rejeitados():
    with pytest.raises(ValueError):
        sequence_tracks([], max_per_artist=0)
    with pytest.raises(ValueError):
        sequence_tracks([], limit=-1)


# ---------------------------------------------------------------------------
# Integração — a ordem persistida é a mesma enviada ao Spotify
# ---------------------------------------------------------------------------


def _mock_db(run_id: uuid.UUID, tracks: list[PlaylistRunTrack]) -> MagicMock:
    db = MagicMock()
    run = PlaylistRun(id=run_id, status="running")

    run_query = MagicMock()
    run_query.with_for_update.return_value = run_query
    run_query.filter.return_value = run_query
    run_query.one.return_value = run

    tracks_query = MagicMock()
    tracks_query.filter.return_value = tracks_query
    tracks_query.order_by.return_value = tracks_query
    tracks_query.all.return_value = tracks

    def query(model):
        return run_query if model is PlaylistRun else tracks_query

    db.query.side_effect = query
    return db


@patch("app.clients.spotify_client.create_playlist", new_callable=AsyncMock)
@patch("app.clients.spotify_client.add_items_to_playlist", new_callable=AsyncMock)
def test_ordem_final_e_enviada_ao_spotify_e_persistida(
    mock_add_items,
    mock_create_playlist,
):
    run_id = uuid.uuid4()
    tracks = [
        PlaylistRunTrack(
            id=uuid.uuid4(),
            run_id=run_id,
            candidate_id=f"candidate-{index}",
            name=f"Track {index}",
            artist=f"Artist {index // 2}",
            spotify_uri=f"uri:{index:02d}",
            status="matched",
            selection_rank=index + 1,
        )
        for index in range(22)
    ]
    db = _mock_db(run_id, tracks)
    mock_create_playlist.return_value = {
        "id": "playlist-sequenced",
        "external_urls": {"spotify": "https://open.spotify.com/playlist/sequenced"},
    }

    asyncio.run(
        create_spotify_playlist_for_run(
            db,
            run_id,
            "host-token",
            "host-id",
            "Sequenced",
            "PB-19",
        )
    )

    sent_uris = mock_add_items.await_args.kwargs["uris"]
    track_by_uri = {track.spotify_uri: track for track in tracks}
    sent_artists = [track_by_uri[uri].artist for uri in sent_uris]

    assert sent_uris[0] == "uri:00"
    assert all(a != b for a, b in zip(sent_artists, sent_artists[1:]))
    assert max(Counter(sent_artists).values()) == 2
    assert [track_by_uri[uri].selection_rank for uri in sent_uris] == list(
        range(1, len(sent_uris) + 1)
    )
    assert 7 <= sent_uris.index("uri:21") <= 15
