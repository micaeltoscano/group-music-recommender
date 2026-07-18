"""Controle e execução do pipeline de geração de playlist (PB-13/PB-15/PB-17)."""

import json
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from app.clients import llm_client, spotify_client
from app.db.models import MusicSession, MusicSessionMember, PlaylistRun, PlaylistRunTrack, User
from app.engine.candidates import CandidateTrack, generate_candidate_pool
from app.engine.context_scoring import (
    ContextCriteria,
    calculate_context_score,
    enrich_candidate_genres,
)
from app.engine.fairness import elevate_least_represented, evaluate_candidate_fairness
from app.engine.scoring import calculate_group_score
from app.engine.taste import UserTasteProfile
from app.engine.weights import CONSENSUS_MODES
from app.services.music_service import get_or_refresh_snapshot
from app.services.room_service import RoomHostRequiredError, RoomNotFoundError

MIN_PLAYLIST_TRACKS = 20
MAX_PLAYLIST_TRACKS = 30
MAX_TRACKS_PER_ARTIST = 2


class GenerationConflictError(Exception):
    """Lançada quando já há uma geração em andamento."""


class InsufficientTracksError(RuntimeError):
    """Indica que não há faixas válidas suficientes para criar a playlist."""


class PlaylistGenerationError(RuntimeError):
    """Falha controlada do pipeline, sem expor detalhes externos ou tokens."""

    def __init__(self, message: str, *, run_id: uuid.UUID, reason: str = "unavailable") -> None:
        self.run_id = run_id
        self.reason = reason
        super().__init__(message)


GenerationExecutor = Callable[[Session, uuid.UUID, int], Awaitable[PlaylistRun]]


def start_generation(db: Session, code: str, host_id: int) -> PlaylistRun:
    """
    Inicia uma nova geração. Faz o lock do banco para impedir concorrência.
    Retorna o PlaylistRun recém criado no estado running.
    """
    try:
        # Lock pessimista para a linha da sala.
        room = db.query(MusicSession).with_for_update().filter(MusicSession.code == code).one()
    except NoResultFound as exc:
        raise RoomNotFoundError(f"Sala '{code}' não encontrada.") from exc

    if room.host_user_id != host_id:
        raise RoomHostRequiredError("Apenas o host pode iniciar a geração.")

    if room.status == "generating":
        raise GenerationConflictError("Uma geração já está em andamento para esta sala.")

    # Altera estado da sala
    room.status = "generating"

    # Registra o histórico da execução
    run = PlaylistRun(
        session_id=room.id,
        status="running",
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    return run


def complete_generation(db: Session, run_id: uuid.UUID) -> None:
    """Marca a execução como completed, calcula as métricas do resultado e libera a sala."""
    from app.services.result_service import finalize_run_metrics

    run = db.query(PlaylistRun).with_for_update().filter(PlaylistRun.id == run_id).one()
    run.status = "completed"

    # Calcula compatibilidade/fairness/explicações a partir das faixas correspondidas
    # e persiste no próprio run, para o endpoint de resultado apenas ler (PB-16).
    finalize_run_metrics(db, run)

    room = db.query(MusicSession).with_for_update().filter(MusicSession.id == run.session_id).one()
    room.status = "open"

    db.commit()


def fail_generation(db: Session, run_id: uuid.UUID, error_message: str) -> None:
    """Marca a execução como failed e libera a sala para novas tentativas."""
    run = db.query(PlaylistRun).with_for_update().filter(PlaylistRun.id == run_id).one()
    run.status = "failed"
    run.error_message = error_message

    room = db.query(MusicSession).with_for_update().filter(MusicSession.id == run.session_id).one()
    room.status = "open"

    db.commit()


async def resolve_candidates(
    db: Session,
    run_id: uuid.UUID,
    candidates: list,
    host_token: str,
    market: str = "from_token",
) -> None:
    """
    Resolve as músicas candidatas no Spotify e salva na tabela playlist_run_tracks.
    `candidates` é uma lista de CandidateTrack (com ID original, raw_data e source_user_ids).
    """
    from app.clients.spotify_client import search_track
    from app.db.models import PlaylistRunTrack
    from app.engine.track_matcher import calculate_match_confidence
    import json

    tracks_to_insert = []

    for selection_rank, candidate in enumerate(candidates, start=1):
        original_name = candidate.raw_data.get("name", "")
        # O Spotify retorna 'artists' como uma lista de objetos
        original_artist = ""
        artists_data = candidate.raw_data.get("artists", [])
        if artists_data and isinstance(artists_data, list):
            original_artist = artists_data[0].get("name", "")
            
        if not original_name or not original_artist:
            # Descartado: sem nome/artista
            tracks_to_insert.append(PlaylistRunTrack(
                run_id=run_id,
                candidate_id=candidate.id,
                name=original_name or "Unknown",
                artist=original_artist or "Unknown",
                status="discarded",
                discard_reason="Missing name or artist",
                source=json.dumps(list(candidate.source_user_ids)),
                selection_rank=selection_rank,
            ))
            continue
            
        # Busca
        query = f"{original_name} {original_artist}"
        try:
            results = await search_track(host_token, query, market=market, limit=3)
        except Exception as exc:
            tracks_to_insert.append(PlaylistRunTrack(
                run_id=run_id,
                candidate_id=candidate.id,
                name=original_name,
                artist=original_artist,
                status="discarded",
                discard_reason=f"Spotify search error: {exc}",
                source=json.dumps(list(candidate.source_user_ids)),
                selection_rank=selection_rank,
            ))
            continue
            
        if not results:
            tracks_to_insert.append(PlaylistRunTrack(
                run_id=run_id,
                candidate_id=candidate.id,
                name=original_name,
                artist=original_artist,
                status="discarded",
                discard_reason="No results found",
                source=json.dumps(list(candidate.source_user_ids)),
                selection_rank=selection_rank,
            ))
            continue
            
        # Avalia a confiança
        best_match = None
        best_confidence = -1.0
        
        for item in results:
            res_name = item.get("name", "")
            res_artists = item.get("artists", [])
            res_artist = res_artists[0].get("name", "") if res_artists else ""
            
            # Pula indisponíveis no mercado
            if not item.get("is_playable", True):
                continue
                
            conf = calculate_match_confidence(original_name, original_artist, res_name, res_artist)
            if conf > best_confidence:
                best_confidence = conf
                best_match = item
                
        if best_match and best_confidence >= 0.8 and best_match.get("uri"):
            tracks_to_insert.append(PlaylistRunTrack(
                run_id=run_id,
                candidate_id=candidate.id,
                spotify_id=best_match.get("id"),
                spotify_uri=best_match.get("uri"),
                name=best_match.get("name"),
                artist=best_match.get("artists")[0].get("name") if best_match.get("artists") else original_artist,
                match_confidence=best_confidence,
                status="matched",
                source=json.dumps(list(candidate.source_user_ids)),
                selection_rank=selection_rank,
            ))
        else:
            if best_match and best_confidence >= 0.8:
                reason = "no_uri"
            elif best_match:
                reason = "Confidence below threshold (0.8)"
            else:
                reason = "All results unplayable"
            tracks_to_insert.append(PlaylistRunTrack(
                run_id=run_id,
                candidate_id=candidate.id,
                name=original_name,
                artist=original_artist,
                match_confidence=best_confidence if best_match else None,
                status="discarded",
                discard_reason=reason,
                source=json.dumps(list(candidate.source_user_ids)),
                selection_rank=selection_rank,
            ))
            
    if tracks_to_insert:
        db.add_all(tracks_to_insert)
        db.commit()


async def create_spotify_playlist_for_run(
    db: Session,
    run_id: uuid.UUID,
    host_token: str,
    host_spotify_id: str,
    name: str,
    description: str,
) -> PlaylistRun:
    """
    Cria a playlist no Spotify para a execução informada, aplicando as regras:
    - Máx. 2 músicas por artista.
    - Tamanho entre 20 e 30 faixas.
    - Grava o spotify_playlist_id e url no PlaylistRun.
    """
    run = db.query(PlaylistRun).with_for_update().filter(PlaylistRun.id == run_id).one()
    
    # Busca as faixas correspondidas (matched)
    tracks = (
        db.query(PlaylistRunTrack)
        .filter(PlaylistRunTrack.run_id == run_id, PlaylistRunTrack.status == "matched")
        .order_by(
            PlaylistRunTrack.selection_rank.is_(None),
            PlaylistRunTrack.selection_rank,
            PlaylistRunTrack.created_at,
        )
        .all()
    )
    
    # Aplica o capping por artista
    artist_counts: dict[str, int] = {}
    selected_uris: list[str] = []
    
    for track in tracks:
        if len(selected_uris) >= MAX_PLAYLIST_TRACKS:
            track.status = "discarded"
            track.discard_reason = "playlist_limit"
            continue

        artist_name = track.artist.strip().lower() if track.artist else ""
        if not track.spotify_uri:
            track.status = "discarded"
            track.discard_reason = "no_uri"
            continue
        if artist_counts.get(artist_name, 0) < MAX_TRACKS_PER_ARTIST:
            artist_counts[artist_name] = artist_counts.get(artist_name, 0) + 1
            selected_uris.append(track.spotify_uri)
        else:
            track.status = "discarded"
            track.discard_reason = "artist_cap"

    if len(selected_uris) < MIN_PLAYLIST_TRACKS:
        raise InsufficientTracksError(
            f"São necessárias ao menos {MIN_PLAYLIST_TRACKS} faixas válidas; "
            f"foram encontradas {len(selected_uris)}."
        )
            
    # Cria a playlist
    playlist_data = await spotify_client.create_playlist(
        access_token=host_token,
        user_spotify_id=host_spotify_id,
        name=name,
        description=description,
        public=False,
    )
    
    playlist_id = playlist_data.get("id")
    external_urls = playlist_data.get("external_urls", {})
    playlist_url = external_urls.get("spotify")

    if not playlist_id or not playlist_url:
        raise spotify_client.SpotifyInvalidResponse(
            "Spotify não retornou o identificador e o link da playlist."
        )
    
    # Salva no banco (mesmo que dê falha na inserção, ID já fica salvo - CT-PB15-04)
    run.spotify_playlist_id = playlist_id
    run.spotify_playlist_url = playlist_url
    db.commit()
    
    # Adiciona os itens em lotes (embora aqui sejam no máximo 30, o endpoint suporta 100)
    if selected_uris:
        await spotify_client.add_items_to_playlist(
            access_token=host_token,
            playlist_id=playlist_id,
            uris=selected_uris,
        )

    return run


def _rank_candidates(
    candidates: list[CandidateTrack],
    profiles: list[UserTasteProfile],
    room_mode: str | None,
    context: ContextCriteria,
) -> list[CandidateTrack]:
    """Ordena candidatas pelo consenso do grupo e pela adequação contextual."""
    mode_key = "safe_party" if room_mode == "Festa Segura" else "democratic"
    mode_config = CONSENSUS_MODES[mode_key]
    scored: list[dict[str, Any]] = []

    for candidate in candidates:
        context_score = calculate_context_score(candidate, context)
        group_data = calculate_group_score(
            candidate,
            profiles,
            mode_config["individual"],
            mode_config["group"],
            context_score=context_score,
        )
        evaluation = evaluate_candidate_fairness(group_data, mode_config)
        evaluation["candidate"] = candidate
        scored.append(evaluation)

    scored.sort(key=lambda item: item["penalized_score"], reverse=True)
    target_size = min(50, len(scored))
    selected = elevate_least_represented(scored, target_size, len(profiles))
    return [item["candidate"] for item in selected]


async def execute_generation(
    db: Session,
    run_id: uuid.UUID,
    host_id: int,
) -> PlaylistRun:
    """Executa snapshots → motor → matching → playlist e fecha a execução."""
    try:
        run = db.query(PlaylistRun).filter(PlaylistRun.id == run_id).one()
        room = db.query(MusicSession).filter(MusicSession.id == run.session_id).one()
        member_ids = [
            row.user_id
            for row in (
                db.query(MusicSessionMember)
                .filter(MusicSessionMember.session_id == room.id)
                .order_by(MusicSessionMember.joined_at, MusicSessionMember.user_id)
                .all()
            )
        ]
        if not member_ids:
            raise RuntimeError("A sala não possui integrantes.")

        # PB-17: interpreta só o contexto do host (nunca dados de tops/artists
        # dos membros) e persiste no run. Cai em fallback determinístico se o
        # LLM estiver indisponível ou responder fora do schema; nunca interrompe
        # a geração (critérios 2 e 3 do PB-17).
        llm_context = await llm_client.interpret_context(room.occasion, room.description)
        run.llm_context_json = json.dumps(llm_context.model_dump())
        db.commit()

        profiles: list[UserTasteProfile] = []
        track_snapshots: list[tuple[int, dict[str, Any]]] = []
        artist_genres: dict[str, set[str]] = {}
        for member_id in member_ids:
            snapshot_result = await get_or_refresh_snapshot(
                db,
                member_id,
                time_range="medium_term",
            )
            snapshot = snapshot_result.snapshot
            tracks_payload = {"items": snapshot.top_tracks_json}
            artists_payload = {"items": snapshot.top_artists_json}
            profiles.append(UserTasteProfile(member_id, tracks_payload, artists_payload))
            track_snapshots.append((member_id, tracks_payload))
            for artist in snapshot.top_artists_json:
                if not isinstance(artist, dict) or not artist.get("id"):
                    continue
                artist_genres.setdefault(str(artist["id"]), set()).update(
                    genre.strip().lower()
                    for genre in artist.get("genres", [])
                    if isinstance(genre, str) and genre.strip()
                )

        candidates, _ = generate_candidate_pool(track_snapshots)
        if not candidates:
            raise InsufficientTracksError("Nenhuma faixa candidata foi encontrada nos snapshots.")
        candidates = enrich_candidate_genres(candidates, artist_genres)
        context_criteria = ContextCriteria(
            occasion=llm_context.occasion,
            mood=llm_context.mood,
            energy=llm_context.energy,
            tags_positive=tuple(llm_context.tags_positive),
            tags_negative=tuple(llm_context.tags_negative),
            avoid=tuple(llm_context.avoid),
        )
        ranked_candidates = _rank_candidates(
            candidates,
            profiles,
            room.mode,
            context_criteria,
        )

        host = db.get(User, host_id)
        if host is None:
            raise RuntimeError("Host da sala não encontrado.")
        host_token = await spotify_client.get_valid_access_token(db, host_id)
        await resolve_candidates(db, run_id, ranked_candidates, host_token)

        playlist_name = f"Vibe Check — {room.occasion or room.code}"[:100]
        member_label = "1 integrante" if len(member_ids) == 1 else f"{len(member_ids)} integrantes"
        await create_spotify_playlist_for_run(
            db,
            run_id,
            host_token,
            host.spotify_id,
            playlist_name,
            f"Playlist privada criada pelo Vibe Check para {member_label}.",
        )
        complete_generation(db, run_id)
        db.refresh(run)
        return run
    except Exception as exc:
        db.rollback()
        if isinstance(exc, spotify_client.ReauthenticationRequired):
            reason = "reauth_required"
            message = "Autorize novamente sua conta Spotify antes de gerar a playlist."
        elif isinstance(exc, InsufficientTracksError):
            reason = "insufficient_tracks"
            message = str(exc)
        else:
            reason = "unavailable"
            message = "Não foi possível gerar a playlist agora. Tente novamente."

        fail_generation(db, run_id, message)
        raise PlaylistGenerationError(message, run_id=run_id, reason=reason) from exc


def get_generation_executor() -> GenerationExecutor:
    """Dependência substituível para isolar os testes históricos do lock do PB-13."""
    return execute_generation
