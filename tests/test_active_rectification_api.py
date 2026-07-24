from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import jyotish_api_server as api_server  # noqa: E402
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


def test_high_rigor_event_rectification_requires_real_vedastro_candidate_discrimination(monkeypatch) -> None:
    original_loader = api_server._load_local_module

    class LocalScorer:
        @staticmethod
        def score_life_events(request):
            return {
                "result_id": "local-result",
                "confidence": "high",
                "can_apply": True,
                "winning_segment": {
                    "start_time": "14:30",
                    "end_time": "14:30",
                    "representative_time": "14:30",
                    "width_minutes": 1,
                },
                "event_count": len(request["events"]),
                "domain_count": len({event["domain"] for event in request["events"]}),
                "top_score": 30,
                "second_score": 20,
                "margin_percent": 33.33,
                "reasons": [],
                "evidence": [],
                "algorithm_version": "fixture",
                "canonical_input_hash": "canonical-fixture",
                "calculation_contract": {"events": request["events"]},
                "stability_diagnostics": {
                    "neighbor_stability": {"all_required_passed": True},
                    "leave_one_event_out": {"status": "pass"},
                },
                "missing_layers": [],
                "candidate_ranking_summary": [
                    {"rank": 1, "time": "14:30", "score": 30, "tied_minute_count": 1},
                    {"rank": 2, "time": "14:31", "score": 20, "tied_minute_count": 1},
                ],
            }

    class VedAstroAdapter:
        @staticmethod
        def run_rectification_minute_snapshot_for_case(case, case_id="user_chart"):
            minute = case["minute"]
            return {
                "available": True,
                "status": "ok",
                "source": "vedastro_official",
                "layers": {
                    "ascendant_house_boundaries": {
                        "status": "ok",
                        "fingerprint": f"asc-{minute}",
                        "ascendant": {"sign": "Leo", "degree_in_sign": minute / 10},
                        "houses": {"House1": {}},
                    },
                    "D9": {
                        "status": "ok",
                        "fingerprint": f"d9-{minute}",
                        "houses": {"House1": {}},
                        "planets": {},
                    },
                    "D10": {
                        "status": "ok",
                        "fingerprint": "d10-same",
                        "houses": {"House1": {}},
                        "planets": {},
                    },
                    "dasha_boundaries": {
                        "status": "ok",
                        "fingerprint": f"dasha-{minute}",
                        "boundary_count": 3,
                    },
                    "kp_cusp_sub_lord": {
                        "status": "unsupported_by_verified_official_interface",
                        "reason": "not supported by verified official interface",
                    },
                },
                "raw_response": {"must_not": "leak"},
            }

        @staticmethod
        def run_range_scan_for_case(case, _domain, _start, _end, case_id="user_chart"):
            return {
                "available": True,
                "status": "ok",
                "event_count": 1,
                "top_event": {"event_id": f"event-{case_id}"},
                "evidence_ledger": [{"signal_lift": 1}],
                "raw_response": {"must_not": "leak"},
            }

    monkeypatch.setattr(
        api_server,
        "_load_local_module",
        lambda name: LocalScorer if name == "active_rectification_events" else VedAstroAdapter if name == "vedastro_service_adapter" else original_loader(name),
    )
    monkeypatch.setattr(
        "scripts.rectification_three_engine_packet.build_packet",
        lambda _case: {
            "engine_status": {"local": "ok", "pyjhora": "ok", "jyotishganit": "ok"},
            "match_count": 3,
            "mismatch_count": 0,
        },
    )
    monkeypatch.setattr(
        JyotishAPIHandler,
        "_compute_vedastro_gateway_run",
        lambda *_args, **_kwargs: {
            "status": "ok",
            "official_closure_state": "official_verified",
            "official_closure_reason": "official_raw_response_present",
            "official_raw_response": {"must_not": "leak"},
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
    assert receipt["status"] == "official_verified"
    contract = result["technique_contract"]
    validation = contract["external_engines"]["validation"]
    assert result["can_apply"] is True
    assert contract["confirmation_allowed"] is True
    assert contract["decision"] == "confirm_minute"
    assert contract["canonical_input_hash"]
    assert contract["gates"]["vedastro_minute_sensitive_validation"]["status"] == "pass"
    assert validation["minute_sensitive_validation"]["discriminated"] is True
    assert validation["minute_sensitive_validation"]["discriminated_layers"]
    assert validation["event_background_validation"]["used_for_decision"] is False
    assert validation["event_background_validation"]["candidates"][0]["metric"] == validation["event_background_validation"]["candidates"][1]["metric"]
    assert "must_not" not in str(validation)
    assert result["calculation_contract"]["events"][0]["summary"] == "2011 年 9 月离开家乡开始大学生活"


def test_long_real_conversation_reaches_vedastro_after_local_range_is_narrow(monkeypatch) -> None:
    original_loader = api_server._load_local_module
    vedastro_calls: list[tuple[str, str, str, str]] = []

    class VedAstroAdapter:
        @staticmethod
        def run_rectification_minute_snapshot_for_case(case, case_id="user_chart"):
            candidate_time = f'{case["hour"]:02d}:{case["minute"]:02d}'
            return {
                "available": True,
                "status": "ok",
                "source": "vedastro_official",
                "layers": {
                    "ascendant_house_boundaries": {
                        "status": "ok",
                        "fingerprint": f"asc-{candidate_time}",
                        "ascendant": {"sign": "Leo", "degree_in_sign": case["minute"] / 10},
                        "houses": {"House1": {}},
                    },
                    "D9": {
                        "status": "ok",
                        "fingerprint": f"d9-{candidate_time}",
                        "houses": {"House1": {}},
                        "planets": {},
                    },
                    "D10": {
                        "status": "ok",
                        "fingerprint": f"d10-{candidate_time}",
                        "houses": {"House1": {}},
                        "planets": {},
                    },
                    "dasha_boundaries": {
                        "status": "ok",
                        "fingerprint": f"dasha-{candidate_time}",
                        "boundary_count": 3,
                    },
                    "kp_cusp_sub_lord": {
                        "status": "unsupported_by_verified_official_interface",
                        "reason": "not supported by verified official interface",
                    },
                },
            }

        @staticmethod
        def run_range_scan_for_case(case, domain, start, end, case_id="user_chart"):
            candidate_time = f'{case["hour"]:02d}:{case["minute"]:02d}'
            vedastro_calls.append((candidate_time, domain, start, end))
            return {
                "available": True,
                "status": "ok",
                "event_count": 1,
                "top_event": {"event_id": f"event-{case_id}"},
                "evidence_ledger": [{"signal_lift": 1}],
            }

    monkeypatch.setattr(
        api_server,
        "_load_local_module",
        lambda name: VedAstroAdapter if name == "vedastro_service_adapter" else original_loader(name),
    )
    monkeypatch.setattr(
        "scripts.rectification_three_engine_packet.build_packet",
        lambda _case: {
            "engine_status": {"local": "ok", "pyjhora": "ok", "jyotishganit": "ok"},
            "match_count": 3,
            "mismatch_count": 0,
        },
    )
    monkeypatch.setattr(
        JyotishAPIHandler,
        "_compute_vedastro_gateway_run",
        lambda *_args, **_kwargs: {
            "status": "ok",
            "official_closure_state": "official_verified",
            "official_closure_reason": "official_raw_response_present",
            "official_raw_response": {"status": "ok"},
        },
    )

    result = _handler()._compute_active_rectification_events(
        {
            "birth_date": "1997-08-08",
            "start_time": "04:00",
            "end_time": "07:59",
            "lat": 36.420487,
            "lon": 114.209936,
            "tz": 8,
            "high_rigor": True,
            "events": [
                {"id": "00000000-0000-4000-8000-000000000001", "domain": "education", "date": "2016-09", "precision": "month", "summary": "离家去外地上大学"},
                {"id": "00000000-0000-4000-8000-000000000002", "domain": "career", "date": "2020-04", "precision": "month", "summary": "去石油化工研究院实习做研究员"},
                {"id": "00000000-0000-4000-8000-000000000003", "domain": "career", "date": "2020-10", "precision": "month", "summary": "从研究院辞职"},
                {"id": "00000000-0000-4000-8000-000000000004", "domain": "education", "date": "2020-12", "precision": "month", "summary": "参加研究生考试结果不理想"},
                {"id": "00000000-0000-4000-8000-000000000005", "domain": "relocation", "date": "2021-01", "precision": "month", "summary": "回家备考并长期在家"},
                {"id": "00000000-0000-4000-8000-000000000006", "domain": "education", "date": "2022-12", "precision": "month", "summary": "考研结束后转向自学前端"},
                {"id": "00000000-0000-4000-8000-000000000007", "domain": "career", "date": "2023-04", "precision": "month", "summary": "去北京入职医疗器械公司"},
                {"id": "00000000-0000-4000-8000-000000000008", "domain": "relationship", "date": "2024-08-08", "precision": "day", "summary": "恋爱关系发生重大转折"},
                {"id": "00000000-0000-4000-8000-000000000009", "domain": "relationship", "date": "2024-10", "precision": "month", "summary": "短暂复联后主动断联"},
                {"id": "00000000-0000-4000-8000-000000000010", "domain": "finance", "date": "2026-01", "precision": "month", "summary": "公司无法正常发放工资"},
                {"id": "00000000-0000-4000-8000-000000000011", "domain": "career", "date": "2026-07-10", "precision": "day", "summary": "与朋友正式决定创业"},
                {"id": "00000000-0000-4000-8000-000000000012", "domain": "career", "date": "2026-07-21", "precision": "day", "summary": "提交公司注册材料"},
            ],
        }
    )

    assert result["winning_segment"] == {
        "start_time": "05:07",
        "end_time": "05:08",
        "representative_time": "05:07",
        "width_minutes": 2,
    }
    assert result["stability_diagnostics"]["neighbor_stability"]["all_required_passed"] is False
    assert result["stability_diagnostics"]["leave_one_event_out"]["status"] != "pass"
    assert len(vedastro_calls) == 6
    assert {call[0] for call in vedastro_calls} == {"05:07", "05:21"}
    assert {call[1] for call in vedastro_calls} == {"career", "wealth", "marriage"}
    assert all(start == end for _, _, start, end in vedastro_calls)
    assert {
        (domain, start)
        for candidate, domain, start, _ in vedastro_calls
        if candidate == "05:07"
    } == {
        ("career", "2026-07-21"),
        ("wealth", "2026-01-16"),
        ("marriage", "2024-08-08"),
    }
    assert {
        candidate
        for candidate, _, _, _ in vedastro_calls
    } == {
        item["time"]
        for item in result["candidate_ranking_summary"][:2]
    }
    validation = result["technique_contract"]["external_engines"]["validation"]
    event_validation = validation["event_background_validation"]
    assert event_validation["eligible_event_count"] == 12
    assert event_validation["supported_event_count"] == 3
    assert event_validation["used_for_decision"] is False
    assert event_validation["candidates"][0]["metric"] == event_validation["candidates"][1]["metric"]
    assert "one_strongest_event_per_native_adapter_domain" in event_validation["selection_policy"]
    assert result["three_engine_packet"]["vedastro"]["status"] == "official_verified"
    assert result["three_engine_packet"]["vedastro"]["search_events_role"] == "background_only"
    assert result["technique_contract"]["gates"]["vedastro_minute_sensitive_validation"]["status"] == "pass"
    assert validation["minute_sensitive_validation"]["discriminated"] is True
    assert result["technique_contract"]["confirmation_allowed"] is True
    assert result["technique_contract"]["decision"] == "confirm_minute"
    assert result["can_apply"] is True
    assert "neighbor_stability_not_passed" not in result["technique_contract"]["hard_blockers"]
    assert "leave_one_event_out_not_passed" not in result["technique_contract"]["hard_blockers"]


def test_identical_vedastro_minute_sensitive_snapshots_do_not_discriminate_candidates() -> None:
    layers = {
        name: {"status": "ok", "fingerprint": f"same-{name}"}
        for name in api_server._VEDASTRO_MINUTE_SENSITIVE_LAYERS
    }
    snapshots = [
        {"candidate_time": "05:07", "available": True, "layers": layers},
        {"candidate_time": "05:21", "available": True, "layers": layers},
    ]

    comparison = api_server._compare_vedastro_minute_snapshots(snapshots)

    assert comparison["comparison_ready"] is True
    assert comparison["discriminated"] is False
    assert comparison["discriminated_layers"] == []
    assert all(item["status"] == "same" for item in comparison["differences"].values())


def test_search_events_difference_cannot_override_identical_minute_snapshots(monkeypatch) -> None:
    original_loader = api_server._load_local_module

    class LocalScorer:
        @staticmethod
        def score_life_events(request):
            return {
                "result_id": "local-result",
                "confidence": "high",
                "can_apply": True,
                "winning_segment": {
                    "start_time": "14:30",
                    "end_time": "14:30",
                    "representative_time": "14:30",
                    "width_minutes": 1,
                },
                "event_count": len(request["events"]),
                "domain_count": len({event["domain"] for event in request["events"]}),
                "top_score": 30,
                "second_score": 20,
                "margin_percent": 33.33,
                "reasons": [],
                "evidence": [],
                "algorithm_version": "fixture",
                "canonical_input_hash": "canonical-fixture",
                "calculation_contract": {"events": request["events"]},
                "stability_diagnostics": {
                    "neighbor_stability": {"all_required_passed": True},
                    "leave_one_event_out": {"status": "pass"},
                },
                "missing_layers": [],
                "candidate_ranking_summary": [
                    {"rank": 1, "time": "14:30", "score": 30, "tied_minute_count": 1},
                    {"rank": 2, "time": "14:31", "score": 20, "tied_minute_count": 1},
                ],
            }

    class VedAstroAdapter:
        @staticmethod
        def run_rectification_minute_snapshot_for_case(_case, case_id="user_chart"):
            layers = {
                name: {
                    "status": "ok",
                    "fingerprint": f"same-{name}",
                    "houses": {"House1": {}},
                    "planets": {},
                    "boundary_count": 3,
                }
                for name in api_server._VEDASTRO_MINUTE_SENSITIVE_LAYERS
            }
            layers["ascendant_house_boundaries"]["ascendant"] = {
                "sign": "Leo",
                "degree_in_sign": 12.5,
            }
            layers["kp_cusp_sub_lord"] = {
                "status": "unsupported_by_verified_official_interface",
                "reason": "not supported by verified official interface",
            }
            return {
                "available": True,
                "status": "ok",
                "source": "vedastro_official",
                "layers": layers,
            }

        @staticmethod
        def run_range_scan_for_case(case, _domain, _start, _end, case_id="user_chart"):
            event_count = 10 if case["minute"] == 30 else 1
            return {
                "available": True,
                "status": "ok",
                "event_count": event_count,
                "top_event": {"event_id": f"event-{case_id}"},
                "evidence_ledger": [{"signal_lift": event_count}],
            }

    monkeypatch.setattr(
        api_server,
        "_load_local_module",
        lambda name: LocalScorer if name == "active_rectification_events" else VedAstroAdapter if name == "vedastro_service_adapter" else original_loader(name),
    )
    monkeypatch.setattr(
        "scripts.rectification_three_engine_packet.build_packet",
        lambda _case: {
            "engine_status": {"local": "ok", "pyjhora": "ok", "jyotishganit": "ok"},
            "match_count": 3,
            "mismatch_count": 0,
        },
    )
    monkeypatch.setattr(
        JyotishAPIHandler,
        "_compute_vedastro_gateway_run",
        lambda *_args, **_kwargs: {
            "status": "ok",
            "official_closure_state": "official_verified",
            "official_closure_reason": "official_raw_response_present",
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
                {"id": "5cb071d6-6d99-46be-85dc-a9bf59ef6ac5", "domain": "education", "date": "2011-09", "precision": "month"},
                {"id": "0790866c-ad5e-4a45-b2b4-a5c73f6be6ea", "domain": "career", "date": "2019-07-01", "precision": "day"},
                {"id": "0ef52e51-ab5f-453b-81e5-adb44a929224", "domain": "relationship", "date": "2021", "precision": "year"},
            ],
        }
    )

    validation = result["technique_contract"]["external_engines"]["validation"]
    background_candidates = validation["event_background_validation"]["candidates"]
    assert background_candidates[0]["metric"] != background_candidates[1]["metric"]
    assert validation["event_background_validation"]["used_for_decision"] is False
    assert validation["minute_sensitive_validation"]["discriminated"] is False
    assert result["can_apply"] is False
    assert result["technique_contract"]["confirmation_allowed"] is False
    assert "vedastro_minute_sensitive_layers_not_discriminated" in result["reasons"]
    assert "vedastro_candidate_not_discriminated" not in result["reasons"]
