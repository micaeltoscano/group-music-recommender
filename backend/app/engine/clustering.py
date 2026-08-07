"""Agrupamento determinístico de perfis musicais temporários (PB-22)."""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Literal

from app.engine.taste import UserTasteProfile, calculate_pairwise_compatibility

ClusteringStatus = Literal["insufficient_evidence", "single_group", "clustered"]

MIN_PROFILES_FOR_SUBGROUPS = 3
MIN_SIGNALS_PER_PROFILE = 2
DEFAULT_SIMILARITY_THRESHOLD = 0.35


@dataclass(frozen=True)
class ProfileSimilarity:
    """Similaridade observada para um par de participantes."""

    user_a: int
    user_b: int
    score: float


@dataclass(frozen=True)
class TasteCluster:
    """Subgrupo transitório identificado somente pelos IDs dos integrantes."""

    id: str
    member_ids: tuple[int, ...]


@dataclass(frozen=True)
class TasteClusteringResult:
    """Resultado explícito do agrupamento, inclusive quando ele não é possível."""

    status: ClusteringStatus
    clusters: tuple[TasteCluster, ...]
    similarities: tuple[ProfileSimilarity, ...]
    reason: str

    def cluster_ids_for_members(self, member_ids: Iterable[int]) -> tuple[str, ...]:
        """Retorna, em ordem estável, os clusters que originaram uma candidata."""
        members = set(member_ids)
        return tuple(
            cluster.id
            for cluster in self.clusters
            if members.intersection(cluster.member_ids)
        )


def _signal_count(profile: UserTasteProfile) -> int:
    return len(profile.tracks) + len(profile.artists) + len(profile.genres)


def _connected_components(
    user_ids: Sequence[int],
    similarities: Sequence[ProfileSimilarity],
    threshold: float,
) -> list[tuple[int, ...]]:
    adjacency = {user_id: set() for user_id in user_ids}
    for similarity in similarities:
        if similarity.score < threshold:
            continue
        adjacency[similarity.user_a].add(similarity.user_b)
        adjacency[similarity.user_b].add(similarity.user_a)

    components: list[tuple[int, ...]] = []
    unseen = set(user_ids)
    while unseen:
        pending = [min(unseen)]
        component: set[int] = set()
        while pending:
            current = pending.pop()
            if current in component:
                continue
            component.add(current)
            unseen.discard(current)
            pending.extend(sorted(adjacency[current] - component, reverse=True))
        components.append(tuple(sorted(component)))
    return sorted(components)


def cluster_taste_profiles(
    profiles: Sequence[UserTasteProfile],
    *,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> TasteClusteringResult:
    """Agrupa perfis por componentes de similaridade, sem I/O ou estado persistente.

    Os únicos sinais consumidos são faixas, artistas e gêneros já extraídos dos
    snapshots temporários autorizados. Perfis esparsos e conjuntos sem qualquer
    par semelhante retornam um estado explícito de evidência insuficiente.
    """
    if not 0.0 <= similarity_threshold <= 1.0:
        raise ValueError("similarity_threshold deve estar entre 0 e 1.")

    ordered_profiles = sorted(profiles, key=lambda profile: profile.user_id)
    user_ids = [profile.user_id for profile in ordered_profiles]
    if len(user_ids) != len(set(user_ids)):
        raise ValueError("Cada perfil deve possuir um user_id único.")

    if len(ordered_profiles) < MIN_PROFILES_FOR_SUBGROUPS:
        return TasteClusteringResult(
            status="insufficient_evidence",
            clusters=(),
            similarities=(),
            reason="São necessários ao menos três perfis para avaliar subgrupos.",
        )

    sparse_user_ids = tuple(
        profile.user_id
        for profile in ordered_profiles
        if _signal_count(profile) < MIN_SIGNALS_PER_PROFILE
    )
    if sparse_user_ids:
        return TasteClusteringResult(
            status="insufficient_evidence",
            clusters=(),
            similarities=(),
            reason="Há perfis sem sinais musicais suficientes para comparação.",
        )

    similarities = tuple(
        ProfileSimilarity(
            user_a=profile_a.user_id,
            user_b=profile_b.user_id,
            score=round(calculate_pairwise_compatibility(profile_a, profile_b), 4),
        )
        for index, profile_a in enumerate(ordered_profiles)
        for profile_b in ordered_profiles[index + 1 :]
    )
    components = _connected_components(user_ids, similarities, similarity_threshold)

    if all(len(component) == 1 for component in components):
        return TasteClusteringResult(
            status="insufficient_evidence",
            clusters=(),
            similarities=similarities,
            reason="Nenhum par de perfis atingiu a similaridade mínima.",
        )

    clusters = tuple(
        TasteCluster(id=f"cluster-{index:02d}", member_ids=component)
        for index, component in enumerate(components, start=1)
    )
    if len(clusters) == 1:
        return TasteClusteringResult(
            status="single_group",
            clusters=clusters,
            similarities=similarities,
            reason="Os perfis formam um único grupo de afinidade; não há subgrupos distintos.",
        )

    return TasteClusteringResult(
        status="clustered",
        clusters=clusters,
        similarities=similarities,
        reason="Foram identificados subgrupos distintos de afinidade musical.",
    )
