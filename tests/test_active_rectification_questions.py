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


def test_active_rectification_scores_legacy_questions_missing_scoring_maps() -> None:
    report = build_questionnaire("1955-02-24 19:15", uncertainty_minutes=30)
    legacy_questionnaire = {
        "questions": [
            {
                "id": question["id"],
                "prompt": question["prompt"],
                "options": question["options"],
            }
            for question in report["questions"]
        ]
    }

    scored = score_answers(
        legacy_questionnaire,
        {
            "education_environment_shift": "A",
            "residence_relocation_shift": "A",
            "relationship_or_partner_entry": "B",
        },
    )

    assert scored["answered_count"] == 3
    assert scored["invalid_answers"] == []
    assert scored["candidate_cluster_rankings"]


def test_active_rectification_recasts_candidate_vargas_when_location_is_available() -> None:
    report = build_questionnaire(
        "1993-04-17 14:49",
        uncertainty_minutes=30,
        lat=36.683333,
        lon=114.35,
        tz=8,
    )
    summary = report["candidate_scan"]["sensitivity_summary"]
    assert "true_varga_recast" in summary["computed_layers"]
    assert "true_arudha_recast" in summary["computed_layers"]
    assert "true_kp_cusp_recast" in summary["computed_layers"]
    assert "true_varga_recast" not in summary["blocked_layers"]
    assert "true_kp_cusp_recast" not in summary["blocked_layers"]
    sample = report["candidate_scan"]["samples"][1]
    assert sample["varga_lagna"]["D9_Navamsa"]["sign"]
    assert sample["varga_lagna"]["D10_Dasamsa"]["sign"]
    assert sample["arudha"]["A7"]["sign"]
    assert sample["arudha"]["A10"]["sign"]
    assert sample["arudha"]["UL"]["sign"]
    assert sample["kp_cusps"]["house_7"]["sub_lord"]
    assert sample["kp_cusps"]["house_10"]["sub_sub_lord"]


def test_candidate_recast_contains_all_evidence_domain_vargas(monkeypatch) -> None:
    report = build_questionnaire(
        "1993-04-17 14:30", 30, 30,
        lat=31.2304, lon=121.4737, tz=8,
    )
    sample = report["candidate_scan"]["samples"][0]
    varga_lagna = sample["varga_lagna"]
    expected_legacy_keys = {
        "D4": "D4_Turyamsa",
        "D9": "D9_Navamsa",
        "D10": "D10_Dasamsa",
        "D24": "D24_Siddhamsa",
        "D30": "D30_Trimsamsa",
    }
    assert set(expected_legacy_keys).issubset(varga_lagna)
    for alias, legacy_key in expected_legacy_keys.items():
        assert varga_lagna[alias]["sign"]
        assert varga_lagna[alias] == varga_lagna[legacy_key]
