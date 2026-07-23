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


def _answered_rectification_score() -> dict:
    questionnaire = _handler()._compute_active_rectification_questions(
        {
            "birth_time": "1993-04-17 14:49",
            "uncertainty_minutes": 30,
            "step_minutes": 1,
            "lat": 36.683333,
            "lon": 114.35,
            "tz": 8,
        }
    )
    return _handler()._compute_active_rectification_score(
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


def test_rectification_score_exposes_narayana_cross_score_red() -> None:
    scored = _answered_rectification_score()

    assert scored["candidate_cluster_rankings"]
    assert all(
        "narayana_cross_score" in candidate
        for candidate in scored["candidate_cluster_rankings"]
    )


def test_rectification_technique_audit_mentions_narayana_red() -> None:
    scored = _answered_rectification_score()

    audit_rows = scored["technique_audit_table"]
    assert any(
        row.get("technique") == "Narayana Dasha Rectification"
        and row.get("status") in {"used", "partial"}
        for row in audit_rows
    )


def test_narayana_conflict_downgrades_without_replacing_vimshottari_red() -> None:
    scored = _handler()._compute_active_rectification_score(
        {
            "questionnaire": {
                "questions": [
                    {
                        "id": "career_responsibility_pressure",
                        "round": 1,
                        "scoring_map": {
                            "A": {
                                "cluster": "middle_candidate_cluster",
                                "points": 9,
                            }
                        },
                    }
                ]
            },
            "answers": {"career_responsibility_pressure": "A"},
            "narayana_cross_scores": {
                "early_candidate_cluster": 10,
                "middle_candidate_cluster": -10,
            },
        }
    )

    top = scored["candidate_cluster_rankings"][0]
    assert top["cluster"] == "middle_candidate_cluster"
    assert top["claim_status"] == "candidate"
    assert top["confidence_cap"] == "low"
    assert top["conflict_policy"] == "downgrade_without_replacement"


def test_rectification_claim_remains_candidate_not_birth_time_truth_red() -> None:
    scored = _answered_rectification_score()

    assert scored["claim_status"] == "candidate"
    assert scored["truth_status"] != "birth_time_truth"


def test_rectification_score_exposes_jaimini_karaka_cross_score_red() -> None:
    scored = _answered_rectification_score()

    assert scored["candidate_cluster_rankings"]
    assert all(
        "jaimini_karaka_cross_score" in candidate
        for candidate in scored["candidate_cluster_rankings"]
    )


def test_rectification_technique_audit_mentions_jaimini_karaka_red() -> None:
    scored = _answered_rectification_score()

    audit_rows = scored["technique_audit_table"]
    assert any(
        row.get("technique") == "Jaimini Karaka Rectification"
        and row.get("status") == "partial"
        for row in audit_rows
    )


def test_jaimini_karaka_conflict_downgrades_without_replacing_primary_rank_red() -> None:
    scored = _handler()._compute_active_rectification_score(
        {
            "questionnaire": {
                "questions": [
                    {
                        "id": "career_responsibility_pressure",
                        "round": 1,
                        "scoring_map": {
                            "A": {
                                "cluster": "middle_candidate_cluster",
                                "points": 9,
                            }
                        },
                    }
                ]
            },
            "answers": {"career_responsibility_pressure": "A"},
            "jaimini_karaka_cross_scores": {
                "early_candidate_cluster": 10,
                "middle_candidate_cluster": -10,
            },
        }
    )

    top = scored["candidate_cluster_rankings"][0]
    assert top["cluster"] == "middle_candidate_cluster"
    assert top["claim_status"] == "candidate"
    assert top["confidence_cap"] == "low"
    assert "jaimini_karaka" in top["downgrade_reasons"]


def test_rectification_score_exposes_vimsopaka_avastha_cross_score_red() -> None:
    scored = _answered_rectification_score()

    assert scored["candidate_cluster_rankings"]
    assert all(
        "vimsopaka_avastha_cross_score" in candidate
        for candidate in scored["candidate_cluster_rankings"]
    )


def test_rectification_technique_audit_mentions_vimsopaka_avastha_red() -> None:
    scored = _answered_rectification_score()

    audit_rows = scored["technique_audit_table"]
    assert any(
        row.get("technique") == "Vimsopaka Avastha Rectification"
        and row.get("status") == "partial"
        for row in audit_rows
    )


def test_vimsopaka_avastha_conflict_downgrades_without_replacing_primary_rank_red() -> None:
    scored = _handler()._compute_active_rectification_score(
        {
            "questionnaire": {
                "questions": [
                    {
                        "id": "career_responsibility_pressure",
                        "round": 1,
                        "scoring_map": {
                            "A": {
                                "cluster": "middle_candidate_cluster",
                                "points": 9,
                            }
                        },
                    }
                ]
            },
            "answers": {"career_responsibility_pressure": "A"},
            "vimsopaka_avastha_cross_scores": {
                "early_candidate_cluster": 10,
                "middle_candidate_cluster": -10,
            },
        }
    )

    top = scored["candidate_cluster_rankings"][0]
    assert top["cluster"] == "middle_candidate_cluster"
    assert top["claim_status"] == "candidate"
    assert top["confidence_cap"] == "low"
    assert "vimsopaka_avastha" in top["downgrade_reasons"]


def test_rectification_score_exposes_shadbala_av_observation_score_red() -> None:
    scored = _answered_rectification_score()

    assert scored["candidate_cluster_rankings"]
    assert all(
        "shadbala_av_observation_score" in candidate
        for candidate in scored["candidate_cluster_rankings"]
    )
    assert scored["formula_unit_parity_status"] == "partial"


def test_rectification_technique_audit_mentions_shadbala_av_low_weight_red() -> None:
    scored = _answered_rectification_score()

    audit_rows = scored["technique_audit_table"]
    assert any(
        row.get("technique") == "Shadbala Ashtakavarga Rectification"
        and row.get("status") == "partial_observation"
        and row.get("weight_policy") == "low_weight_only"
        for row in audit_rows
    )


def test_shadbala_av_conflict_downgrades_without_replacing_primary_rank_red() -> None:
    scored = _handler()._compute_active_rectification_score(
        {
            "questionnaire": {
                "questions": [
                    {
                        "id": "career_responsibility_pressure",
                        "round": 1,
                        "scoring_map": {
                            "A": {
                                "cluster": "middle_candidate_cluster",
                                "points": 9,
                            }
                        },
                    }
                ]
            },
            "answers": {"career_responsibility_pressure": "A"},
            "shadbala_av_observation_scores": {
                "early_candidate_cluster": 10,
                "middle_candidate_cluster": -10,
            },
        }
    )

    top = scored["candidate_cluster_rankings"][0]
    assert top["cluster"] == "middle_candidate_cluster"
    assert top["claim_status"] == "candidate"
    assert top["confidence_cap"] == "low"
    assert "shadbala_av" in top["downgrade_reasons"]


def test_rectification_score_exposes_gochara_observation_score_red() -> None:
    scored = _answered_rectification_score()

    assert scored["candidate_cluster_rankings"]
    assert all(
        "gochara_transit_observation_score" in candidate
        for candidate in scored["candidate_cluster_rankings"]
    )
    assert scored["timing_claim_status"] == "exploratory_unvalidated"


def test_rectification_technique_audit_mentions_gochara_holdout_gate_red() -> None:
    scored = _answered_rectification_score()

    audit_rows = scored["technique_audit_table"]
    assert any(
        row.get("technique") == "Gochara Transit Rectification"
        and row.get("status") == "blocked_from_verified_timing"
        and row.get("holdout_gate") == "negative_holdout_required"
        for row in audit_rows
    )


def test_gochara_conflict_downgrades_without_verified_timing_claim_red() -> None:
    scored = _handler()._compute_active_rectification_score(
        {
            "questionnaire": {
                "questions": [
                    {
                        "id": "career_responsibility_pressure",
                        "round": 1,
                        "scoring_map": {
                            "A": {
                                "cluster": "middle_candidate_cluster",
                                "points": 9,
                            }
                        },
                    }
                ]
            },
            "answers": {"career_responsibility_pressure": "A"},
            "gochara_transit_observation_scores": {
                "early_candidate_cluster": 10,
                "middle_candidate_cluster": -10,
            },
        }
    )

    top = scored["candidate_cluster_rankings"][0]
    assert top["cluster"] == "middle_candidate_cluster"
    assert top["claim_status"] == "candidate"
    assert top["confidence_cap"] == "low"
    assert "gochara_transit" in top["downgrade_reasons"]
    assert scored["timing_claim_status"] == "exploratory_unvalidated"


def test_high_rigor_event_rectification_queues_vedastro_packet(monkeypatch) -> None:
    monkeypatch.setattr(
        "scripts.rectification_three_engine_packet._enqueue_vedastro_gateway_job",
        lambda *_args, **_kwargs: {
            "scope": "vedastro_gateway_job_receipt",
            "status": "queued",
            "job_id": "vgw_rectification",
            "poll_path": "/api/vedastro_gateway/jobs/vgw_rectification",
            "raw_response_archive": {
                "status": "pending",
                "official_raw_response_available": False,
            },
            "boundary": "VedAstro raw response remains server-side; this receipt never returns request data or raw evidence.",
        },
    )
    result = _handler()._compute_active_rectification_events(
        {
            "birth_date": "1993-04-17",
            "start_time": "14:29",
            "end_time": "14:31",
            "lat": 36.683333,
            "lon": 114.35,
            "tz": 8,
            "high_rigor": True,
            "events": [
                {
                    "id": "5cb071d6-6d99-46be-85dc-a9bf59ef6ac5",
                    "domain": "education",
                    "date": "2011-09",
                    "precision": "month",
                    "summary": "2011 年 9 月离开家乡开始大学生活",
                },
                {"id": "0790866c-ad5e-4a45-b2b4-a5c73f6be6ea", "domain": "career", "date": "2019-07-01", "precision": "day"},
                {"id": "0ef52e51-ab5f-453b-81e5-adb44a929224", "domain": "relationship", "date": "2021", "precision": "year"},
            ],
        }
    )
    receipt = result["three_engine_packet"]["vedastro"]
    assert receipt["status"] == "queued"
    assert receipt["job_id"] == "vgw_rectification"
    assert "1993" not in str(receipt)
    contract = result["technique_contract"]
    assert result["can_apply"] is False
    assert contract["confirmation_allowed"] is False
    assert contract["decision"] == "continue_rectification"
    assert contract["canonical_input_hash"]
    assert contract["gates"]["public_holdout_release"]["status"] == "blocked"
    assert result["calculation_contract"]["events"][0]["summary"] == "2011 年 9 月离开家乡开始大学生活"
