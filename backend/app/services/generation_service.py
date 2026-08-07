"""Controle e execução do pipeline de geração de playlist (PB-13/PB-15/PB-17)."""

import json
import uuid
from collections import Counter
from collections.abc import Awaitable, Callable
from typing import Any

from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from app.clients import llm_client, spotify_client
from app.config import settings
from app.db.models import (
    MusicSession,
    MusicSessionMember,
    PlaylistRun,
    PlaylistRunTrack,
    User,
    VibeCheckAnswer,
)
from app.engine.bridge import evaluate_bridge_candidate
from app.engine.candidates import CandidateTrack, generate_candidate_pool
from app.engine.clustering import TasteClusteringResult, cluster_taste_profiles
from app.engine.context_scoring import (
    ContextCriteria,
    calculate_context_score,
    enrich_candidate_genres,
)
from app.engine.contextual_pool import blend_contextual_candidates
from app.engine.fairness import elevate_least_represented, evaluate_candidate_fairness
from app.engine.scoring import calculate_candidate_diversity_score, calculate_group_score
from app.engine.sequencer import SequencerTrack, sequence_tracks
from app.engine.subgroup_balance import balance_subgroup_candidates
from app.engine.taste import UserTasteProfile
from app.engine.vibe_scoring import (
    VibePreferences,
    aggregate_vibe_preferences,
    calculate_vibe_score,
)
from app.engine.weights import CONSENSUS_MODES, VIBE_CHECK_INFLUENCE
from app.services.context_enrichment_service import enrich_candidates_context
from app.services.contextual_pool_service import discover_context_candidates
from app.services.library_application_service import load_library_generation_data
from app.services.music_service import get_or_refresh_snapshot
from app.services.room_service import RoomHostRequiredError, RoomNotFoundError

MIN_PLAYLIST_TRACKS = 20
MAX_PLAYLIST_TRACKS = 30
MAX_TRACKS_PER_ARTIST = 2
ROOM_MODE_KEYS = {
    "Democrático": "democratic",
    "Festa Segura": "safe_party",
    "Descoberta": "discovery",
}
GENERATION_STAGES = {
    "starting": 0,
    "interpreting_context": 8,
    "collecting_tastes": 20,
    "discovering_context": 40,
    "ranking": 55,
    "matching_spotify": 70,
    "creating_playlist": 90,
    "finalizing": 97,
    "completed": 100,
}


class GenerationConflictError(Exception):
    """Lançada quando já há uma geração em andamento."""


class InsufficientTracksError(RuntimeError):
    """Indica que não há faixas válidas suficientes para criar a playlist."""


class PlaylistGenerationError(RuntimeError):
    """Falha controlada do pipeline, sem expor detalhes externos ou tokens."""

    def __init__(
        self,
        message: str,
        *,
        run_id: uuid.UUID,
        reason: str = "unavailable",
        retry_after: int | None = None,
    ) -> None:
        self.run_id = run_id
        self.reason = reason
        self.retry_after = retry_after
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


def update_generation_progress(
    db: Session,
    run_id: uuid.UUID,
    stage: str,
) -> PlaylistRun:
    """Persiste um estágio público real sem permitir regressão percentual."""

    if stage not in GENERATION_STAGES:
        raise ValueError(f"Estágio de geração desconhecido: {stage}")
    run = db.query(PlaylistRun).filter(PlaylistRun.id == run_id).one()
    next_percent = GENERATION_STAGES[stage]
    if next_percent < run.progress_percent:
        return run
    run.progress_stage = stage
    run.progress_percent = next_percent
    db.commit()
    return run


def complete_generation(db: Session, run_id: uuid.UUID) -> None:
    """Marca a execução como completed, calcula as métricas do resultado e libera a sala."""
    from app.services.result_service import finalize_run_metrics

    run = db.query(PlaylistRun).with_for_update().filter(PlaylistRun.id == run_id).one()
    run.status = "completed"
    run.progress_stage = "completed"
    run.progress_percent = 100

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
    run.progress_stage = "failed"

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
    from app.clients.spotify_client import SpotifyRateLimited, search_track
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
                is_bridge=candidate.is_bridge,
                selection_rank=selection_rank,
            ))
            continue

        # Candidatas originadas nos snapshots já são objetos Spotify completos.
        # Reutilizar o ID/URI evita uma busca redundante por faixa e reduz
        # drasticamente a chance de rate limit. Itens externos/incompletos
        # continuam pelo matching textual logo abaixo.
        raw_spotify_id = str(candidate.raw_data.get("id") or "")
        raw_spotify_uri = candidate.raw_data.get("uri")
        expected_spotify_uri = f"spotify:track:{raw_spotify_id}"
        has_consistent_native_identity = (
            bool(raw_spotify_id)
            and raw_spotify_id == str(candidate.id)
            and raw_spotify_uri == expected_spotify_uri
        )
        if has_consistent_native_identity:
            if candidate.raw_data.get("is_playable") is False:
                tracks_to_insert.append(PlaylistRunTrack(
                    run_id=run_id,
                    candidate_id=candidate.id,
                    name=original_name,
                    artist=original_artist,
                    status="discarded",
                    discard_reason="unavailable_in_market",
                    source=json.dumps(sorted(candidate.source_user_ids)),
                    is_bridge=candidate.is_bridge,
                    selection_rank=selection_rank,
                ))
                continue
            tracks_to_insert.append(PlaylistRunTrack(
                run_id=run_id,
                candidate_id=candidate.id,
                spotify_id=raw_spotify_id,
                spotify_uri=expected_spotify_uri,
                name=original_name,
                artist=original_artist,
                match_confidence=1.0,
                status="matched",
                source=json.dumps(sorted(candidate.source_user_ids)),
                is_bridge=candidate.is_bridge,
                selection_rank=selection_rank,
            ))
            continue

        # Busca
        query = f"{original_name} {original_artist}"
        try:
            results = await search_track(host_token, query, market=market, limit=3)
        except SpotifyRateLimited:
            # Rate limit é do lote, não da faixa. Continuar criaria dezenas de
            # descartes falsos e prolongaria a janela de bloqueio.
            raise
        except Exception as exc:
            tracks_to_insert.append(PlaylistRunTrack(
                run_id=run_id,
                candidate_id=candidate.id,
                name=original_name,
                artist=original_artist,
                status="discarded",
                discard_reason=f"Spotify search error: {exc}",
                source=json.dumps(list(candidate.source_user_ids)),
                is_bridge=candidate.is_bridge,
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
                is_bridge=candidate.is_bridge,
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
                is_bridge=candidate.is_bridge,
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
                is_bridge=candidate.is_bridge,
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

    # PB-19: a posição do ranking representa aceitação; seu inverso representa
    # risco. O motor puro aplica cap/limite e produz a ordem final enviada ao
    # Spotify, evitando artistas adjacentes quando a seleção permite.
    rank_by_track_id: dict[str, int] = {}
    track_by_id: dict[str, PlaylistRunTrack] = {}
    for fallback_rank, track in enumerate(tracks, start=1):
        if not track.spotify_uri:
            track.status = "discarded"
            track.discard_reason = "no_uri"
            continue
        track_key = str(track.id or f"track-{fallback_rank}")
        rank = (
            track.selection_rank
            if track.selection_rank and track.selection_rank > 0
            else fallback_rank
        )
        rank_by_track_id[track_key] = rank
        track_by_id[track_key] = track

    max_rank = max(rank_by_track_id.values(), default=1)
    min_rank = min(rank_by_track_id.values(), default=1)
    rank_span = max(1, max_rank - min_rank)
    sequence_input = []
    for track_key, track in track_by_id.items():
        acceptance = 1.0 - ((rank_by_track_id[track_key] - min_rank) / rank_span)
        sequence_input.append(
            SequencerTrack(
                track_id=track_key,
                artist=track.artist or "",
                acceptance=acceptance,
                risk=1.0 - acceptance,
                original_position=rank_by_track_id[track_key],
            )
        )

    sequenced = sequence_tracks(
        sequence_input,
        max_per_artist=MAX_TRACKS_PER_ARTIST,
        limit=MAX_PLAYLIST_TRACKS,
    )
    selected_ids = {track.track_id for track in sequenced}
    selected_artist_counts = Counter(track.artist.strip().casefold() for track in sequenced)

    for track_key, track in track_by_id.items():
        if track_key in selected_ids:
            continue
        artist_name = (track.artist or "").strip().casefold()
        track.status = "discarded"
        track.discard_reason = (
            "artist_cap"
            if selected_artist_counts[artist_name] >= MAX_TRACKS_PER_ARTIST
            else "playlist_limit"
        )

    selected_uris: list[str] = []
    for final_position, sequence_track in enumerate(sequenced, start=1):
        track = track_by_id[sequence_track.track_id]
        track.selection_rank = final_position
        selected_uris.append(track.spotify_uri)

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
    vibe_preferences: VibePreferences | None = None,
    taste_clusters: TasteClusteringResult | None = None,
    bridge_tracks_enabled: bool = False,
    subgroup_balancing_enabled: bool = False,
    subgroup_max_share: float = 0.60,
    contextual_pool_enabled: bool = False,
    contextual_pool_share: float = 0.50,
) -> list[CandidateTrack]:
    """Ordena candidatas por consenso, contexto e Vibe Check opcional."""
    mode_key = ROOM_MODE_KEYS.get(room_mode or "Democrático", "democratic")
    mode_config = CONSENSUS_MODES[mode_key]
    scored: list[dict[str, Any]] = []

    for candidate in candidates:
        candidate.source_cluster_ids = (
            taste_clusters.cluster_ids_for_members(candidate.source_user_ids)
            if taste_clusters is not None
            else ()
        )
        if bridge_tracks_enabled:
            bridge = evaluate_bridge_candidate(
                candidate,
                profiles,
                taste_clusters,
                mode_config["individual"],
            )
            candidate.is_bridge = bridge.is_bridge
            candidate.bridge_score = bridge.bridge_score
            candidate.bridge_cluster_ids = bridge.accepted_cluster_ids
        else:
            candidate.is_bridge = False
            candidate.bridge_score = 0.0
            candidate.bridge_cluster_ids = ()
        context_score = calculate_context_score(candidate, context)
        diversity_score = calculate_candidate_diversity_score(candidate, profiles)
        group_data = calculate_group_score(
            candidate,
            profiles,
            mode_config["individual"],
            mode_config["group"],
            context_score=context_score,
            diversity_score=diversity_score,
        )
        if vibe_preferences is not None:
            vibe_score = calculate_vibe_score(candidate, vibe_preferences)
            group_data["group_score"] = round(
                (group_data["group_score"] * (1.0 - VIBE_CHECK_INFLUENCE))
                + (vibe_score * VIBE_CHECK_INFLUENCE),
                4,
            )
            group_data["vibe_score"] = vibe_score
        evaluation = evaluate_candidate_fairness(group_data, mode_config)
        evaluation["context_score"] = context_score
        evaluation["candidate"] = candidate
        scored.append(evaluation)

    scored.sort(key=lambda item: item["penalized_score"], reverse=True)
    target_size = min(50, len(scored))
    selected = elevate_least_represented(scored, target_size, len(profiles))
    if contextual_pool_enabled:
        selected_candidate_ids = {
            id(item["candidate"])
            for item in selected
        }
        prioritised = selected + [
            item
            for item in scored
            if id(item["candidate"]) not in selected_candidate_ids
        ]
        selected = blend_contextual_candidates(
            prioritised,
            target_size=target_size,
            contextual_share=contextual_pool_share,
        )
    if subgroup_balancing_enabled:
        balance = balance_subgroup_candidates(
            selected,
            taste_clusters,
            target_size=min(MAX_PLAYLIST_TRACKS, len(selected)),
            max_cluster_share=subgroup_max_share,
        )
        selected = list(balance.ranked_candidates)
        allocation_by_candidate = {
            allocation.candidate_id: allocation.cluster_id
            for allocation in balance.allocations
        }
        for item in selected:
            candidate = item["candidate"]
            candidate.subgroup_balancing_applied = balance.applied
            candidate.balanced_cluster_id = allocation_by_candidate.get(candidate.id)
    else:
        for item in selected:
            candidate = item["candidate"]
            candidate.subgroup_balancing_applied = False
            candidate.balanced_cluster_id = None
    return [item["candidate"] for item in selected]


def load_vibe_preferences(
    db: Session,
    session_id: uuid.UUID,
    member_ids: list[int],
) -> VibePreferences | None:
    """Agrega somente respostas reais; pendente/pulado permanecem neutros."""

    vibe_answers = (
        db.query(VibeCheckAnswer)
        .filter(
            VibeCheckAnswer.session_id == session_id,
            VibeCheckAnswer.user_id.in_(member_ids),
            VibeCheckAnswer.status == "answered",
        )
        .all()
    )
    return aggregate_vibe_preferences(
        (
            (answer.energy, answer.valence, answer.popularity)
            for answer in vibe_answers
        ),
        total_members=len(member_ids),
    )


async def execute_generation(
    db: Session,
    run_id: uuid.UUID,
    host_id: int,
) -> PlaylistRun:
    """Executa snapshots → motor → matching → playlist e fecha a execução."""
    try:
        run = db.query(PlaylistRun).filter(PlaylistRun.id == run_id).one()
        room = db.query(MusicSession).filter(MusicSession.id == run.session_id).one()
        update_generation_progress(db, run_id, "interpreting_context")
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
        update_generation_progress(db, run_id, "collecting_tastes")

        profiles: list[UserTasteProfile] = []
        track_snapshots: list[tuple[int, dict[str, Any]]] = []
        artist_genres: dict[str, set[str]] = {}
        library_data = load_library_generation_data(db, member_ids)
        if library_data is not None:
            for weighted_profile in library_data.profiles:
                items = [
                    {
                        "id": track.spotify_track_id,
                        "uri": track.spotify_uri,
                        "name": track.track_name,
                        "artists": [
                            {"id": track.artist_id, "name": track.artist_name}
                        ] if track.artist_id or track.artist_name else [],
                    }
                    for track in weighted_profile.tracks
                ]
                payload = {"items": items}
                profiles.append(UserTasteProfile(weighted_profile.user_id, payload, {"items": []}))
                track_snapshots.append((weighted_profile.user_id, payload))
            candidates = list(library_data.candidates)
        else:
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

        taste_clusters = cluster_taste_profiles(profiles)
        if not candidates:
            raise InsufficientTracksError("Nenhuma faixa candidata foi encontrada nos snapshots.")
        candidates = enrich_candidate_genres(candidates, artist_genres)
        # PB-18: Last.fm é apenas uma fonte auxiliar. O serviço consulta tags
        # da faixa → artista e cai para os gêneros já anexados acima (ou
        # consenso), persistindo fonte/confiança e reutilizando cache válido.
        candidates = await enrich_candidates_context(db, candidates)
        update_generation_progress(db, run_id, "discovering_context")
        context_criteria = ContextCriteria(
            occasion=llm_context.occasion,
            mood=llm_context.mood,
            energy=llm_context.energy,
            tags_positive=tuple(llm_context.tags_positive),
            tags_negative=tuple(llm_context.tags_negative),
            avoid=tuple(llm_context.avoid),
        )
        contextual_candidates = await discover_context_candidates(
            candidates,
            context_criteria,
        )
        if contextual_candidates:
            # Descobertas por similaridade não herdam tags da semente. Cada
            # faixa externa recebe seus próprios metadados antes de pontuar;
            # falhas continuam caindo na cascata do PB-18.
            contextual_candidates = await enrich_candidates_context(
                db,
                contextual_candidates,
            )
        candidates.extend(contextual_candidates)
        update_generation_progress(db, run_id, "ranking")
        vibe_preferences = load_vibe_preferences(
            db,
            room.id,
            member_ids,
        )
        ranked_candidates = _rank_candidates(
            candidates,
            profiles,
            room.mode,
            context_criteria,
            vibe_preferences,
            taste_clusters=taste_clusters,
            bridge_tracks_enabled=settings.bridge_tracks_enabled,
            subgroup_balancing_enabled=settings.subgroup_balancing_enabled,
            subgroup_max_share=settings.subgroup_max_share,
            contextual_pool_enabled=bool(contextual_candidates),
            contextual_pool_share=settings.contextual_pool_share,
        )
        explanation_sample = ranked_candidates[:MAX_PLAYLIST_TRACKS]
        origin_counts = {"top": 0, "playlist": 0, "context": 0}
        for candidate in explanation_sample:
            if str(candidate.origin).startswith("lastfm_"):
                origin_counts["context"] += 1
                continue
            library_counts = candidate.raw_data.get("library_origin_counts", {})
            if library_counts.get("top", 0):
                origin_counts["top"] += 1
            elif library_counts.get("playlist", 0):
                origin_counts["playlist"] += 1
            else:
                origin_counts["top"] += 1
        total_explained = sum(origin_counts.values())
        run.explanation_json = json.dumps(
            {
                "library_mix": {
                    key: round(100 * value / total_explained) if total_explained else 0
                    for key, value in origin_counts.items()
                }
            }
        )
        run.subgroup_balancing_applied = any(
            candidate.subgroup_balancing_applied for candidate in ranked_candidates
        )
        db.commit()

        host = db.get(User, host_id)
        if host is None:
            raise RuntimeError("Host da sala não encontrado.")
        host_token = await spotify_client.get_valid_access_token(db, host_id)
        update_generation_progress(db, run_id, "matching_spotify")
        await resolve_candidates(db, run_id, ranked_candidates, host_token)

        update_generation_progress(db, run_id, "creating_playlist")
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
        update_generation_progress(db, run_id, "finalizing")
        complete_generation(db, run_id)
        db.refresh(run)
        return run
    except Exception as exc:
        db.rollback()
        if isinstance(exc, spotify_client.ReauthenticationRequired):
            reason = "reauth_required"
            message = "Autorize novamente sua conta Spotify antes de gerar a playlist."
        elif isinstance(exc, spotify_client.SpotifyRateLimited):
            reason = "rate_limited"
            message = (
                "Spotify temporariamente limitado; "
                f"tente novamente em {exc.retry_after} segundos."
            )
        elif isinstance(exc, InsufficientTracksError):
            reason = "insufficient_tracks"
            message = str(exc)
        else:
            reason = "unavailable"
            message = "Não foi possível gerar a playlist agora. Tente novamente."

        fail_generation(db, run_id, message)
        raise PlaylistGenerationError(
            message,
            run_id=run_id,
            reason=reason,
            retry_after=(
                exc.retry_after
                if isinstance(exc, spotify_client.SpotifyRateLimited)
                else None
            ),
        ) from exc


def get_generation_executor() -> GenerationExecutor:
    """Dependência substituível para isolar os testes históricos do lock do PB-13."""
    return execute_generation
