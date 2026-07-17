"""Montagem e persistência do resultado explicável de uma execução (PB-16).

As métricas de compatibilidade e justiça (fairness) são calculadas **na conclusão
do run**, a partir das faixas efetivamente correspondidas, e persistidas no próprio
`PlaylistRun`. O endpoint de resultado apenas lê o que foi calculado pela execução
(com recomputo de contingência para runs antigos, anteriores a esta persistência).

Semânticas (documentadas propositalmente):
- `compatibility_score`: percentual das faixas selecionadas que agradam a mais de um
  integrante (fontes com 2+ contribuintes). Mede o quanto o grupo tem gosto em comum.
- `fairness_score`: índice de justiça de Jain sobre a contagem de contribuições por
  integrante — 100 = todos igualmente representados; cai conforme a distribuição
  fica desigual.
- Explicações agregadas: nunca nomeiam quem **rejeitou** algo, nem descrevem gosto
  individual negativo (ver README §3.2). O crédito **positivo** por integrante
  (`contributed_by`) é mantido por decisão de produto (grupo consensual).
"""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.db.models import MusicSession, MusicSessionMember, PlaylistRun, PlaylistRunTrack
from app.schemas.rooms import (
    MemberRepresentation,
    RoomResultResponse,
    TrackResultResponse,
)
from app.services.room_service import list_room_members


def _parse_source(raw: str | None) -> list[int]:
    """Interpreta o campo `source` (JSON com ids dos contribuintes). Tolera lixo."""
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        return []
    if not isinstance(parsed, list):
        return []
    result: list[int] = []
    for item in parsed:
        try:
            result.append(int(item))
        except (ValueError, TypeError):
            continue
    return result


def _jain_index(counts: list[int]) -> int:
    """Índice de justiça de Jain em 0..100 (100 = distribuição perfeitamente igual)."""
    total = sum(counts)
    if total <= 0 or not counts:
        return 0
    sum_sq = sum(c * c for c in counts)
    if sum_sq == 0:
        return 0
    index = (total * total) / (len(counts) * sum_sq)
    return round(index * 100)


def _reason_for(num_contributors: int) -> str:
    """Justificativa agregada por faixa, sem nomear integrantes."""
    if num_contributors > 1:
        return f"Combina com o gosto de {num_contributors} integrantes."
    if num_contributors == 1:
        return "Escolhida a partir do gosto de um dos integrantes."
    return "Incluída para reforçar o consenso do grupo."


def compute_metrics(member_ids: list[int], tracks: list[PlaylistRunTrack]) -> dict:
    """Calcula métricas e explicações a partir das faixas correspondidas.

    Retorna um dicionário serializável: compatibility_score, fairness_score,
    representation (user_id/percentage) e why_items.
    """
    total = len(tracks)
    member_set = set(member_ids)
    counts: dict[int, int] = {uid: 0 for uid in member_ids}
    shared = 0

    for track in tracks:
        contributors = [uid for uid in _parse_source(track.source) if uid in member_set]
        if len(contributors) > 1:
            shared += 1
        for uid in contributors:
            counts[uid] += 1

    representation = [
        {
            "user_id": uid,
            "percentage": round(100 * counts[uid] / total) if total else 0,
        }
        for uid in member_ids
    ]
    compatibility_score = round(100 * shared / total) if total else 0
    fairness_score = _jain_index([counts[uid] for uid in member_ids])

    zero_members = [uid for uid in member_ids if counts[uid] == 0]
    if zero_members:
        cobertura = (
            f"{len(zero_members)} integrante(s) ainda sem faixa que os represente diretamente."
        )
    else:
        cobertura = f"Todos os {len(member_ids)} integrantes têm faixas que os representam."

    if fairness_score >= 70:
        justica = f"Distribuição equilibrada entre os integrantes (índice de justiça {fairness_score}%)."
    else:
        justica = f"Distribuição desigual entre os integrantes (índice de justiça {fairness_score}%)."

    why_items = [
        cobertura,
        f"{compatibility_score}% das faixas agradam a mais de um integrante.",
        justica,
        "Limite de 2 faixas por artista aplicado na seleção.",
    ]

    return {
        "compatibility_score": compatibility_score,
        "fairness_score": fairness_score,
        "representation": representation,
        "why_items": why_items,
    }


def _matched_tracks(db: Session, run_id) -> list[PlaylistRunTrack]:
    return (
        db.query(PlaylistRunTrack)
        .filter(PlaylistRunTrack.run_id == run_id, PlaylistRunTrack.status == "matched")
        .order_by(PlaylistRunTrack.created_at)
        .all()
    )


def _member_ids(db: Session, session_id) -> list[int]:
    return [
        row.user_id
        for row in (
            db.query(MusicSessionMember)
            .filter(MusicSessionMember.session_id == session_id)
            .order_by(MusicSessionMember.joined_at, MusicSessionMember.user_id)
            .all()
        )
    ]


def finalize_run_metrics(db: Session, run: PlaylistRun) -> None:
    """Calcula e persiste as métricas da execução no próprio run (sem commit).

    Deve ser chamada quando a execução conclui, com as faixas já correspondidas e
    o capping por artista já aplicado.
    """
    tracks = _matched_tracks(db, run.id)
    member_ids = _member_ids(db, run.session_id)
    metrics = compute_metrics(member_ids, tracks)

    run.compatibility_score = metrics["compatibility_score"]
    run.fairness_score = metrics["fairness_score"]
    run.explanation_json = json.dumps(
        {
            "representation": metrics["representation"],
            "why_items": metrics["why_items"],
        }
    )


def build_room_result(db: Session, room: MusicSession, run: PlaylistRun) -> RoomResultResponse:
    """Monta o payload de resultado lendo as métricas persistidas na execução.

    Para runs antigos (sem métricas persistidas) recomputa como contingência.
    """
    tracks = _matched_tracks(db, run.id)
    members_map = {
        user.id: (user.display_name or f"Membro {user.id}")
        for _, user in list_room_members(db, room.id)
    }
    member_ids = list(members_map.keys())

    track_results: list[TrackResultResponse] = []
    for track in tracks:
        contributors = [uid for uid in _parse_source(track.source) if uid in members_map]
        names = [members_map[uid] for uid in contributors]
        track_results.append(
            TrackResultResponse(
                name=track.name,
                artist=track.artist,
                spotify_url=track.spotify_uri,
                reason=_reason_for(len(names)),
                contributed_by=names,
            )
        )

    # Métricas: preferir o que a execução persistiu; recomputar só se ausente.
    stored = None
    if run.explanation_json:
        try:
            stored = json.loads(run.explanation_json)
        except (ValueError, TypeError):
            stored = None

    if stored is not None and run.compatibility_score is not None and run.fairness_score is not None:
        compatibility_score = run.compatibility_score
        fairness_score = run.fairness_score
        representation_data = stored.get("representation", [])
        why_items = stored.get("why_items", [])

        # DEF-PB16-04: o snapshot foi persistido no momento da conclusão do run e
        # pode não incluir membros que entraram na sala depois. Complementa com
        # percentage 0 para que todo membro ATUAL apareça na própria representação.
        represented_ids = {item["user_id"] for item in representation_data}
        missing_ids = [uid for uid in member_ids if uid not in represented_ids]
        if missing_ids:
            representation_data = representation_data + [
                {"user_id": uid, "percentage": 0} for uid in missing_ids
            ]
    else:
        metrics = compute_metrics(member_ids, tracks)
        compatibility_score = metrics["compatibility_score"]
        fairness_score = metrics["fairness_score"]
        representation_data = metrics["representation"]
        why_items = metrics["why_items"]

    representation = [
        MemberRepresentation(
            user_id=item["user_id"],
            display_name=members_map.get(item["user_id"], f"Membro {item['user_id']}"),
            percentage=item["percentage"],
        )
        for item in representation_data
    ]

    return RoomResultResponse(
        playlist_url=run.spotify_playlist_url,
        compatibility_score=compatibility_score,
        fairness_score=fairness_score,
        representation=representation,
        tracks=track_results,
        why_items=why_items,
    )
