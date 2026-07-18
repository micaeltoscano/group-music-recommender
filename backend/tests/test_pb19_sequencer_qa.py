"""QA (validador independente) — PB-19 (sequenciamento).

Sondagem adversarial da autoridade de QA. Onde o Dev usa exemplos, aqui a
verificação é por **propriedade exaustiva**:

- CT-PB19-01: para TODA entrada pequena onde existe um arranjo sem artistas
  adjacentes, o sequenciador precisa produzir um (verificado por força bruta,
  comparando com um oráculo de permutações).
- CT-PB19-02: a abertura é a de maior aceitação entre as que ainda permitem
  terminar sem adjacência.
- CT-PB19-04: cap de 2/artista sempre respeitado após sequenciar (exaustivo).
- Determinismo: mesma entrada → mesma saída, e permutar a ordem de entrada não
  muda o resultado (desempates estáveis).
"""

from __future__ import annotations

import itertools
import random

import pytest

from app.engine.sequencer import SequencerTrack, sequence_tracks


def _tracks(spec: list[tuple[str, float]]) -> list[SequencerTrack]:
    """spec: lista de (artista, aceitação). risk = 1 - aceitação."""
    out = []
    for i, (artist, acc) in enumerate(spec, start=1):
        out.append(
            SequencerTrack(
                track_id=f"t{i}",
                artist=artist,
                acceptance=acc,
                risk=1.0 - acc,
                original_position=i,
            )
        )
    return out


def _has_adjacent(order: list[SequencerTrack]) -> bool:
    return any(
        a.artist.casefold() == b.artist.casefold()
        for a, b in zip(order, order[1:])
    )


def _nonadjacent_arrangement_exists(tracks: list[SequencerTrack]) -> bool:
    """Oráculo: existe alguma permutação sem artistas adjacentes?"""
    ids = list(range(len(tracks)))
    for perm in itertools.permutations(ids):
        seq = [tracks[i] for i in perm]
        if not _has_adjacent(seq):
            return True
    return False


# ---------------------------------------------------------------------------
# CT-PB19-01 — exaustivo: se existe solução sem adjacência, produzimos uma
# ---------------------------------------------------------------------------

def test_ct01_exaustivo_sem_adjacencia_quando_possivel():
    artists = ["A", "B", "C"]
    checked = 0
    for size in range(2, 7):
        # todas as combinações de artistas (com repetição) de tamanho `size`
        for combo in itertools.product(artists, repeat=size):
            # aceitação distinta por posição para forçar desempates variados
            spec = [(art, 1.0 - idx * 0.03) for idx, art in enumerate(combo)]
            tracks = _tracks(spec)
            result = sequence_tracks(tracks, max_per_artist=99, limit=None)
            # sequenciador não perde faixas quando o cap é frouxo
            assert len(result) == size
            checked += 1
            if _nonadjacent_arrangement_exists(tracks):
                assert not _has_adjacent(result), (
                    f"havia arranjo sem adjacência para {combo}, mas o "
                    f"sequenciador produziu {[t.artist for t in result]}"
                )
    assert checked > 300  # garante que a varredura foi ampla


# ---------------------------------------------------------------------------
# CT-PB19-02 — abertura de alta aceitação
# ---------------------------------------------------------------------------

def test_ct02_abertura_e_de_alta_aceitacao():
    # A tem a maior aceitação e há espaço para não gerar adjacência
    spec = [("A", 0.95), ("B", 0.90), ("A", 0.50), ("C", 0.40), ("B", 0.30)]
    result = sequence_tracks(_tracks(spec), max_per_artist=2, limit=None)
    assert result[0].acceptance == pytest.approx(0.95)
    assert not _has_adjacent(result)


def test_ct02_abertura_cede_se_maior_aceitacao_forcaria_adjacencia():
    """Se abrir pela faixa de maior aceitação tornaria a adjacência inevitável,
    a abertura deve ceder para permitir um final limpo (CT-PB19-01 tem
    prioridade sobre a abertura pura)."""
    # A domina (3 de 5) — abrir por A na posição errada pode forçar A,A no fim.
    spec = [("A", 0.99), ("A", 0.98), ("A", 0.97), ("B", 0.50), ("C", 0.40)]
    tracks = _tracks(spec)
    result = sequence_tracks(tracks, max_per_artist=99, limit=None)
    # com 3 As e 2 outros (total 5), existe arranjo sem adjacência (A_A_A)
    assert _nonadjacent_arrangement_exists(tracks)
    assert not _has_adjacent(result)


# ---------------------------------------------------------------------------
# CT-PB19-04 — cap sempre respeitado após sequenciar (exaustivo)
# ---------------------------------------------------------------------------

def test_ct04_cap_sempre_respeitado():
    artists = ["A", "B", "C"]
    for size in range(2, 7):
        for combo in itertools.product(artists, repeat=size):
            spec = [(art, 1.0 - idx * 0.05) for idx, art in enumerate(combo)]
            result = sequence_tracks(_tracks(spec), max_per_artist=2, limit=None)
            counts: dict[str, int] = {}
            for t in result:
                counts[t.artist] = counts.get(t.artist, 0) + 1
            assert all(c <= 2 for c in counts.values()), (
                f"cap violado para {combo}: {counts}"
            )


# ---------------------------------------------------------------------------
# Determinismo e estabilidade a permutações de entrada
# ---------------------------------------------------------------------------

def test_determinismo_mesma_entrada_mesma_saida():
    spec = [("A", 0.9), ("B", 0.8), ("A", 0.7), ("C", 0.6), ("B", 0.5), ("C", 0.4)]
    a = [t.track_id for t in sequence_tracks(_tracks(spec), max_per_artist=2, limit=None)]
    b = [t.track_id for t in sequence_tracks(_tracks(spec), max_per_artist=2, limit=None)]
    assert a == b


def test_permutar_entrada_nao_muda_resultado_por_ids():
    """Desempates usam original_position/id; se preservarmos o par
    (artista, aceitação, original_position) de cada faixa, a saída — como
    conjunto ordenado de artistas/aceitações — deve ser idêntica independente
    da ordem em que as faixas são passadas."""
    base = [
        SequencerTrack(track_id=f"t{i}", artist=art, acceptance=acc, risk=1 - acc, original_position=i)
        for i, (art, acc) in enumerate(
            [("A", 0.9), ("B", 0.8), ("A", 0.7), ("C", 0.6), ("B", 0.5)], start=1
        )
    ]
    reference = [t.track_id for t in sequence_tracks(base, max_per_artist=2, limit=None)]
    rng = random.Random(1234)
    for _ in range(20):
        shuffled = base[:]
        rng.shuffle(shuffled)
        got = [t.track_id for t in sequence_tracks(shuffled, max_per_artist=2, limit=None)]
        assert got == reference, "resultado depende da ordem de entrada — desempate instável"


# ---------------------------------------------------------------------------
# CT-PB19-05 — robustez de bordas
# ---------------------------------------------------------------------------

def test_ct05_bordas():
    assert sequence_tracks([], max_per_artist=2, limit=None) == []
    single = sequence_tracks(_tracks([("A", 0.5)]), max_per_artist=2, limit=None)
    assert len(single) == 1
    # artista único: cap corta para 2, sem erro
    solo = sequence_tracks(_tracks([("A", 0.9), ("A", 0.8), ("A", 0.7)]), max_per_artist=2, limit=None)
    assert len(solo) == 2
    assert all(t.artist == "A" for t in solo)
