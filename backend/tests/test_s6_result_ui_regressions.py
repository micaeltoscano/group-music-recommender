"""Regressões da correção visual e de navegação do resultado na Sprint 6."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_result_return_identifies_the_run_being_left() -> None:
    result_source = (ROOT / "frontend/src/Result.jsx").read_text()
    room_source = (ROOT / "frontend/src/Room.jsx").read_text()

    assert "stayForRunId: String(result?.run_id || '')" in result_source
    assert "location.state?.stayForRunId" in room_source
    assert "String(generation?.run_id) === String(stayedRunId)" in room_source
    assert "generation?.status === 'completed' && !isExplicitReturn" in room_source


def test_result_uses_product_layout_and_real_discovery_metric() -> None:
    result_source = (ROOT / "frontend/src/Result.jsx").read_text()
    stylesheet = (ROOT / "frontend/src/index.css").read_text()

    assert "className=\"product-header\"" in result_source
    assert "className=\"result-metrics\"" in result_source
    assert "discovery_percentage: discoveryPercentage" in result_source
    assert "POR QUE ESSA PLAYLIST É JUSTA?" in result_source
    assert ".result-grid" in stylesheet
    assert ".result-representation" in stylesheet
