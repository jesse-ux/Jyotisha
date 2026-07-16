from __future__ import annotations

from scripts.active_rectification_questions import build_questionnaire, score_answers


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
    assert report["candidate_scan"]["samples"]
    assert report["candidate_scan"]["sensitivity_summary"]
    assert {"D9", "D10", "D24", "D30", "UL", "A10", "KP_cusp"} <= set(
        report["candidate_scan"]["sensitivity_summary"]["high_value_layers"]
    )
    assert report["candidate_scan"]["samples"][0]["cluster"] == "early_candidate_cluster"
    assert report["candidate_scan"]["samples"][-1]["cluster"] == "late_candidate_cluster"


def test_active_rectification_scores_answers_and_selects_next_round() -> None:
    report = build_questionnaire("1955-02-24 19:15", uncertainty_minutes=30)
    scored = score_answers(
        report,
        {
            "education_environment_shift": "A",
            "residence_relocation_shift": "B",
            "relationship_or_partner_entry": "D",
            "career_responsibility_pressure": "A",
            "research_tool_expression_shift": "C",
        },
    )

    assert scored["scope"] == "active_birth_time_rectification_scoring"
    assert scored["answered_count"] == 5
    assert scored["next_round"] == 2
    assert scored["next_round_questions"]
    assert scored["candidate_cluster_rankings"][0]["score"] > scored["candidate_cluster_rankings"][-1]["score"]
    assert "final rectification requires scoring answers against actual candidate chart differences" in scored["boundary"]
