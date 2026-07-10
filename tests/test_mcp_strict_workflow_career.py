#!/usr/bin/env python3
"""Regression tests for MCP career event adjudication."""

from __future__ import annotations

import jyotish_engine
import mcp_server

from mcp_server import _collect_strict_evidence, _existing_interpretation_source_pack

SOURCE_LAYER_CONTEXT = {
    "dasha_timing_layer_used",
    "varga_strength_layer_used",
    "annual_special_layer_context",
    "modifier_obstacle_layer_used",
}


def _assert_context_contains(context: list[str], expected: set[str]) -> None:
    assert expected <= set(context)
    assert SOURCE_LAYER_CONTEXT <= set(context)


def _base_career_result() -> dict:
    return {
        "modules": {
            "chart": {
                "ascendant": {"sign": "Leo"},
                "planets": {
                    "Moon": {"status": "中性(Neutral)"},
                    "Venus": {"status": "中性(Neutral)"},
                    "Saturn": {"status": "中性(Neutral)"},
                    "Sun": {"status": "中性(Neutral)"},
                },
            },
            "varga_full": {"D10_Dasamsa": {"summary": "career varga present"}},
            "special_lagnas": {"A10_Karma_Pada": {"sign": "Capricorn", "lord": "Saturn"}},
            "jaimini": {
                "karakas": {
                    "Amatyakaraka": {"planet": "Mercury"},
                    "Atmakaraka": {"planet": "Sun"},
                },
                "karakamsha": {"karakamsha_sign": "Leo", "karakamsha_lord": "Sun"},
            },
            "dasha": {"current_dasha": {"mahadasha": "Mercury", "antardasha": "Sun"}},
            "narayana_dasha": {"current_dasha": {"sign": "Capricorn", "lord": "Saturn"}},
            "dasa_convergence": {
                "domain_activations": {
                    "career_status": {"convergence_level": "L2", "probability": "35-50%"}
                }
            },
            "argala": {
                "houses": {
                    "house_10": {
                        "net_result": "supported",
                        "argala_count": 2,
                        "virodhargala_count": 0,
                    }
                }
            },
        }
    }


def test_career_collects_a10_amk_karakamsha_as_strict_evidence() -> None:
    strict = _collect_strict_evidence("career", _base_career_result())

    assert strict["question_type"] == "career"
    assert strict["present_evidence"]["d10_dasamsa"] == {"summary": "career varga present"}
    assert strict["present_evidence"]["a10_karma_pada"] == {"sign": "Capricorn", "lord": "Saturn"}
    assert strict["present_evidence"]["amatyakaraka"] == {"planet": "Mercury"}
    assert strict["present_evidence"]["karakamsha"] == {
        "karakamsha_sign": "Leo",
        "karakamsha_lord": "Sun",
    }
    assert strict["event_judgement"]["event_family"] == "career"
    assert strict["event_judgement"]["dominant_label"] == "career_status"
    _assert_context_contains(
        strict["event_judgement"]["secondary_context"],
        {
            "a10_active",
            "amk_active",
            "karakamsha_context",
            "functional_benefic_malefic_used",
            "argala_support",
            "vedastro_range_scan_missing",
        },
    )


def test_career_strict_contract_attaches_existing_interpretation_source_pack() -> None:
    strict = _collect_strict_evidence("career", _base_career_result())

    source_pack = strict["present_evidence"]["interpretation_source_pack"]
    assert source_pack["status"] == "used"
    assert "references/interpretation_template_registry.json" in source_pack["source_refs"]
    assert "references/open_source_sources/vedic-astro-skills/codex/skills/vedic-core/resources/p1_p12.md" in source_pack["source_refs"]
    assert "references/open_source_sources/vedic-astro-skills/codex/skills/vedic-core/resources/house_framework.md" in source_pack["source_refs"]
    assert "references/raman-house-judgment-methodology.md" in source_pack["source_refs"]
    assert "jyotish-app/planet-house-details-a.js" in source_pack["source_refs"]
    assert source_pack["template_registry"]["template_count"] >= 11
    assert source_pack["frontend_planet_house_details"]["planet_count"] == 9
    assert source_pack["frontend_planet_house_details"]["house_count"] == 12
    assert source_pack["interpretation_source_inventory"]["status"] == "used"
    assert source_pack["frontend_interpretation_layer"]["status"] == "available"
    assert source_pack["frontend_interpretation_layer"]["source_refs"] == [
        "jyotish-app/interpretation.js",
        "jyotish-app/analysis-deep.js",
    ]
    assert source_pack["yoga_rule_layer"]["status"] == "available"
    assert "references/yoga_rules.json" in source_pack["yoga_rule_layer"]["source_refs"]
    assert source_pack["reader_validation_layer"]["status"] == "available"
    assert "references/open_source_sources/vedic-astro-skills/codex/skills/vedic-reader/resources/validation_rules.md" in source_pack["reader_validation_layer"]["source_refs"]

    audit = strict["technique_audit_summary"]
    assert audit["interpretation_source_pack"]["used"] is True
    assert audit["mevg_global_web_evidence"]["status"] == "blocked"
    assert audit["real_case_calibration"]["status"] == "blocked"


def test_interpretation_source_inventory_classifies_sources_without_promoting_drafts() -> None:
    source_pack = _existing_interpretation_source_pack()
    inventory = source_pack["interpretation_source_inventory"]

    assert inventory["status"] == "used"
    assert inventory["summary"]["primary_truth_count"] >= 4
    assert inventory["summary"]["reference_layer_count"] >= 4
    assert inventory["summary"]["quarantined_draft_count"] >= 1
    assert "jyotish-app/interpretation.js" in inventory["layers"]["frontend_interpretation"]["source_refs"]
    assert "references/open_source_sources/vedic-astro-skills/codex/skills/vedic-core/resources/qa_rules.md" in inventory["layers"]["qa_governance"]["source_refs"]
    assert "references/open_source_sources/vedic-astro-skills/codex/skills/vedic-reader/resources/validation_rules.md" in inventory["layers"]["reader_validation"]["source_refs"]
    assert "references/yoga_rules.json" in inventory["layers"]["yoga_rules"]["source_refs"]

    draft_refs = inventory["layers"]["quarantined_drafts"]["source_refs"]
    assert any("docs/research/local_drafts/" in path for path in draft_refs)
    assert all(path not in source_pack["source_refs"] for path in draft_refs)


def test_mcp_strict_workflow_returns_runtime_evidence_log(monkeypatch) -> None:
    def fake_execute(**kwargs):
        return {
            "chart": {
                "modules": {},
                "ai_prompt_pack": {
                    "evidence_snapshot": {
                        "vedastro_official_snapshot": {
                            "status": "ok",
                            "official_primary_evidence": {"chart_core": {"status": "ok"}},
                        }
                    }
                },
            },
            "routing": {"question_type": "career", "primary_theme": "career"},
            "entry_mode": "direct_chart",
            "runtime_planner": {"executed_steps": ["compute_chart"], "skipped_steps": []},
        }

    monkeypatch.setattr(mcp_server, "_execute_mcp_consultation_workflow", fake_execute)
    monkeypatch.setattr(mcp_server, "_maybe_attach_vedastro_evidence", lambda route, chart, **kwargs: chart)
    monkeypatch.setattr(mcp_server, "_collect_strict_evidence", lambda route, chart: {"question_type": route})

    result = mcp_server.strict_workflow(
        question="career timing",
        year=1955,
        month=2,
        day=24,
        hour=19,
        minute=15,
        lat=37.7749,
        lon=-122.4194,
        tz=8,
        age=33,
        transit_date="2026-07-05",
    )

    assert result["runtime_evidence_log"]["surface"] == "skill_mcp"
    assert result["runtime_evidence_log"]["route"]["question_type"] == "career"
    assert result["runtime_evidence_log"]["vedastro_cloud_state"] == "official_verified"
    assert result["machine_evidence_packet"]["status"] == "partial"
    assert "vedastro_official_raw_archive_manifest" in result["machine_evidence_packet"]["sections"]
    assert result["real_case_calibration"]["status"] == "partial_scored"
    assert result["runtime_evidence_log"]["evidence_packet_contract"]["status"] == "partial"
    assert result["runtime_evidence_log"]["real_case_calibration"]["status"] == "partial_scored"
    assert result["runtime_evidence_log"]["quality_gate"]["technique_audit_table_required"] is True
    assert result["runtime_evidence_log"]["quality_gate"]["technique_audit_table"][0]["technique"] == "VedAstro Cloud State"
    assert result["runtime_evidence_log"]["quality_gate"]["technique_audit_table"][1]["technique"] == "VedAstro Raw Archive Manifest"


def test_mcp_strict_workflow_preserves_western_evidence_packet(monkeypatch) -> None:
    seen = {}

    def fake_execute(**kwargs):
        seen.update(kwargs)
        return {
            "chart": {
                "modules": {},
                "cross_system_signals": [
                    {
                        "theme": "career_relocation",
                        "claim": "career_triggered_relocation",
                        "timing": "2026-07",
                        "source": "jyotish_runtime_signal",
                    }
                ],
                "ai_prompt_pack": {
                    "evidence_snapshot": {
                        "vedastro_official_snapshot": {
                            "status": "ok",
                            "official_primary_evidence": {"chart_core": {"status": "ok"}},
                        }
                    }
                },
            },
            "routing": {"question_type": "career", "primary_theme": "career"},
            "entry_mode": "direct_chart",
            "runtime_planner": {"executed_steps": ["compute_chart"], "skipped_steps": []},
            "western_evidence_packet": kwargs["western_evidence_packet"],
        }

    western_packet = {
        "system": "western_astrology",
        "status": "complete",
        "signals": [
            {
                "theme": "career_relocation",
                "claim": "career_triggered_relocation",
                "timing": "2026-07",
                "source": "western_oracle_signal",
            }
        ],
    }

    monkeypatch.setattr(mcp_server, "_execute_mcp_consultation_workflow", fake_execute)
    monkeypatch.setattr(mcp_server, "_maybe_attach_vedastro_evidence", lambda route, chart, **kwargs: chart)
    monkeypatch.setattr(mcp_server, "_collect_strict_evidence", lambda route, chart: {"question_type": route})

    result = mcp_server.strict_workflow(
        question="career relocation timing",
        year=1955,
        month=2,
        day=24,
        hour=19,
        minute=15,
        lat=37.7749,
        lon=-122.4194,
        tz=8,
        age=33,
        transit_date="2026-07-05",
        western_evidence_packet=western_packet,
    )

    assert seen["western_evidence_packet"] == western_packet
    assert result["runtime_evidence_log"]["cross_system_arbitration"]["status"] == "used"
    assert result["runtime_evidence_log"]["cross_system_arbitration"]["shared_signals"][0]["claim"] == "career_triggered_relocation"


def test_career_blocks_label_when_d10_is_missing_but_preserves_jaimini_context() -> None:
    result = _base_career_result()
    del result["modules"]["varga_full"]["D10_Dasamsa"]

    strict = _collect_strict_evidence("career", result)

    assert "d10_dasamsa" in strict["missing_evidence"]
    assert strict["blocked"] is True
    assert strict["event_judgement"]["dominant_label"] is None
    _assert_context_contains(
        strict["event_judgement"]["secondary_context"],
        {
            "a10_active",
            "amk_active",
            "karakamsha_context",
            "functional_benefic_malefic_used",
            "argala_support",
            "vedastro_range_scan_missing",
        },
    )


def test_career_dignity_guardrail_uses_career_relevant_planets_only() -> None:
    result = _base_career_result()
    result["modules"]["chart"] = {
        "ascendant": {"sign": "Leo"},
        "planets": {
            "Venus": {"status": "落陷取消(Neecha Bhanga)"},
            "Saturn": {"status": "中性(Neutral)"},
            "Moon": {"status": "中性(Neutral)"},
            "Mars": {"status": "极敌(Great Enemy)"},
        },
    }

    strict = _collect_strict_evidence("career", result)

    assert strict["present_evidence"]["dignity_guardrail"]["status"] == "caution"
    assert strict["present_evidence"]["dignity_guardrail"]["score_delta"] == 5
    assert "dignity_supportive_recovery" in strict["event_judgement"]["secondary_context"]
    assert "dignity_high_friction" not in strict["event_judgement"]["secondary_context"]


def test_career_dignity_guardrail_detects_conflict_across_career_significators() -> None:
    result = _base_career_result()
    result["modules"]["chart"] = {
        "ascendant": {"sign": "Leo"},
        "planets": {
            "Venus": {"status": "落陷取消(Neecha Bhanga)"},
            "Saturn": {"status": "极敌(Great Enemy)"},
            "Moon": {"status": "中性(Neutral)"},
        },
    }

    strict = _collect_strict_evidence("career", result)

    assert strict["present_evidence"]["dignity_guardrail"]["status"] == "conflict"
    assert strict["present_evidence"]["dignity_guardrail"]["score_delta"] == 0
    assert "dignity_conflict" in strict["event_judgement"]["secondary_context"]


def test_career_argala_bridge_uses_tenth_house_as_modifier_only() -> None:
    result = _base_career_result()

    strict = _collect_strict_evidence("career", result)

    assert strict["present_evidence"]["argala_support"] == {
        "level": "supportive",
        "target_house": 10,
        "source": "argala_house_bridge_v1",
        "signals": ["argala_support"],
        "raw": {
            "net_result": "supported",
            "argala_count": 2,
            "virodhargala_count": 0,
        },
    }
    assert strict["event_judgement"]["dominant_label"] == "career_status"
    assert "argala_support" in strict["event_judgement"]["secondary_context"]


def test_career_kakshya_support_adds_small_score_bump_without_label_override() -> None:
    base_result = _base_career_result()
    base_result["modules"]["dasa_convergence"]["domain_activations"]["career_status"] = {
        "convergence_level": "L1",
        "probability": "+15-20%",
    }
    base = _collect_strict_evidence("career", base_result)
    result = _base_career_result()
    result["modules"]["dasa_convergence"]["domain_activations"]["career_status"] = {
        "convergence_level": "L1",
        "probability": "+15-20%",
    }
    result["modules"]["kakshya"] = {
        "summary": {"average_strength": 6.7},
        "planets": {"Sun": {"kakshya_strength": 7.0}},
    }

    strict = _collect_strict_evidence("career", result)

    assert strict["present_evidence"]["kakshya_career_support"] == {
        "level": "supportive",
        "source": "kakshya_career_bridge_v1",
        "signals": ["kakshya_career_support"],
        "average_strength": 6.7,
    }
    assert strict["event_judgement"]["dominant_label"] == "career_status"
    assert strict["event_judgement"]["score"] >= base["event_judgement"]["score"]
    assert "kakshya_career_support" in strict["event_judgement"]["secondary_context"]


def test_career_caps_confidence_when_provided_shadbala_components_are_incomplete() -> None:
    result = _base_career_result()
    result["modules"]["dasa_convergence"]["domain_activations"]["career_status"] = {
        "convergence_level": "L4",
        "probability": "70-85%",
    }
    result["modules"]["shadbala"] = {"planets": {"Mercury": {"total_rupa": 7.5}}}

    strict = _collect_strict_evidence("career", result)

    assert strict["present_evidence"]["shadbala_component_audit"] == {
        "status": "incomplete",
        "source": "shadbala.planets",
        "required_components": ["sthana", "dig", "kala", "chesta", "naisargika", "drik"],
        "missing": {"Mercury": ["sthana", "dig", "kala", "chesta", "naisargika", "drik"]},
    }
    assert strict["confidence_cap"] == "low"
    assert "shadbala_component_gap" in strict["event_judgement"]["secondary_context"]


def test_career_accepts_complete_shadbala_components_without_cap_penalty() -> None:
    result = _base_career_result()
    result["modules"]["dasa_convergence"]["domain_activations"]["career_status"] = {
        "convergence_level": "L4",
        "probability": "70-85%",
    }
    result["modules"]["shadbala"] = {
        "planets": {
            "Mercury": {
                "components": {
                    "sthana": 1.0,
                    "dig": 0.8,
                    "kala": 1.2,
                    "chesta": 0.7,
                    "naisargika": 0.5,
                    "drik": 0.3,
                },
                "total_rupa": 4.5,
            }
        }
    }

    strict = _collect_strict_evidence("career", result)

    assert strict["present_evidence"]["shadbala_component_audit"]["status"] == "complete"
    assert strict["confidence_cap"] == "medium-high"
    assert "shadbala_component_gap" not in strict["event_judgement"]["secondary_context"]


def test_career_strict_contract_marks_a10_as_local_supplement_to_official_primary() -> None:
    result = _base_career_result()
    result["modules"]["source_priority"] = {"mode": "vedastro_official_primary"}
    result["modules"]["vedastro_official_full_snapshot"] = {
        "status": "partial",
        "available": True,
        "official_chart": {"planets": {"Sun": {}}, "ascendant": {"sign": "Leo"}},
        "section_statuses": {"chart_core": "ok", "dasha_all": "ok"},
    }

    strict = _collect_strict_evidence("career", result)

    assert strict["official_primary_evidence"]["chart_core"]["status"] == "ok"
    assert strict["official_primary_evidence"]["dasha"]["status"] == "ok"
    assert strict["local_supplemental_evidence"]["a10_karma_pada"]["role"] == "required_local_supplement"
    assert strict["local_supplemental_evidence"]["narayana_current"]["role"] == "required_local_supplement"


def test_career_strict_contract_exposes_adjudication_stages_and_multi_reference_summary() -> None:
    strict = _collect_strict_evidence("career", _base_career_result())

    assert strict["adjudication_stages"]["promise"]["status"] in {"present", "weak", "missing"}
    assert strict["adjudication_stages"]["activation"]["required_timing_systems"] == ["Vimshottari", "Narayana"]
    assert strict["adjudication_stages"]["label"]["value"] == strict["event_judgement"]["dominant_label"]
    assert "multi_reference_reading_summary" in strict
    summary = strict["multi_reference_reading_summary"]
    assert "root_frame" in summary
    assert "divisional_frame" in summary
    assert "visibility_frame" in summary
    assert "karaka_frame" in summary
    assert "timing_frame" in summary
    assert "modifier_frame" in summary
    assert "conflict_frame" in summary


def test_career_strict_contract_exposes_monthly_adjudication_summary() -> None:
    result = _base_career_result()
    result["modules"]["vedastro_range_scan_result"] = {
        "backend": "vedastro_service_adapter_candidate",
        "status": "ok",
        "operation": "range_scan",
        "domain": "career",
        "evidence_ledger": [],
        "daily_windows": [
            {
                "date": "2026-07-18",
                "domain": "career",
                "score": 5,
                "confidence": "high",
                "event_count": 2,
                "signal_families": ["career_trigger"],
                "event_ids": ["GocharJupiterAspect10th", "CareerExpansionWindow"],
                "top_signal_label": "Career expansion window",
            },
            {
                "date": "2026-07-28",
                "domain": "career",
                "score": 6,
                "confidence": "high",
                "event_count": 2,
                "signal_families": ["career_trigger"],
                "event_ids": ["TravelForWork", "GocharJupiterAspect10th"],
                "top_signal_label": "Travel for work expansion window",
            },
        ],
        "top_daily_window": {
            "date": "2026-07-28",
            "domain": "career",
            "score": 6,
            "confidence": "high",
            "event_count": 2,
            "signal_families": ["career_trigger"],
            "event_ids": ["TravelForWork", "GocharJupiterAspect10th"],
            "top_signal_label": "Travel for work expansion window",
        },
        "source_metadata": {},
    }

    strict = _collect_strict_evidence("career", result)

    summary = strict["monthly_adjudication_summary"]
    assert summary["route"] == "career"
    assert summary["primary_state"]["value"] in {"推进", "启动", "重组", "收束", "观察"}
    assert summary["manifestation_mode"]["value"]
    assert summary["friction_source"]["value"]
    assert summary["time_confidence"]["value"] in {"day_supported", "month_supported", "month_only", "blocked"}
    assert isinstance(summary["supporting_days"], list)
    assert summary["supporting_days"][0]["date"] == "2026-07-18"


def test_career_strict_contract_exposes_compact_technique_audit_summary() -> None:
    strict = _collect_strict_evidence("career", _base_career_result())

    audit = strict["technique_audit_summary"]
    assert audit["functional_benefic_malefic"]["gate"] == "hard"
    assert audit["relevant_vargas"]["gate"] == "hard"
    assert audit["vimshottari_narayana_crosscheck"]["gate"] == "hard"
    assert audit["source_priority_boundary"]["fallback_used"] == strict["fallback_used"]


def test_career_external_activation_derives_user_readable_day_signals() -> None:
    result = _base_career_result()
    result["modules"]["vedastro_range_scan_result"] = {
        "backend": "vedastro_service_adapter_candidate",
        "status": "ok",
        "operation": "range_scan",
        "domain": "career",
        "evidence_ledger": [],
        "daily_windows": [
            {
                "date": "2026-07-18",
                "domain": "career",
                "score": 5,
                "confidence": "high",
                "event_count": 2,
                "signal_families": ["career_trigger"],
                "event_ids": ["GocharJupiterAspect10th", "CareerExpansionWindow"],
                "top_signal_label": "Career expansion window",
            },
            {
                "date": "2026-07-26",
                "domain": "career",
                "score": 2,
                "confidence": "medium",
                "event_count": 1,
                "signal_families": ["career_pressure"],
                "event_ids": ["SaturnIn10thCareerWindow"],
                "top_signal_label": "Saturn in 10th career window",
            },
        ],
        "top_daily_window": {
            "date": "2026-07-18",
            "domain": "career",
            "score": 5,
            "confidence": "high",
            "event_count": 2,
            "signal_families": ["career_trigger"],
            "event_ids": ["GocharJupiterAspect10th", "CareerExpansionWindow"],
            "top_signal_label": "Career expansion window",
        },
        "source_metadata": {},
    }

    strict = _collect_strict_evidence("career", result)
    external = strict["present_evidence"]["external_activation"]

    assert external["official_day_signals"][0]["date"] == "2026-07-18"
    assert external["official_day_signals"][0]["day_type"] == "opportunity_entry"
    assert external["official_day_signals"][0]["summary"] == "事业机会进入日"
    assert external["official_day_signals"][1]["day_type"] == "pressure_opportunity"


def test_career_official_day_signals_distinguish_motion_and_closure_risk() -> None:
    result = _base_career_result()
    result["modules"]["vedastro_range_scan_result"] = {
        "backend": "vedastro_service_adapter_candidate",
        "status": "ok",
        "operation": "range_scan",
        "domain": "career",
        "evidence_ledger": [],
        "daily_windows": [
            {
                "date": "2026-07-28",
                "domain": "career",
                "score": 6,
                "confidence": "high",
                "event_count": 2,
                "signal_families": [],
                "event_ids": ["GoodLunarDayForTravel", "GoodSunSignForBuilding"],
                "top_signal_label": "Good lunar day for travel",
            },
            {
                "date": "2025-02-28",
                "domain": "career",
                "score": 4,
                "confidence": "medium",
                "event_count": 2,
                "signal_families": [],
                "event_ids": ["BadLunarDayForTravel", "BadForSellingForProfit"],
                "top_signal_label": "Bad lunar day for travel",
            },
        ],
        "top_daily_window": {
            "date": "2026-07-28",
            "domain": "career",
            "score": 6,
            "confidence": "high",
            "event_count": 2,
            "signal_families": [],
            "event_ids": ["GoodLunarDayForTravel", "GoodSunSignForBuilding"],
            "top_signal_label": "Good lunar day for travel",
        },
        "source_metadata": {},
    }

    strict = _collect_strict_evidence("career", result)
    signals = strict["present_evidence"]["external_activation"]["official_day_signals"]

    assert signals[0]["day_type"] == "relocation_motion"
    assert signals[0]["summary"] == "事业迁移动作日"
    assert signals[1]["day_type"] == "closure_risk"
    assert signals[1]["summary"] == "事业真正收尾风险日"


def test_career_narrative_payload_forces_monthly_adjudication_layers_into_final_chinese_conclusion() -> None:
    result = _base_career_result()
    result["modules"]["vedastro_range_scan_result"] = {
        "backend": "vedastro_service_adapter_candidate",
        "status": "ok",
        "operation": "range_scan",
        "domain": "career",
        "evidence_ledger": [],
        "daily_windows": [
            {
                "date": "2026-07-18",
                "domain": "career",
                "score": 5,
                "confidence": "high",
                "event_count": 2,
                "signal_families": ["career_trigger"],
                "event_ids": ["GocharJupiterAspect10th", "CareerExpansionWindow"],
                "top_signal_label": "Career expansion window",
            }
        ],
        "top_daily_window": {
            "date": "2026-07-18",
            "domain": "career",
            "score": 5,
            "confidence": "high",
            "event_count": 2,
            "signal_families": ["career_trigger"],
            "event_ids": ["GocharJupiterAspect10th", "CareerExpansionWindow"],
            "top_signal_label": "Career expansion window",
        },
        "source_metadata": {},
    }

    strict = _collect_strict_evidence("career", result)
    payload = jyotish_engine._build_career_narrative_payload(strict)

    assert "事业" in payload["headline"]
    assert payload["monthly_frame"]["primary_state"]["value"]
    assert payload["monthly_frame"]["manifestation_mode"]["value"]
    assert payload["monthly_frame"]["friction_source"]["value"]
    assert payload["monthly_frame"]["time_confidence"]["value"]
    assert any("月度主状态" in item for item in payload["strengths"])
    assert any("阻力来源" in item for item in payload["risks"])
    assert "时间置信度" in payload["markdown"]
