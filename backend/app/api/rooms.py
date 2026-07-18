"""Rotas de salas efêmeras."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.models import MusicSession, PlaylistRun, VibeCheckAnswer
from app.db.session import get_db
from app.schemas.rooms import (
    ConsensusModesResponse,
    PlaylistRunResponse,
    RoomGenerationResponse,
    RoomContextUpdate,
    RoomMemberResponse,
    RoomModeUpdate,
    RoomResponse,
    RoomResultResponse,
    VibeSummaryResponse,
)
from app.services.room_service import (
    RoomAccessDeniedError,
    RoomCodeGenerationError,
    RoomExpiredError,
    RoomFullError,
    RoomHostRequiredError,
    RoomNotFoundError,
    RoomModeUnavailableError,
    available_consensus_modes,
    create_room,
    get_room_for_member,
    join_room,
    list_room_members,
    update_room_context,
    update_room_mode,
)

router = APIRouter()

LEGACY_ROOM_RESPONSE_EXCLUDE = {
    "generation": True,
    "vibe_summary": True,
    "members": {"__all__": {"vibe_status": True}},
}


def _room_response(db: Session, room: MusicSession) -> RoomResponse:
    member_rows = list_room_members(db, room.id)
    member_ids = [user.id for _, user in member_rows]
    vibe_status_by_user = {
        answer.user_id: answer.status
        for answer in (
            db.query(VibeCheckAnswer)
            .filter(
                VibeCheckAnswer.session_id == room.id,
                VibeCheckAnswer.user_id.in_(member_ids),
            )
            .all()
        )
    }
    members = [
        RoomMemberResponse(
            user_id=user.id,
            display_name=user.display_name,
            image_url=user.image_url,
            role=membership.role,
            vibe_status=vibe_status_by_user.get(user.id, "pending"),
            joined_at=membership.joined_at,
        )
        for membership, user in member_rows
    ]
    answered = sum(member.vibe_status == "answered" for member in members)
    skipped = sum(member.vibe_status == "skipped" for member in members)
    vibe_summary = VibeSummaryResponse(
        total=len(members),
        pending=len(members) - answered - skipped,
        answered=answered,
        skipped=skipped,
    )
    latest_run = (
        db.query(PlaylistRun)
        .filter(PlaylistRun.session_id == room.id)
        .order_by(PlaylistRun.created_at.desc(), PlaylistRun.id.desc())
        .first()
    )
    generation = (
        RoomGenerationResponse(
            run_id=latest_run.id,
            status=latest_run.status,
            stage=latest_run.progress_stage,
            progress_percent=latest_run.progress_percent,
            error_message=latest_run.error_message,
            playlist_url=latest_run.spotify_playlist_url,
            updated_at=latest_run.updated_at,
        )
        if latest_run is not None
        else None
    )
    return RoomResponse(
        id=room.id,
        code=room.code,
        status=room.status,
        occasion=room.occasion,
        description=room.description,
        mode=room.mode,
        created_at=room.created_at,
        expires_at=room.expires_at,
        members=members,
        generation=generation,
        vibe_summary=vibe_summary,
    )


@router.post(
    "",
    response_model=RoomResponse,
    response_model_exclude=LEGACY_ROOM_RESPONSE_EXCLUDE,
    status_code=status.HTTP_201_CREATED,
)
def create_music_room(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoomResponse:
    """Cria uma sala e registra o usuário autenticado como host."""
    try:
        room, _ = create_room(db, current_user["id"])
    except RoomCodeGenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível criar a sala agora. Tente novamente.",
        ) from exc

    return _room_response(db, room)


@router.post(
    "/{code}/join",
    response_model=RoomResponse,
)
def join_music_room(
    code: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoomResponse:
    """Entra em uma sala existente ou devolve o estado atual se já for membro."""
    try:
        room, _ = join_room(db, code, current_user["id"])
    except RoomNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RoomExpiredError as exc:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(exc)) from exc
    except RoomFullError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _room_response(db, room)


@router.get("/consensus-modes", response_model=ConsensusModesResponse)
def read_consensus_modes(
    _current_user: dict = Depends(get_current_user),
) -> ConsensusModesResponse:
    """Lista somente os modos habilitados pela configuração do servidor."""

    return ConsensusModesResponse(modes=available_consensus_modes())


@router.get("/{code}", response_model=RoomResponse)
def read_music_room(
    code: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoomResponse:
    """Retorna o estado público da sala somente para integrantes."""
    try:
        room = get_room_for_member(db, code, current_user["id"])
    except RoomNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RoomAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return _room_response(db, room)


def _raise_room_update_error(exc: Exception) -> None:
    if isinstance(exc, RoomNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if isinstance(exc, (RoomAccessDeniedError, RoomHostRequiredError)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    if isinstance(exc, RoomModeUnavailableError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    raise exc


@router.put(
    "/{code}/context",
    response_model=RoomResponse,
    response_model_exclude=LEGACY_ROOM_RESPONSE_EXCLUDE,
)
def set_music_room_context(
    code: str,
    payload: RoomContextUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoomResponse:
    """Substitui ocasião/descrição da sala quando solicitado pelo host."""
    try:
        room = update_room_context(
            db,
            code,
            current_user["id"],
            occasion=payload.occasion,
            description=payload.description,
        )
    except (RoomNotFoundError, RoomAccessDeniedError, RoomHostRequiredError) as exc:
        _raise_room_update_error(exc)
    return _room_response(db, room)


@router.put(
    "/{code}/mode",
    response_model=RoomResponse,
    response_model_exclude=LEGACY_ROOM_RESPONSE_EXCLUDE,
)
def set_music_room_mode(
    code: str,
    payload: RoomModeUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoomResponse:
    """Seleciona um modo de consenso habilitado na configuração do produto."""
    try:
        room = update_room_mode(
            db,
            code,
            current_user["id"],
            mode=payload.mode,
        )
    except (
        RoomNotFoundError,
        RoomAccessDeniedError,
        RoomHostRequiredError,
        RoomModeUnavailableError,
    ) as exc:
        _raise_room_update_error(exc)
    return _room_response(db, room)


from app.services.generation_service import (
    GenerationConflictError,
    GenerationExecutor,
    PlaylistGenerationError,
    get_generation_executor,
    start_generation,
)

@router.post("/{code}/generate", response_model=PlaylistRunResponse, status_code=status.HTTP_202_ACCEPTED)
async def request_playlist_generation(
    code: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    executor: GenerationExecutor = Depends(get_generation_executor),
) -> PlaylistRunResponse:
    """Inicia e executa o pipeline básico até criar a playlist privada no Spotify."""
    try:
        run = start_generation(db, code, current_user["id"])
    except RoomNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RoomHostRequiredError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except GenerationConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    try:
        return await executor(db, run.id, current_user["id"])
    except PlaylistGenerationError as exc:
        if exc.reason == "reauth_required":
            response_status = status.HTTP_401_UNAUTHORIZED
        elif exc.reason == "rate_limited":
            response_status = status.HTTP_429_TOO_MANY_REQUESTS
        elif exc.reason == "insufficient_tracks":
            response_status = status.HTTP_422_UNPROCESSABLE_ENTITY
        else:
            response_status = status.HTTP_502_BAD_GATEWAY
        detail = {"message": str(exc), "run_id": str(exc.run_id)}
        if exc.retry_after is not None:
            detail["retry_after"] = exc.retry_after
        raise HTTPException(
            status_code=response_status,
            detail=detail,
        ) from exc


@router.get("/{code}/result", response_model=RoomResultResponse)
def get_room_result(
    code: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoomResultResponse:
    """Retorna o resultado explicável da última execução concluída da sala.

    As métricas (compatibilidade/fairness) e explicações são as calculadas pela
    própria execução e persistidas no run (ver `result_service`); aqui apenas lê.
    """
    from app.db.models import PlaylistRun
    from app.services.result_service import build_room_result

    try:
        room = get_room_for_member(db, code, current_user["id"])
    except RoomNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RoomAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    run = (
        db.query(PlaylistRun)
        .filter(PlaylistRun.session_id == room.id)
        .order_by(PlaylistRun.created_at.desc())
        .first()
    )

    if not run or run.status != "completed":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nenhuma playlist concluída encontrada.")

    return build_room_result(db, room, run)
