"""Balanceamento determinístico entre subgrupos após justiça e rejeição (PB-24)."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from app.engine.clustering import TasteClusteringResult

DEFAULT_MAX_CLUSTER_SHARE = 0.60
DEFAULT_VETO_THRESHOLD = 0.05


@dataclass(frozen=True, slots=True)
class ClusterAllocation:
    """Cluster contabilizado para uma candidata no prefixo balanceado."""

    candidate_id: str
    cluster_id: str | None


@dataclass(frozen=True)
class SubgroupBalanceResult:
    """Ordem balanceada e evidências agregadas da decisão."""

    ranked_candidates: tuple[dict[str, Any], ...]
    applied: bool
    prefix_size: int
    max_per_cluster: int
    cluster_counts: tuple[tuple[str, int], ...]
    allocations: tuple[ClusterAllocation, ...]


def _candidate_id(item: dict[str, Any]) -> str:
    candidate = item.get("candidate")
    return str(getattr(candidate, "id", ""))


def _cluster_ids(item: dict[str, Any], known_cluster_ids: set[str]) -> tuple[str, ...]:
    candidate = item.get("candidate")
    raw_ids = getattr(candidate, "source_cluster_ids", ())
    return tuple(sorted({str(cluster_id) for cluster_id in raw_ids} & known_cluster_ids))


def _has_veto(item: dict[str, Any], veto_threshold: float) -> bool:
    return any(
        float(score) <= veto_threshold
        for score in item.get("individual_scores", [])
    )


def balance_subgroup_candidates(
    scored_candidates: Sequence[dict[str, Any]],
    clustering: TasteClusteringResult | None,
    *,
    target_size: int,
    max_cluster_share: float = DEFAULT_MAX_CLUSTER_SHARE,
    veto_threshold: float = DEFAULT_VETO_THRESHOLD,
) -> SubgroupBalanceResult:
    """Reordena o prefixo final por menor representação, sem trocar seu conjunto.

    Somente candidatas sem veto podem ser promovidas. Quando faltam opções para
    cumprir o teto por cluster, o restante é preenchido na ordem original como
    melhor esforço. Popularidade, score, fairness e membros selecionados não são
    recalculados nem alterados.
    """
    if target_size < 0:
        raise ValueError("target_size não pode ser negativo.")
    if not 0.5 <= max_cluster_share <= 1.0:
        raise ValueError("max_cluster_share deve estar entre 0.5 e 1.")
    if not 0.0 <= veto_threshold <= 1.0:
        raise ValueError("veto_threshold deve estar entre 0 e 1.")

    ranked = list(scored_candidates)
    prefix_size = min(target_size, len(ranked))
    if (
        prefix_size <= 1
        or clustering is None
        or clustering.status != "clustered"
        or len(clustering.clusters) < 2
    ):
        return SubgroupBalanceResult(tuple(ranked), False, prefix_size, 0, (), ())

    cluster_ids = tuple(sorted(cluster.id for cluster in clustering.clusters))
    known_cluster_ids = set(cluster_ids)
    max_per_cluster = max(1, math.ceil(prefix_size * max_cluster_share))
    counts = {cluster_id: 0 for cluster_id in cluster_ids}
    remaining = list(enumerate(ranked))
    balanced_prefix: list[tuple[int, dict[str, Any]]] = []
    allocations: list[ClusterAllocation] = []

    while len(balanced_prefix) < prefix_size:
        options: list[tuple[int, int, str | None, int, dict[str, Any]]] = []
        minimum_count = min(counts.values())
        for remaining_position, (original_index, item) in enumerate(remaining):
            if _has_veto(item, veto_threshold):
                continue
            item_cluster_ids = _cluster_ids(item, known_cluster_ids)
            if item_cluster_ids:
                available_ids = [
                    cluster_id
                    for cluster_id in item_cluster_ids
                    if counts[cluster_id] < max_per_cluster
                ]
                if not available_ids:
                    continue
                assigned_cluster_id = min(
                    available_ids,
                    key=lambda cluster_id: (counts[cluster_id], cluster_id),
                )
                representation = counts[assigned_cluster_id]
            else:
                assigned_cluster_id = None
                representation = minimum_count
            options.append(
                (
                    representation,
                    original_index,
                    assigned_cluster_id,
                    remaining_position,
                    item,
                )
            )

        if not options:
            break
        _, original_index, assigned_cluster_id, remaining_position, item = min(
            options,
            key=lambda option: (option[0], option[1], _candidate_id(option[4])),
        )
        remaining.pop(remaining_position)
        balanced_prefix.append((original_index, item))
        if assigned_cluster_id is not None:
            counts[assigned_cluster_id] += 1
        allocations.append(ClusterAllocation(_candidate_id(item), assigned_cluster_id))

    # Melhor esforço: vetos e clusters já no teto nunca são promovidos pelo
    # balanceador, mas preenchem o tamanho solicitado se o pool não tiver opção.
    remaining.sort(key=lambda entry: entry[0])
    while remaining and len(balanced_prefix) < prefix_size:
        original_index, item = remaining.pop(0)
        balanced_prefix.append((original_index, item))
        item_cluster_ids = _cluster_ids(item, known_cluster_ids)
        assigned_cluster_id = (
            min(item_cluster_ids, key=lambda cluster_id: (counts[cluster_id], cluster_id))
            if item_cluster_ids
            else None
        )
        if assigned_cluster_id is not None:
            counts[assigned_cluster_id] += 1
        allocations.append(ClusterAllocation(_candidate_id(item), assigned_cluster_id))

    ordered_entries = balanced_prefix + remaining
    ordered = [item for _, item in ordered_entries]
    original_indices = [index for index, _ in ordered_entries]
    applied = original_indices != list(range(len(ranked)))
    return SubgroupBalanceResult(
        ranked_candidates=tuple(ordered),
        applied=applied,
        prefix_size=prefix_size,
        max_per_cluster=max_per_cluster,
        cluster_counts=tuple((cluster_id, counts[cluster_id]) for cluster_id in cluster_ids),
        allocations=tuple(allocations),
    )
