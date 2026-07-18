"""Pesos configuráveis para o cálculo de pontuação (PB-11) e Modos de Consenso (PB-12)."""

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

# O Vibe Check ajusta o resultado na margem, sem substituir os componentes
# centrais de afinidade, consenso, justica e contexto.
VIBE_CHECK_INFLUENCE = 0.20

CONSENSUS_MODES = {
    "democratic": {
        "individual": {
            "track_affinity": 0.4,
            "artist_affinity": 0.3,
            "genre_affinity": 0.2,
            "popularity": 0.05,
            "novelty": 0.05,
        },
        "group": {
            "average_score": 0.45,
            "min_score": 0.25,
            "coverage": 0.15,
            "context": 0.15,
            "diversity": 0.0,
        },
        "rejection_penalty": 0.5,  # Reduz a pontuação da música em 50% caso tenha veto
    },
    "safe_party": {
        "individual": {
            "track_affinity": 0.5,
            "artist_affinity": 0.2,
            "genre_affinity": 0.1,
            "popularity": 0.2,   # Favorece músicas populares (conhecidas)
            "novelty": 0.0,      # Não arrisca em novidades
        },
        "group": {
            "average_score": 0.25,
            "min_score": 0.45,   # Fortemente focado no "least misery" (ninguém odiar)
            "coverage": 0.15,
            "context": 0.15,
            "diversity": 0.0,
        },
        "rejection_penalty": 1.0,  # Veto derruba a música totalmente (penalidade de 100%)
    }
}
