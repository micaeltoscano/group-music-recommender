"""Identificação pura e determinística de faixas-ponte (PB-23)."""

from collections.abc import Sequence
from dataclasses import dataclass

from app.engine.candidates import CandidateTrack
from app.engine.clustering import TasteClusteringResult
from app.engine.scoring import calculate_individual_score
from app.engine.taste import UserTasteProfile

DEFAULT_MIN_CLUSTER_ACCEPTANCE = 0.25
MIN_ACCEPTED_CLUSTERS = 2
NON_AFFINITY_SIGNALS = frozenset({"popularity", "novelty"})


@dataclass(frozen=True)
class ClusterAcceptance:
    """Afinidade média de uma candidata dentro de um cluster."""

    cluster_id: str
    score: float


@dataclass(frozen=True)
class BridgeTrackEvaluation:
    """Avaliação transitória usada pelo ranqueamento e pela explicação."""

    is_bridge: bool
    bridge_score: float
    accepted_cluster_ids: tuple[str, ...]
    cluster_acceptance: tuple[ClusterAcceptance, ...]


def evaluate_bridge_candidate(
    candidate: CandidateTrack,
    profiles: Sequence[UserTasteProfile],
    clustering: TasteClusteringResult | None,
    individual_weights: dict[str, float],
    *,
    min_cluster_acceptance: float = DEFAULT_MIN_CLUSTER_ACCEPTANCE,
) -> BridgeTrackEvaluation:
    """Marca ponte quando dois ou mais subgrupos aceitam a candidata.

    A aceitação de cada cluster é a média dos componentes de afinidade do score
    individual definido no PB-11. Popularidade e novidade são zeradas porque
    são sinais globais e não comprovam ligação entre gostos. O `bridge_score`
    é o segundo maior score entre os clusters: uma medida conservadora da força
    da ligação entre pelo menos dois subgrupos.
    """
    if not 0.0 <= min_cluster_acceptance <= 1.0:
        raise ValueError("min_cluster_acceptance deve estar entre 0 e 1.")

    if clustering is None or clustering.status != "clustered":
        return BridgeTrackEvaluation(False, 0.0, (), ())

    affinity_weights = {
        signal: 0.0 if signal in NON_AFFINITY_SIGNALS else weight
        for signal, weight in individual_weights.items()
    }
    profiles_by_id = {profile.user_id: profile for profile in profiles}
    acceptances: list[ClusterAcceptance] = []
    for cluster in clustering.clusters:
        cluster_profiles = [
            profiles_by_id[user_id]
            for user_id in cluster.member_ids
            if user_id in profiles_by_id
        ]
        if len(cluster_profiles) != len(cluster.member_ids) or not cluster_profiles:
            score = 0.0
        else:
            individual_scores = [
                calculate_individual_score(candidate, profile, affinity_weights)
                for profile in cluster_profiles
            ]
            score = round(sum(individual_scores) / len(individual_scores), 4)
        acceptances.append(ClusterAcceptance(cluster.id, score))

    accepted_cluster_ids = tuple(
        acceptance.cluster_id
        for acceptance in acceptances
        if acceptance.score >= min_cluster_acceptance
    )
    descending_scores = sorted(
        (acceptance.score for acceptance in acceptances),
        reverse=True,
    )
    bridge_score = (
        descending_scores[MIN_ACCEPTED_CLUSTERS - 1]
        if len(descending_scores) >= MIN_ACCEPTED_CLUSTERS
        else 0.0
    )
    is_bridge = len(accepted_cluster_ids) >= MIN_ACCEPTED_CLUSTERS
    return BridgeTrackEvaluation(
        is_bridge=is_bridge,
        bridge_score=round(bridge_score, 4) if is_bridge else 0.0,
        accepted_cluster_ids=accepted_cluster_ids if is_bridge else (),
        cluster_acceptance=tuple(acceptances),
    )
