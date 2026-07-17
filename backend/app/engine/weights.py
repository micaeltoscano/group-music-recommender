"""Pesos configuráveis para o cálculo de pontuação (PB-11)."""

DEFAULT_INDIVIDUAL_WEIGHTS = {
    "track_affinity": 0.4,
    "artist_affinity": 0.3,
    "genre_affinity": 0.2,
    "popularity": 0.05,
    "novelty": 0.05,
}

DEFAULT_GROUP_WEIGHTS = {
    "average_score": 0.5,
    "min_score": 0.3,
    "coverage": 0.1,
    "context": 0.05,
    "diversity": 0.05,
}
