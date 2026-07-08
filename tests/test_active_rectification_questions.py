from __future__ import annotations

from scripts.active_rectification_questions import build_questionnaire


def test_active_rectification_questions_generate_choice_based_workflow() -> None:
    report = build_questionnaire("1955-02-24 19:15", uncertainty_minutes=30)

    assert report["scope"] == "active_birth_time_rectification_questionnaire"
    assert report["candidate_scan"]["start"] == "1955-02-24 18:45"
    assert report["candidate_scan"]["end"] == "1955-02-24 19:45"
    assert report["candidate_scan"]["candidate_count"] == 61
    assert "high_information_question_generation" in report["workflow"]
    assert {"D9", "D10", "D24", "D30", "UL", "A10", "KP_cusp"} <= set(report["sensitivity_layers"])
    assert len(report["questions"]) >= 8
    assert {q["round"] for q in report["questions"]} == {1, 2, 3}
    assert all({option["key"] for option in q["options"]} == {"A", "B", "C", "D"} for q in report["questions"])
    assert all("scoring_map" in q for q in report["questions"])
