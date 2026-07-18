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


def test_active_rectification_questions_api_accepts_location_for_true_recast() -> None:
    result = _handler()._compute_active_rectification_questions(
        {
            "birth_time": "1993-04-17 14:49",
            "uncertainty_minutes": 30,
            "lat": 36.683333,
            "lon": 114.35,
            "tz": 8,
        }
    )

    summary = result["candidate_scan"]["sensitivity_summary"]
    assert "true_varga_recast" in summary["computed_layers"]
    assert "true_arudha_recast" in summary["computed_layers"]
    assert "true_kp_cusp_recast" in summary["computed_layers"]
    assert "true_varga_recast" not in summary["blocked_layers"]
    assert "true_kp_cusp_recast" not in summary["blocked_layers"]


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


def test_active_rectification_events_api_scores_structured_events() -> None:
    result = _handler()._compute_active_rectification_events({
        "birth_date": "1993-04-17",
        "start_time": "14:29",
        "end_time": "14:31",
        "lat": 36.683333,
        "lon": 114.35,
        "tz": 8,
        "events": [
            {"id": "5cb071d6-6d99-46be-85dc-a9bf59ef6ac5", "domain": "education", "date": "2011-09", "precision": "month"},
            {"id": "0790866c-ad5e-4a45-b2b4-a5c73f6be6ea", "domain": "career", "date": "2019-07-01", "precision": "day"},
            {"id": "0ef52e51-ab5f-453b-81e5-adb44a929224", "domain": "relationship", "date": "2021", "precision": "year"},
        ],
    })

    assert result["success"] is True
    assert result["endpoint"] == "active_rectification_events"
    assert result["result_id"]
    assert result["event_count"] == 3


def test_active_rectification_events_api_rejects_client_scores() -> None:
    with pytest.raises(BadRequest, match="unsupported active rectification event field"):
        _handler()._compute_active_rectification_events({
            "birth_date": "1993-04-17",
            "start_time": "14:29",
            "end_time": "14:31",
            "lat": 36.683333,
            "lon": 114.35,
            "tz": 8,
            "events": [],
            "confidence": "high",
        })
