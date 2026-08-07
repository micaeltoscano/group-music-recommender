import pytest
from app.engine.candidates import CandidateTrack
from app.engine.taste import UserTasteProfile
from app.engine.scoring import calculate_individual_score, calculate_group_score

def test_pb11_qa_missing_album_or_none():
    """Garante que dict sem album ou album=None não quebre a função."""
    # album: None
    candidate = CandidateTrack(
        track_id="t1",
        raw_data={"popularity": 50, "album": None},
        source_user_ids={1}
    )
    profile = UserTasteProfile(1, {"items":[]}, {"items":[]})

    # QA Check: se album for None, album.get("release_date") no código vai falhar com AttributeError?
    # Vamos verificar.
    try:
        score = calculate_individual_score(candidate, profile, {"novelty": 1.0})
    except AttributeError:
        pytest.fail("A função quebrou porque 'album' é None e foi usado como dict.")

def test_pb11_qa_popularity_string():
    """Se popularidade vier como string do JSON por acaso, deve ser resiliente ou tratada."""
    candidate = CandidateTrack(
        track_id="t1",
        raw_data={"popularity": "80", "album": {}},
        source_user_ids={1}
    )
    profile = UserTasteProfile(1, {"items":[]}, {"items":[]})

    try:
        score = calculate_individual_score(candidate, profile, {"popularity": 1.0})
        # se der certo, OK. se quebrar por causa da divisão de str por float, é bug.
    except TypeError:
        pytest.fail("A função quebrou porque a popularidade é string.")

def test_pb11_qa_group_score_empty_profiles():
    """Grupo sem perfis deve retornar dicionário zerado sem quebrar division by zero."""
    result = calculate_group_score(
        CandidateTrack("t1", {}, set()),
        [],
        {},
        {}
    )
    assert result["group_score"] == 0.0
