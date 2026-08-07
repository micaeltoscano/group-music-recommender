"""Módulo para normalização e correspondência de nomes de faixas e artistas (PB-14)."""

import re
from difflib import SequenceMatcher

def normalize_string(text: str) -> str:
    """
    Normaliza uma string para comparação.
    Converte para minúsculas e remove termos comuns em versões de músicas
    como '- Remastered', '(Live)', '(Acoustic)', etc.
    """
    if not text:
        return ""

    text = text.lower()

    # Remove textos entre parênteses ou colchetes, que geralmente são (Remastered 2011), (Live), etc.
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'\[.*?\]', '', text)

    # Remove o que vier depois de um hífen (ex: "Song Name - Remastered")
    text = text.split('-')[0]

    # Remove espaços extras e caracteres especiais (mantendo letras e números)
    text = re.sub(r'[^a-z0-9\s]', '', text)

    return text.strip()


def calculate_match_confidence(query_title: str, query_artist: str, result_title: str, result_artist: str) -> float:
    """
    Calcula a confiança (0.0 a 1.0) da correspondência entre a consulta e o resultado.
    Dá um peso maior para o título da faixa (ex: 60%) e um pouco menor para o artista (40%).
    """
    norm_query_title = normalize_string(query_title)
    norm_result_title = normalize_string(result_title)

    norm_query_artist = normalize_string(query_artist)
    norm_result_artist = normalize_string(result_artist)

    # Se, após a normalização, algum for vazio, a confiança é baixa
    if not norm_query_title or not norm_result_title:
        title_score = 0.0
    else:
        title_score = SequenceMatcher(None, norm_query_title, norm_result_title).ratio()

    if not norm_query_artist or not norm_result_artist:
        artist_score = 0.0
    else:
        artist_score = SequenceMatcher(None, norm_query_artist, norm_result_artist).ratio()

    # Combinação ponderada
    return (title_score * 0.6) + (artist_score * 0.4)
