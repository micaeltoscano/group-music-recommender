"""Pontuação individual e coletiva para as candidatas (PB-11)."""

from typing import Any, Dict, List
from app.engine.taste import UserTasteProfile
from app.engine.candidates import CandidateTrack


def calculate_individual_score(
    candidate: CandidateTrack,
    profile: UserTasteProfile,
    weights: Dict[str, float]
) -> float:
    """
    Calcula o score de afinidade de um usuário específico por uma candidata.
    """
    # 1. Afinidade de faixa
    if candidate.preference_by_user:
        track_affinity = candidate.preference_by_user.get(profile.user_id, 0.0)
    else:
        track_affinity = 1.0 if candidate.id in profile.tracks else 0.0
    
    # 2. Afinidade de artista
    candidate_artists = [
        a.get("id") 
        for a in candidate.raw_data.get("artists", []) 
        if a.get("id")
    ]
    artist_affinity = 1.0 if any(a in profile.artists for a in candidate_artists) else 0.0
    
    # 3. Afinidade de gênero
    candidate_genres = candidate.raw_data.get("genres", [])
    if candidate_genres:
        genre_affinity = 1.0 if any(g in profile.genres for g in candidate_genres) else 0.0
    else:
        # Fallback se a faixa não trouxer gêneros embutidos
        genre_affinity = artist_affinity * 0.5
        
    # 4. Popularidade
    pop_raw = candidate.raw_data.get("popularity")
    if pop_raw is None:
        pop_raw = 50
    try:
        popularity = float(pop_raw) / 100.0
    except (ValueError, TypeError):
        popularity = 0.5
    
    # 5. Novidade
    album = candidate.raw_data.get("album") or {}
    release_date = str(album.get("release_date", ""))
    novelty = 1.0 if release_date.startswith("202") else 0.5
    
    score = (
        track_affinity * weights.get("track_affinity", 0.4) +
        artist_affinity * weights.get("artist_affinity", 0.3) +
        genre_affinity * weights.get("genre_affinity", 0.2) +
        popularity * weights.get("popularity", 0.05) +
        novelty * weights.get("novelty", 0.05)
    )
    
    return round(score, 4)


def calculate_group_score(
    candidate: CandidateTrack,
    profiles: List[UserTasteProfile],
    individual_weights: Dict[str, float],
    group_weights: Dict[str, float],
    context_score: float = 1.0,
    diversity_score: float = 1.0
) -> Dict[str, Any]:
    """
    Avalia a candidata para o grupo inteiro com base nos scores individuais e regras coletivas.
    """
    if not profiles:
        return {
            "group_score": 0.0,
            "average_score": 0.0,
            "min_user_score": 0.0,
            "coverage": 0.0,
            "individual_scores": []
        }
        
    scores = [
        calculate_individual_score(candidate, p, individual_weights)
        for p in profiles
    ]
    
    average_score = sum(scores) / len(scores)
    min_score = min(scores)
    
    # Cobertura: proporção de pessoas que têm alguma afinidade razoável (score > 0.1)
    coverage = sum(1 for s in scores if s > 0.1) / len(scores)
    
    group_score = (
        average_score * group_weights.get("average_score", 0.5) +
        min_score * group_weights.get("min_score", 0.3) +
        coverage * group_weights.get("coverage", 0.1) +
        context_score * group_weights.get("context", 0.05) +
        diversity_score * group_weights.get("diversity", 0.05)
    )
    
    return {
        "group_score": round(group_score, 4),
        "average_score": round(average_score, 4),
        "min_user_score": round(min_score, 4),
        "coverage": round(coverage, 4),
        "individual_scores": scores
    }


def calculate_candidate_diversity_score(
    candidate: CandidateTrack,
    profiles: List[UserTasteProfile],
) -> float:
    """Mede quanto artista/gêneros ampliam o repertório já conhecido pelo grupo.

    É um sinal puro e determinístico. Modos com peso de diversidade zero continuam
    matematicamente inalterados; o modo Descoberta passa a consumir este valor.
    """

    known_artists = {artist_id for profile in profiles for artist_id in profile.artists}
    known_genres = {
        genre.strip().lower() for profile in profiles for genre in profile.genres if genre.strip()
    }
    candidate_artists = {
        str(artist.get("id"))
        for artist in candidate.raw_data.get("artists", [])
        if isinstance(artist, dict) and artist.get("id")
    }
    candidate_genres = {
        genre.strip().lower()
        for genre in candidate.raw_data.get("genres", [])
        if isinstance(genre, str) and genre.strip()
    }

    artist_diversity = (
        1.0 if candidate_artists and candidate_artists.isdisjoint(known_artists) else 0.0
    )
    if candidate_genres:
        genre_diversity = len(candidate_genres - known_genres) / len(candidate_genres)
    else:
        genre_diversity = artist_diversity
    return round((artist_diversity * 0.6) + (genre_diversity * 0.4), 4)
