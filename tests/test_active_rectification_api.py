from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from jyotish_api_server import BadRequest, JyotishAPIHandler  # noqa: E402


def _handler() -> JyotishAPIHandler:
    return JyotishAPIHandler.__new__(JyotishAPIHandler)


def test_active_rectification_questions_api_builds_choice_workflow() -> None:
    result = _handler()._compute_active_rectification_questions(
        {
            "birth_time": "1993-04-17 14:49",
            "uncertainty_minutes": 30,
            "step_minutes": 1,
        }
    )

    assert result["success"] is True
    assert result["endpoint"] == "active_rectification_questions"
    assert result["scope"] == "active_birth_time_rectification_questionnaire"
    assert result["candidate_scan"]["start"] == "1993-04-17 14:19"
    assert result["candidate_scan"]["end"] == "1993-04-17 15:19"
    assert result["candidate_scan"]["candidate_count"] == 61
    assert result["questions"]
    assert {option["key"] for option in result["questions"][0]["options"]} == {"A", "B", "C", "D"}
    assert "dynamic_candidate_cluster_scoring" in result["workflow"]


def test_active_rectification_score_api_returns_rankings_and_next_questions() -> None:
    questionnaire = _handler()._compute_active_rectification_questions(
        {"birth_time": "1993-04-17 14:49", "uncertainty_minutes": 30}
    )
    scored = _handler()._compute_active_rectification_score(
        {
            "questionnaire": questionnaire,
            "answers": {
                "education_environment_shift": "A",
                "residence_relocation_shift": "B",
                "relationship_or_partner_entry": "D",
                "career_responsibility_pressure": "A",
                "research_tool_expression_shift": "C",
            },
        }
    )

    assert scored["success"] is True
    assert scored["endpoint"] == "active_rectification_score"
    assert scored["scope"] == "active_birth_time_rectification_scoring"
    assert scored["answered_count"] == 5
    assert scored["candidate_cluster_rankings"]
    assert scored["next_round_questions"]
    assert scored["candidate_cluster_rankings"][0]["score"] >= scored["candidate_cluster_rankings"][-1]["score"]


def test_active_rectification_questions_api_validates_request() -> None:
    with pytest.raises(BadRequest, match="birth_time must be a string"):
        _handler()._compute_active_rectification_questions({})

    with pytest.raises(BadRequest, match="uncertainty_minutes must be between 1 and 180"):
        _handler()._compute_active_rectification_questions(
            {"birth_time": "1993-04-17 14:49", "uncertainty_minutes": 0}
        )

    with pytest.raises(BadRequest, match="step_minutes must be between 1 and 30"):
        _handler()._compute_active_rectification_questions(
            {"birth_time": "1993-04-17 14:49", "step_minutes": 31}
        )


def test_active_rectification_score_api_validates_payload() -> None:
    with pytest.raises(BadRequest, match="questionnaire must be an object"):
        _handler()._compute_active_rectification_score({"answers": {}})

    with pytest.raises(BadRequest, match="answers must be an object"):
        _handler()._compute_active_rectification_score({"questionnaire": {}})
