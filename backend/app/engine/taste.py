"""Modelagem de gosto musical e cálculo de compatibilidade (PNE)."""

from typing import Any, Dict, List, Set


class UserTasteProfile:
    """Perfil de gosto musical extraído de um snapshot."""

    def __init__(
        self,
        user_id: int,
        top_tracks_data: Dict[str, Any],
        top_artists_data: Dict[str, Any],
    ) -> None:
        self.user_id = user_id
        self.tracks: Set[str] = set()
        self.artists: Set[str] = set()
        self.genres: Set[str] = set()

        for item in top_tracks_data.get("items", []):
            if track_id := item.get("id"):
                self.tracks.add(track_id)
            for artist in item.get("artists", []):
                if artist_id := artist.get("id"):
                    self.artists.add(artist_id)

        for item in top_artists_data.get("items", []):
            if artist_id := item.get("id"):
                self.artists.add(artist_id)
            for genre in item.get("genres", []):
                if isinstance(genre, str):
                    self.genres.add(genre.lower().strip())


def jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    """Calcula a similaridade de Jaccard entre dois conjuntos. Retorna 0.0 se ambos forem vazios."""
    if not set1 and not set2:
        return 0.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return float(intersection) / union


def calculate_pairwise_compatibility(
    profile1: UserTasteProfile, profile2: UserTasteProfile
) -> float:
    """
    Calcula a compatibilidade entre dois usuários usando uma média ponderada.
    Pesos sugeridos (MVP): faixas (20%), artistas (40%), gêneros (40%).
    """
    track_sim = jaccard_similarity(profile1.tracks, profile2.tracks)
    artist_sim = jaccard_similarity(profile1.artists, profile2.artists)
    genre_sim = jaccard_similarity(profile1.genres, profile2.genres)

    return (track_sim * 0.2) + (artist_sim * 0.4) + (genre_sim * 0.4)


def calculate_group_compatibility(profiles: List[UserTasteProfile]) -> float:
    """
    Calcula a compatibilidade média de um grupo (pares únicos).
    Retorna 1.0 para grupos de um único integrante e 0.0 se estiver vazio.
    """
    if not profiles:
        return 0.0
    if len(profiles) == 1:
        return 1.0

    total_sim = 0.0
    pairs_count = 0
    num_profiles = len(profiles)

    for i in range(num_profiles):
        for j in range(i + 1, num_profiles):
            total_sim += calculate_pairwise_compatibility(profiles[i], profiles[j])
            pairs_count += 1

    return total_sim / pairs_count
