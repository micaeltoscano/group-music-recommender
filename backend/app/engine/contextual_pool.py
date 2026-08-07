"""Composição determinística entre âncoras pessoais e descoberta contextual."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

DEFAULT_CONTEXT_THRESHOLD = 0.60
DEFAULT_VETO_THRESHOLD = 0.05


def _is_contextual(item: dict[str, Any]) -> bool:
    candidate = item.get("candidate")
    return str(getattr(candidate, "origin", "spotify_top")).startswith("lastfm_")


def _has_veto(item: dict[str, Any], veto_threshold: float) -> bool:
    return any(
        float(score) <= veto_threshold
        for score in item.get("individual_scores", ())
    )


def blend_contextual_candidates(
    scored_candidates: Sequence[dict[str, Any]],
    *,
    target_size: int,
    contextual_share: float,
    minimum_anchor_share: float = 0.40,
    context_threshold: float = DEFAULT_CONTEXT_THRESHOLD,
    veto_threshold: float = DEFAULT_VETO_THRESHOLD,
) -> list[dict[str, Any]]:
    """Reserva contexto no prefixo sem promover vetos ou apagar os Tops.

    A função só reordena/recorta dados já pontuados. Se não houver descoberta
    elegível, mantém exatamente o fallback recebido.
    """

    if target_size < 0:
        raise ValueError("target_size não pode ser negativo.")
    if not 0.0 <= contextual_share <= 0.60:
        raise ValueError("contextual_share deve estar entre 0 e 0.60.")
    if not 0.0 <= minimum_anchor_share <= 1.0:
        raise ValueError("minimum_anchor_share deve estar entre 0 e 1.")

    ranked = list(scored_candidates)
    size = min(target_size, len(ranked))
    if not ranked or size == 0 or contextual_share == 0:
        return ranked[:size]

    contextual = [
        item
        for item in ranked
        if _is_contextual(item)
        and float(item.get("context_score", 0.0)) >= context_threshold
        and not _has_veto(item, veto_threshold)
    ]
    anchors = [item for item in ranked if not _is_contextual(item)]
    if not contextual or not anchors:
        return ranked[:size]

    minimum_anchors = min(len(anchors), math.ceil(size * minimum_anchor_share))
    desired_context = min(
        len(contextual),
        int(round(size * contextual_share)),
        size - minimum_anchors,
    )
    if desired_context <= 0:
        return ranked[:size]

    desired_anchors = size - desired_context
    selected: list[dict[str, Any]] = []
    context_index = 0
    anchor_index = 0
    # Distribui as duas origens ao longo do prefixo, evitando um bloco artificial
    # de descoberta antes ou depois das preferências pessoais.
    for position in range(size):
        expected_context = ((position + 1) * desired_context) // size
        use_context = context_index < expected_context
        if use_context and context_index < desired_context:
            selected.append(contextual[context_index])
            context_index += 1
        elif anchor_index < desired_anchors:
            selected.append(anchors[anchor_index])
            anchor_index += 1
        elif context_index < desired_context:
            selected.append(contextual[context_index])
            context_index += 1

    return selected
