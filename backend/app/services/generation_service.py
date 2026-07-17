"""Serviço para controle da execução de geração de playlist (PB-13)."""

import uuid

from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from app.db.models import MusicSession, PlaylistRun
from app.services.room_service import RoomHostRequiredError, RoomNotFoundError


class GenerationConflictError(Exception):
    """Lançada quando já há uma geração em andamento."""


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
    """Marca a execução como completed e libera a sala."""
    run = db.query(PlaylistRun).with_for_update().filter(PlaylistRun.id == run_id).one()
    run.status = "completed"

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

    for candidate in candidates:
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
            ))
            continue
            
        # Busca
        query = f"{original_name} {original_artist}"
        try:
            results = await search_track(host_token, query, market=market, limit=3)
        except Exception as exc:
            # Ignora falha de rede temporária ou rate limit e marca como descartada?
            # Por segurança, vamos marcar como indisponível/erro
            tracks_to_insert.append(PlaylistRunTrack(
                run_id=run_id,
                candidate_id=candidate.id,
                name=original_name,
                artist=original_artist,
                status="discarded",
                discard_reason=f"Spotify search error: {exc}",
                source=json.dumps(list(candidate.source_user_ids)),
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
                
        if best_match and best_confidence >= 0.8:
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
            ))
        else:
            reason = "Confidence below threshold (0.8)" if best_match else "All results unplayable"
            tracks_to_insert.append(PlaylistRunTrack(
                run_id=run_id,
                candidate_id=candidate.id,
                name=original_name,
                artist=original_artist,
                match_confidence=best_confidence if best_match else None,
                status="discarded",
                discard_reason=reason,
                source=json.dumps(list(candidate.source_user_ids)),
            ))
            
    if tracks_to_insert:
        db.add_all(tracks_to_insert)
        db.commit()
