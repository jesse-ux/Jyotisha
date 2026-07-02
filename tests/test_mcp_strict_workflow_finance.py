#!/usr/bin/env python3
"""Regression tests for MCP finance event adjudication."""

from __future__ import annotations

import jyotish_engine

from mcp_server import (
    _collect_strict_evidence,
    _derive_event_judgement,
    _derive_wealth_promise_strength,
    _derive_yogi_wealth_support,
)


def test_finance_public_wealth_label_requires_at_least_moderate_window() -> None:
    judgement = _derive_event_judgement(
        "finance",
        {
            "wealth_convergence": {"convergence_level": "L1", "probability": "+15-20%"},
            "gains_convergence": {"convergence_level": "L1", "probability": "+15-20%"},
            "career_convergence": {"convergence_level": "L1", "probability": "+15-20%"},
            "vimshottari_current": {"mahadasha": "Venus", "antardasha": "Mercury"},
            "narayana_current": {"sign": "Taurus", "lord": "Venus"},
        },
        [],
    )

    assert judgement["event_family"] == "finance"
    assert judgement["score"] == 40
    assert judgement["verdict"] == "weak_window_needs_confirmation"
    assert judgement["payout_label"] is None
    assert judgement["dominant_label"] is None
    assert judgement["secondary_context"] == []


def test_finance_strict_contract_attaches_existing_interpretation_source_pack() -> None:
    strict = _collect_strict_evidence("finance", {"modules": {}})

    source_pack = strict["present_evidence"]["interpretation_source_pack"]
    assert source_pack["status"] == "used"
    assert "lakshmi_dhana_activation_chain" in source_pack["template_registry"]["template_ids"]
    assert "yogi_asc_tight_orb_wealth" in source_pack["template_registry"]["template_ids"]
    assert source_pack["bphs_raman_layer"]["status"] == "available"
    assert source_pack["frontend_planet_house_details"]["coverage"] == "9_planets_x_12_houses"
    assert source_pack["interpretation_source_inventory"]["status"] == "used"
    assert source_pack["frontend_interpretation_layer"]["status"] == "available"
    assert source_pack["yoga_rule_layer"]["status"] == "available"
    assert source_pack["qa_governance_layer"]["status"] == "available"

    audit = strict["technique_audit_summary"]
    assert audit["interpretation_source_pack"]["used"] is True
    assert audit["mevg_global_web_evidence"]["effect_on_confidence"] == "blocks_or_downgrades_interpretive_claims_until_completed"
    assert audit["real_case_calibration"]["effect_on_confidence"] == "caps_confidence_without_matching_cases"


def test_finance_public_wealth_label_can_lift_visible_wealth_cases() -> None:
    judgement = _derive_event_judgement(
        "finance",
        {
            "wealth_convergence": {"convergence_level": "L1", "probability": "+15-20%"},
            "gains_convergence": {"convergence_level": "L2", "probability": "35-50%"},
            "career_convergence": {"convergence_level": "L2", "probability": "35-50%"},
            "vimshottari_current": {"mahadasha": "Jupiter", "antardasha": "Venus"},
            "narayana_current": {"sign": "Libra", "lord": "Venus"},
        },
        [],
    )

    assert judgement["event_family"] == "finance"
    assert judgement["score"] == 60
    assert judgement["verdict"] == "moderate_probability_window"
    assert judgement["payout_label"] == "public_wealth_status"
    assert judgement["dominant_label"] == "public_wealth_status"
    assert judgement["secondary_context"] == ["career_status", "gains_wishes"]


def test_finance_prefers_income_growth_when_gains_outrun_public_status_signals() -> None:
    judgement = _derive_event_judgement(
        "finance",
        {
            "wealth_convergence": {"convergence_level": "L1", "probability": "+15-20%"},
            "gains_convergence": {"convergence_level": "L3", "probability": "50-65%"},
            "vimshottari_current": {"mahadasha": "Venus", "antardasha": "Moon"},
            "narayana_current": {"sign": "Gemini", "lord": "Mercury"},
        },
        [],
    )

    assert judgement["event_family"] == "finance"
    assert judgement["score"] == 80
    assert judgement["verdict"] == "moderate_probability_window"
    assert judgement["payout_label"] == "income_growth"
    assert judgement["dominant_label"] == "income_growth"
    assert judgement["secondary_context"] == ["wealth_family"]


def test_finance_strong_wealth_promise_can_unlock_public_wealth_status() -> None:
    judgement = _derive_event_judgement(
        "finance",
        {
            "wealth_convergence": {"convergence_level": "L1", "probability": "+15-20%"},
            "gains_convergence": {"convergence_level": "L1", "probability": "+15-20%"},
            "career_convergence": {"convergence_level": "L1", "probability": "+15-20%"},
            "vimshottari_current": {"mahadasha": "Venus", "antardasha": "Mercury"},
            "narayana_current": {"sign": "Taurus", "lord": "Venus"},
            "wealth_promise_strength": {
                "level": "strong",
                "primary_source": "dhana_yogas",
                "supporting_sources": ["dhana"],
                "source_diversity": 1,
                "count": 1,
            },
        },
        [],
    )

    assert judgement["event_family"] == "finance"
    assert judgement["score"] == 60
    assert judgement["verdict"] == "moderate_probability_window"
    assert judgement["payout_label"] == "public_wealth_status"
    assert judgement["dominant_label"] == "public_wealth_status"
    assert judgement["secondary_context"] == ["career_status", "gains_wishes"]


def test_finance_source_diversity_adds_small_bump_without_changing_verdict_band() -> None:
    low_diversity = _derive_event_judgement(
        "finance",
        {
            "wealth_convergence": {"convergence_level": "L1", "probability": "+15-20%"},
            "gains_convergence": {"convergence_level": "L1", "probability": "+15-20%"},
            "career_convergence": {"convergence_level": "L1", "probability": "+15-20%"},
            "vimshottari_current": {"mahadasha": "Venus", "antardasha": "Mercury"},
            "narayana_current": {"sign": "Taurus", "lord": "Venus"},
            "wealth_promise_strength": {
                "level": "strong",
                "primary_source": "dhana_yogas",
                "supporting_sources": ["dhana"],
                "source_diversity": 1,
                "count": 2,
            },
        },
        [],
    )
    high_diversity = _derive_event_judgement(
        "finance",
        {
            "wealth_convergence": {"convergence_level": "L1", "probability": "+15-20%"},
            "gains_convergence": {"convergence_level": "L1", "probability": "+15-20%"},
            "career_convergence": {"convergence_level": "L1", "probability": "+15-20%"},
            "vimshottari_current": {"mahadasha": "Venus", "antardasha": "Mercury"},
            "narayana_current": {"sign": "Taurus", "lord": "Venus"},
            "wealth_promise_strength": {
                "level": "strong",
                "primary_source": "dhana_lakshmi_hooks",
                "supporting_sources": ["dhana", "lakshmi"],
                "source_diversity": 2,
                "count": 2,
            },
        },
        [],
    )

    assert low_diversity["verdict"] == "moderate_probability_window"
    assert high_diversity["verdict"] == "moderate_probability_window"
    assert high_diversity["score"] == low_diversity["score"] + 5


def test_finance_strict_contract_surfaces_official_block_and_local_fallback_usage() -> None:
    strict = _collect_strict_evidence("finance", {"modules": {"source_priority": {"mode": "local_fallback_official_blocked"}}})

    assert "official_primary_chart_blocked" in strict["blocked_items"]
    assert isinstance(strict["fallback_used"], list)
    assert isinstance(strict["conflicts"], list)


def test_finance_strict_contract_exposes_adjudication_stages_and_multi_reference_summary() -> None:
    strict = _collect_strict_evidence("finance", {"modules": {"source_priority": {"mode": "local_fallback_official_blocked"}}})

    assert strict["adjudication_stages"]["promise"]["status"] in {"present", "weak", "missing"}
    assert strict["adjudication_stages"]["activation"]["required_timing_systems"] == ["Vimshottari", "Narayana"]
    assert "multi_reference_reading_summary" in strict
    summary = strict["multi_reference_reading_summary"]
    assert "root_frame" in summary
    assert "divisional_frame" in summary
    assert "visibility_frame" in summary
    assert "karaka_frame" in summary
    assert "timing_frame" in summary
    assert "modifier_frame" in summary
    assert "conflict_frame" in summary


def test_finance_strict_contract_exposes_monthly_adjudication_summary() -> None:
    strict = _collect_strict_evidence(
        "finance",
        {
            "modules": {
                "source_priority": {"mode": "vedastro_official_primary"},
                "varga_full": {
                    "D2_Hora": {"summary": "hora ready"},
                    "D10_Dasamsa": {"summary": "dasamsa ready"},
                },
                "shadbala": {
                    "planets": {
                        "Venus": {
                            "components": {
                                "sthana": 1,
                                "dig": 1,
                                "kala": 1,
                                "chesta": 1,
                                "naisargika": 1,
                                "drik": 1,
                            }
                        }
                    }
                },
                "ashtakavarga": {"house_scores": {"2": {"sav_score": 33}, "11": {"sav_score": 35}}},
                "dasha": {"current_dasha": {"mahadasha": "Venus", "antardasha": "Mercury"}},
                "narayana_dasha": {"current_dasha": {"sign": "Taurus", "lord": "Venus"}},
                "dasa_convergence": {
                    "domain_activations": {
                        "wealth_family": {"convergence_level": "L2", "probability": "35-50%"},
                        "gains_wishes": {"convergence_level": "L1", "probability": "+15-20%"},
                    }
                },
                "chart": {"ascendant": {"sign": "Leo"}},
                "dhana_yogas": [{"name": "Dhana Yoga"}],
                "lakshmi_yoga": {"present": True},
                "vedastro_range_scan_result": {
                    "backend": "vedastro_service_adapter_candidate",
                    "status": "ok",
                    "operation": "range_scan",
                    "domain": "wealth",
                    "evidence_ledger": [],
                    "daily_windows": [
                        {
                            "date": "2026-10-04",
                            "domain": "wealth",
                            "score": 5,
                            "confidence": "high",
                            "event_count": 2,
                            "signal_families": ["wealth_trigger"],
                            "event_ids": ["GoodForBorrowingMoneyForBusiness", "GoodForLendingMoney"],
                            "top_signal_label": "Good for borrowing money for business",
                        },
                        {
                            "date": "2026-10-20",
                            "domain": "wealth",
                            "score": 2,
                            "confidence": "medium",
                            "event_count": 1,
                            "signal_families": ["wealth_pressure"],
                            "event_ids": ["BadForSellingForProfit"],
                            "top_signal_label": "Bad for selling for profit",
                        },
                    ],
                    "top_daily_window": {
                        "date": "2026-10-04",
                        "domain": "wealth",
                        "score": 5,
                        "confidence": "high",
                        "event_count": 2,
                        "signal_families": ["wealth_trigger"],
                        "event_ids": ["GoodForBorrowingMoneyForBusiness", "GoodForLendingMoney"],
                        "top_signal_label": "Good for borrowing money for business",
                    },
                    "source_metadata": {},
                },
            }
        },
    )

    summary = strict["monthly_adjudication_summary"]
    assert summary["route"] == "finance"
    assert summary["primary_state"]["value"] in {"推进", "启动", "整固", "收束", "观察"}
    assert summary["manifestation_mode"]["value"]
    assert summary["friction_source"]["value"]
    assert summary["time_confidence"]["value"] in {"day_supported", "month_supported", "month_only", "blocked"}
    assert isinstance(summary["supporting_days"], list)
    assert summary["supporting_days"][0]["date"] == "2026-10-04"


def test_finance_summary_modifier_frame_includes_yogi_and_ashtakavarga_only_as_modifiers() -> None:
    modules = {
        "source_priority": {"mode": "vedastro_official_primary"},
        "varga_full": {
            "D2_Hora": {"summary": "hora ready"},
            "D10_Dasamsa": {"summary": "dasamsa ready"},
        },
        "shadbala": {"planets": {"Venus": {"components": {"sthana": 1, "dig": 1, "kala": 1, "chesta": 1, "naisargika": 1, "drik": 1}}}},
        "ashtakavarga": {"house_scores": {"2": {"sav_score": 33}, "11": {"sav_score": 35}}},
        "dasha": {"current_dasha": {"mahadasha": "Venus", "antardasha": "Mercury"}},
        "narayana_dasha": {"current_dasha": {"sign": "Taurus", "lord": "Venus"}},
        "dasa_convergence": {"domain_activations": {"wealth_family": {"convergence_level": "L1"}}},
        "chart": {"ascendant": {"sign": "Leo"}},
        "source_priority": {"mode": "vedastro_official_primary"},
        "dhana_yogas": [{"name": "Dhana Yoga"}],
        "lakshmi_yoga": {"present": True},
    }
    strict = _collect_strict_evidence("finance", {"modules": modules})

    modifier = strict["multi_reference_reading_summary"]["modifier_frame"]
    assert "functional_benefic_malefic" in modifier
    assert modifier["ashtakavarga_finance_support"]["source"] == "ashtakavarga_house_scores_bridge_v1"
    assert modifier["yogi_support"]["role"] == "modifier_only"


def test_finance_strict_contract_compact_audit_marks_dual_dasha_gate() -> None:
    strict = _collect_strict_evidence("finance", {"modules": {"source_priority": {"mode": "local_fallback_official_blocked"}}})

    audit = strict["technique_audit_summary"]
    assert audit["vimshottari_narayana_crosscheck"]["gate"] == "hard"
    assert "official_primary_chart_blocked" in audit["source_priority_boundary"]["blocked_items"]


def test_finance_external_activation_derives_wealth_day_signals() -> None:
    strict = _collect_strict_evidence(
        "finance",
        {
            "modules": {
                "source_priority": {"mode": "vedastro_official_primary"},
                "varga_full": {
                    "D2_Hora": {"summary": "hora ready"},
                    "D10_Dasamsa": {"summary": "dasamsa ready"},
                },
                "shadbala": {
                    "planets": {
                        "Venus": {
                            "components": {
                                "sthana": 1,
                                "dig": 1,
                                "kala": 1,
                                "chesta": 1,
                                "naisargika": 1,
                                "drik": 1,
                            }
                        }
                    }
                },
                "ashtakavarga": {"house_scores": {"2": {"sav_score": 33}, "11": {"sav_score": 35}}},
                "dasha": {"current_dasha": {"mahadasha": "Venus", "antardasha": "Mercury"}},
                "narayana_dasha": {"current_dasha": {"sign": "Taurus", "lord": "Venus"}},
                "dasa_convergence": {
                    "domain_activations": {
                        "wealth_family": {"convergence_level": "L2", "probability": "35-50%"},
                        "gains_wishes": {"convergence_level": "L1", "probability": "+15-20%"},
                    }
                },
                "chart": {"ascendant": {"sign": "Leo"}},
                "vedastro_range_scan_result": {
                    "backend": "vedastro_service_adapter_candidate",
                    "status": "ok",
                    "operation": "range_scan",
                    "domain": "wealth",
                    "evidence_ledger": [],
                    "daily_windows": [
                        {
                            "date": "2026-10-04",
                            "domain": "wealth",
                            "score": 5,
                            "confidence": "high",
                            "event_count": 2,
                            "signal_families": ["wealth_trigger"],
                            "event_ids": ["GoodForBorrowingMoneyForBusiness", "GoodForLendingMoney"],
                            "top_signal_label": "Good for borrowing money for business",
                        },
                        {
                            "date": "2026-10-20",
                            "domain": "wealth",
                            "score": 2,
                            "confidence": "medium",
                            "event_count": 1,
                            "signal_families": ["wealth_pressure"],
                            "event_ids": ["BadForSellingForProfit"],
                            "top_signal_label": "Bad for selling for profit",
                        },
                    ],
                    "top_daily_window": {
                        "date": "2026-10-04",
                        "domain": "wealth",
                        "score": 5,
                        "confidence": "high",
                        "event_count": 2,
                        "signal_families": ["wealth_trigger"],
                        "event_ids": ["GoodForBorrowingMoneyForBusiness", "GoodForLendingMoney"],
                        "top_signal_label": "Good for borrowing money for business",
                    },
                    "source_metadata": {},
                },
            }
        },
    )

    external = strict["present_evidence"]["external_activation"]
    assert external["official_day_signals"][0]["date"] == "2026-10-04"
    assert external["official_day_signals"][0]["day_type"] == "opportunity"
    assert external["official_day_signals"][0]["summary"] == "财富机会日"
    assert external["official_day_signals"][1]["day_type"] == "risk"


def test_finance_deep_ashtakavarga_supports_add_small_score_bump_without_label_override() -> None:
    base = _derive_event_judgement(
        "finance",
        {
            "wealth_convergence": {"convergence_level": "L1", "probability": "+15-20%"},
            "gains_convergence": {"convergence_level": "L1", "probability": "+15-20%"},
            "career_convergence": {"convergence_level": "L1", "probability": "+15-20%"},
            "vimshottari_current": {"mahadasha": "Venus", "antardasha": "Mercury"},
            "narayana_current": {"sign": "Taurus", "lord": "Venus"},
            "wealth_promise_strength": {
                "level": "strong",
                "primary_source": "dhana_yogas",
                "supporting_sources": ["dhana", "lakshmi"],
                "source_diversity": 2,
                "count": 1,
            },
        },
        [],
    )
    weighted = _derive_event_judgement(
        "finance",
        {
            "wealth_convergence": {"convergence_level": "L1", "probability": "+15-20%"},
            "gains_convergence": {"convergence_level": "L1", "probability": "+15-20%"},
            "career_convergence": {"convergence_level": "L1", "probability": "+15-20%"},
            "vimshottari_current": {"mahadasha": "Venus", "antardasha": "Mercury"},
            "narayana_current": {"sign": "Taurus", "lord": "Venus"},
            "wealth_promise_strength": {
                "level": "strong",
                "primary_source": "dhana_yogas",
                "supporting_sources": ["dhana", "lakshmi"],
                "source_diversity": 2,
                "count": 1,
            },
            "pav_finance_support": {
                "level": "supportive",
                "source": "ashtakavarga_pav_bridge_v1",
                "signals": ["pav_finance_support"],
                "top_planets": ["Venus"],
            },
            "kakshya_finance_support": {
                "level": "supportive",
                "source": "kakshya_finance_bridge_v1",
                "signals": ["kakshya_finance_support"],
                "average_strength": 6.8,
            },
        },
        [],
    )

    assert base["dominant_label"] == "public_wealth_status"
    assert weighted["dominant_label"] == "public_wealth_status"
    assert weighted["score"] == base["score"] + 4


def test_finance_sodhita_and_kakshya_friction_reduce_score_without_forcing_label_swap() -> None:
    base = _derive_event_judgement(
        "finance",
        {
            "wealth_convergence": {"convergence_level": "L1", "probability": "+15-20%"},
            "gains_convergence": {"convergence_level": "L1", "probability": "+15-20%"},
            "career_convergence": {"convergence_level": "L1", "probability": "+15-20%"},
            "vimshottari_current": {"mahadasha": "Venus", "antardasha": "Mercury"},
            "narayana_current": {"sign": "Taurus", "lord": "Venus"},
            "wealth_promise_strength": {
                "level": "strong",
                "primary_source": "dhana_yogas",
                "supporting_sources": ["dhana", "lakshmi"],
                "source_diversity": 2,
                "count": 1,
            },
        },
        [],
    )
    weighted = _derive_event_judgement(
        "finance",
        {
            "wealth_convergence": {"convergence_level": "L1", "probability": "+15-20%"},
            "gains_convergence": {"convergence_level": "L1", "probability": "+15-20%"},
            "career_convergence": {"convergence_level": "L1", "probability": "+15-20%"},
            "vimshottari_current": {"mahadasha": "Venus", "antardasha": "Mercury"},
            "narayana_current": {"sign": "Taurus", "lord": "Venus"},
            "wealth_promise_strength": {
                "level": "strong",
                "primary_source": "dhana_yogas",
                "supporting_sources": ["dhana", "lakshmi"],
                "source_diversity": 2,
                "count": 1,
            },
            "sodhita_finance_support": {
                "level": "obstructive",
                "source": "ashtakavarga_sodhita_bridge_v1",
                "signals": ["sodhita_wealth_friction"],
                "target_houses": [2, 11],
                "raw_scores": {"2": 18, "11": 17},
            },
            "kakshya_finance_support": {
                "level": "obstructive",
                "source": "kakshya_finance_bridge_v1",
                "signals": ["kakshya_finance_friction"],
                "average_strength": 4.1,
            },
        },
        [],
    )

    assert base["dominant_label"] == "public_wealth_status"
    assert weighted["dominant_label"] == "public_wealth_status"
    assert weighted["score"] == base["score"] - 4


def test_collect_strict_evidence_finance_derives_wealth_promise_from_dhana_yogas() -> None:
    result = {
        "modules": {
            "varga_full": {"D2_Hora": {"summary": "ok"}, "D10_Dasamsa": {"summary": "ok"}},
            "shadbala": {"planets": {"Venus": {"total_rupa": 8.2}}},
            "ashtakavarga": {"house_scores": {"2": 31, "11": 36}},
            "dasha": {"current_dasha": {"mahadasha": "Venus", "antardasha": "Mercury"}},
            "narayana_dasha": {"current_dasha": {"sign": "Taurus", "lord": "Venus"}},
            "dasa_convergence": {
                "domain_activations": {
                    "wealth_family": {"convergence_level": "L1", "probability": "+15-20%"},
                    "gains_wishes": {"convergence_level": "L1", "probability": "+15-20%"},
                    "career_status": {"convergence_level": "L1", "probability": "+15-20%"},
                }
            },
            "yogas_doshas": {
                "dhana_yogas": {
                    "yogas": [
                        {"type": "Dhana Yoga", "strength": "strong"},
                        {"type": "Dhana Yoga", "strength": "moderate"},
                    ],
                    "summary": "Dhana Yoga检测：共2个格局",
                }
            },
        }
    }

    strict = _collect_strict_evidence("finance", result)
    present = strict["present_evidence"]
    assert present["wealth_promise_strength"] == {
        "level": "strong",
        "primary_source": "dhana_yogas",
        "count": 2,
        "source_diversity": 1,
        "supporting_sources": ["dhana"],
        "yogi_support": None,
    }
    assert strict["event_judgement"]["score"] == 100
    assert strict["event_judgement"]["verdict"] == "moderate_probability_window"
    assert strict["event_judgement"]["payout_label"] == "public_wealth_status"


def test_collect_strict_evidence_finance_folds_wealth_ashtakavarga_support() -> None:
    result = {
        "modules": {
            "varga_full": {"D2_Hora": {"summary": "ok"}, "D10_Dasamsa": {"summary": "ok"}},
            "shadbala": {"planets": {"Venus": {"total_rupa": 8.2}}},
            "ashtakavarga": {
                "house_scores": {
                    "2": 33,
                    "11": 35,
                    "10": {"sav": 32},
                }
            },
            "dasha": {"current_dasha": {"mahadasha": "Venus", "antardasha": "Mercury"}},
            "narayana_dasha": {"current_dasha": {"sign": "Taurus", "lord": "Venus"}},
            "dasa_convergence": {
                "domain_activations": {
                    "wealth_family": {"convergence_level": "L1", "probability": "+15-20%"},
                    "gains_wishes": {"convergence_level": "L1", "probability": "+15-20%"},
                    "career_status": {"convergence_level": "L1", "probability": "+15-20%"},
                }
            },
            "yogas_doshas": {
                "dhana_yogas": {
                    "yogas": [{"type": "Dhana Yoga", "strength": "moderate"}],
                    "summary": "Dhana Yoga检测：共1个格局",
                }
            },
        }
    }

    strict = _collect_strict_evidence("finance", result)

    assert strict["present_evidence"]["ashtakavarga_finance_support"] == {
        "level": "supportive",
        "source": "ashtakavarga_house_scores_bridge_v1",
        "target_houses": [2, 11],
        "signals": ["wealth_sav_support"],
        "raw_scores": {"2": 33, "11": 35},
    }
    assert "ashtakavarga_wealth_support" in strict["event_judgement"]["secondary_context"]


def test_collect_strict_evidence_finance_caps_confidence_when_shadbala_components_missing() -> None:
    result = {
        "modules": {
            "varga_full": {"D2_Hora": {"summary": "ok"}, "D10_Dasamsa": {"summary": "ok"}},
            "shadbala": {"planets": {"Venus": {"total_rupa": 8.2}}},
            "ashtakavarga": {"house_scores": {"2": 33, "11": 35}},
            "dasha": {"current_dasha": {"mahadasha": "Venus", "antardasha": "Mercury"}},
            "narayana_dasha": {"current_dasha": {"sign": "Taurus", "lord": "Venus"}},
            "dasa_convergence": {
                "domain_activations": {
                    "wealth_family": {"convergence_level": "L4", "probability": "70-85%"},
                    "gains_wishes": {"convergence_level": "L4", "probability": "70-85%"},
                    "career_status": {"convergence_level": "L4", "probability": "70-85%"},
                }
            },
            "yogas_doshas": {
                "dhana_yogas": {
                    "yogas": [{"type": "Dhana Yoga", "strength": "strong"}],
                    "summary": "Dhana Yoga检测：共1个格局",
                }
            },
        }
    }

    strict = _collect_strict_evidence("finance", result)

    assert strict["present_evidence"]["shadbala_component_audit"] == {
        "status": "incomplete",
        "source": "shadbala.planets",
        "required_components": ["sthana", "dig", "kala", "chesta", "naisargika", "drik"],
        "missing": {"Venus": ["sthana", "dig", "kala", "chesta", "naisargika", "drik"]},
    }
    assert strict["confidence_cap"] == "low"
    assert "shadbala_component_gap" in strict["event_judgement"]["secondary_context"]


def test_collect_strict_evidence_finance_accepts_complete_shadbala_components() -> None:
    result = {
        "modules": {
            "varga_full": {"D2_Hora": {"summary": "ok"}, "D10_Dasamsa": {"summary": "ok"}},
            "shadbala": {
                "planets": {
                    "Venus": {
                        "components": {
                            "sthana": 1.2,
                            "dig": 0.8,
                            "kala": 1.1,
                            "chesta": 0.9,
                            "naisargika": 0.7,
                            "drik": 0.4,
                        },
                        "total_rupa": 5.1,
                    }
                }
            },
            "ashtakavarga": {"house_scores": {"2": 33, "11": 35}},
            "dasha": {"current_dasha": {"mahadasha": "Venus", "antardasha": "Mercury"}},
            "narayana_dasha": {"current_dasha": {"sign": "Taurus", "lord": "Venus"}},
            "dasa_convergence": {
                "domain_activations": {
                    "wealth_family": {"convergence_level": "L4", "probability": "70-85%"},
                    "gains_wishes": {"convergence_level": "L4", "probability": "70-85%"},
                    "career_status": {"convergence_level": "L4", "probability": "70-85%"},
                }
            },
            "yogas_doshas": {
                "dhana_yogas": {
                    "yogas": [{"type": "Dhana Yoga", "strength": "strong"}],
                    "summary": "Dhana Yoga检测：共1个格局",
                }
            },
        }
    }

    strict = _collect_strict_evidence("finance", result)

    assert strict["present_evidence"]["shadbala_component_audit"] == {
        "status": "complete",
        "source": "shadbala.planets",
        "required_components": ["sthana", "dig", "kala", "chesta", "naisargika", "drik"],
        "missing": {},
    }
    assert strict["confidence_cap"] == "medium-high"
    assert "shadbala_component_gap" not in strict["event_judgement"]["secondary_context"]


def test_collect_strict_evidence_finance_adds_pav_and_kakshya_support_as_secondary_context() -> None:
    result = {
        "modules": {
            "chart": {"ascendant": {"sign": "Aries"}},
            "varga_full": {"D2_Hora": {"summary": "ok"}, "D10_Dasamsa": {"summary": "ok"}},
            "shadbala": {
                "planets": {
                    "Venus": {
                        "components": {
                            "sthana": 1.2,
                            "dig": 0.8,
                            "kala": 1.1,
                            "chesta": 0.9,
                            "naisargika": 0.7,
                            "drik": 0.4,
                        },
                        "total_rupa": 5.1,
                    }
                }
            },
            "ashtakavarga": {
                "house_scores": {"2": 33, "11": 35},
                "pav": {
                    "pav_summary": {
                        "Venus": {"Jupiter": 5, "Venus": 6, "Lagna": 5},
                        "Saturn": {"Saturn": 2},
                    }
                },
            },
            "kakshya": {
                "summary": {"average_strength": 6.8},
                "planets": {
                    "Venus": {"kakshya_strength": 7.4},
                    "Jupiter": {"kakshya_strength": 6.9},
                },
            },
            "dasha": {"current_dasha": {"mahadasha": "Venus", "antardasha": "Mercury"}},
            "narayana_dasha": {"current_dasha": {"sign": "Taurus", "lord": "Venus"}},
            "dasa_convergence": {
                "domain_activations": {
                    "wealth_family": {"convergence_level": "L1", "probability": "+15-20%"},
                    "gains_wishes": {"convergence_level": "L1", "probability": "+15-20%"},
                    "career_status": {"convergence_level": "L1", "probability": "+15-20%"},
                }
            },
            "yogas_doshas": {
                "dhana_yogas": {
                    "yogas": [{"type": "Dhana Yoga", "strength": "strong"}],
                    "summary": "Dhana Yoga检测：共1个格局",
                }
            },
        }
    }

    strict = _collect_strict_evidence("finance", result)

    assert strict["present_evidence"]["pav_finance_support"] == {
        "level": "supportive",
        "source": "ashtakavarga_pav_bridge_v1",
        "signals": ["pav_finance_support"],
        "top_planets": ["Venus"],
    }
    assert strict["present_evidence"]["kakshya_finance_support"] == {
        "level": "supportive",
        "source": "kakshya_finance_bridge_v1",
        "signals": ["kakshya_finance_support"],
        "average_strength": 6.8,
    }
    assert "pav_finance_support" in strict["event_judgement"]["secondary_context"]
    assert "kakshya_finance_support" in strict["event_judgement"]["secondary_context"]


def test_collect_strict_evidence_finance_flags_sodhita_wealth_friction() -> None:
    result = {
        "modules": {
            "chart": {"ascendant": {"sign": "Aries"}},
            "varga_full": {"D2_Hora": {"summary": "ok"}, "D10_Dasamsa": {"summary": "ok"}},
            "shadbala": {
                "planets": {
                    "Venus": {
                        "components": {
                            "sthana": 1.2,
                            "dig": 0.8,
                            "kala": 1.1,
                            "chesta": 0.9,
                            "naisargika": 0.7,
                            "drik": 0.4,
                        },
                        "total_rupa": 5.1,
                    }
                }
            },
            "ashtakavarga": {
                "house_scores": {"2": 33, "11": 35},
                "sodhita": {
                    "sodhita_sav": {
                        "assessment": [
                            {"sign": "Taurus", "score": 18, "level": "挑战"},
                            {"sign": "Aquarius", "score": 17, "level": "挑战"},
                        ]
                    }
                },
            },
            "dasha": {"current_dasha": {"mahadasha": "Venus", "antardasha": "Mercury"}},
            "narayana_dasha": {"current_dasha": {"sign": "Taurus", "lord": "Venus"}},
            "dasa_convergence": {
                "domain_activations": {
                    "wealth_family": {"convergence_level": "L1", "probability": "+15-20%"},
                    "gains_wishes": {"convergence_level": "L1", "probability": "+15-20%"},
                    "career_status": {"convergence_level": "L1", "probability": "+15-20%"},
                }
            },
            "yogas_doshas": {
                "dhana_yogas": {
                    "yogas": [{"type": "Dhana Yoga", "strength": "strong"}],
                    "summary": "Dhana Yoga检测：共1个格局",
                }
            },
        }
    }

    strict = _collect_strict_evidence("finance", result)

    assert strict["present_evidence"]["sodhita_finance_support"] == {
        "level": "obstructive",
        "source": "ashtakavarga_sodhita_bridge_v1",
        "signals": ["sodhita_wealth_friction"],
        "target_houses": [2, 11],
        "raw_scores": {"2": 18, "11": 17},
    }
    assert "sodhita_wealth_friction" in strict["event_judgement"]["secondary_context"]


def test_collect_strict_evidence_finance_flags_kakshya_friction_as_secondary_only() -> None:
    result = {
        "modules": {
            "chart": {"ascendant": {"sign": "Aries"}},
            "varga_full": {"D2_Hora": {"summary": "ok"}, "D10_Dasamsa": {"summary": "ok"}},
            "shadbala": {
                "planets": {
                    "Venus": {
                        "components": {
                            "sthana": 1.2,
                            "dig": 0.8,
                            "kala": 1.1,
                            "chesta": 0.9,
                            "naisargika": 0.7,
                            "drik": 0.4,
                        },
                        "total_rupa": 5.1,
                    }
                }
            },
            "ashtakavarga": {"house_scores": {"2": 33, "11": 35}},
            "kakshya": {
                "summary": {"average_strength": 4.1},
                "planets": {
                    "Venus": {"kakshya_strength": 4.0},
                },
            },
            "dasha": {"current_dasha": {"mahadasha": "Venus", "antardasha": "Mercury"}},
            "narayana_dasha": {"current_dasha": {"sign": "Taurus", "lord": "Venus"}},
            "dasa_convergence": {
                "domain_activations": {
                    "wealth_family": {"convergence_level": "L1", "probability": "+15-20%"},
                    "gains_wishes": {"convergence_level": "L1", "probability": "+15-20%"},
                    "career_status": {"convergence_level": "L1", "probability": "+15-20%"},
                }
            },
            "yogas_doshas": {
                "dhana_yogas": {
                    "yogas": [{"type": "Dhana Yoga", "strength": "strong"}],
                    "summary": "Dhana Yoga检测：共1个格局",
                }
            },
        }
    }

    strict = _collect_strict_evidence("finance", result)

    assert strict["present_evidence"]["kakshya_finance_support"] == {
        "level": "obstructive",
        "source": "kakshya_finance_bridge_v1",
        "signals": ["kakshya_finance_friction"],
        "average_strength": 4.1,
    }
    assert strict["event_judgement"]["dominant_label"] == "public_wealth_status"
    assert "kakshya_finance_friction" in strict["event_judgement"]["secondary_context"]


def test_collect_strict_evidence_finance_flags_low_wealth_ashtakavarga_friction() -> None:
    result = {
        "modules": {
            "varga_full": {"D2_Hora": {"summary": "ok"}, "D10_Dasamsa": {"summary": "ok"}},
            "shadbala": {"planets": {"Venus": {"total_rupa": 8.2}}},
            "ashtakavarga": {"house_scores": {"house_2": {"sav": 23}, "house_11": {"sav": 22}}},
            "dasha": {"current_dasha": {"mahadasha": "Venus", "antardasha": "Mercury"}},
            "narayana_dasha": {"current_dasha": {"sign": "Taurus", "lord": "Venus"}},
            "dasa_convergence": {
                "domain_activations": {
                    "wealth_family": {"convergence_level": "L1", "probability": "+15-20%"},
                    "gains_wishes": {"convergence_level": "L1", "probability": "+15-20%"},
                    "career_status": {"convergence_level": "L1", "probability": "+15-20%"},
                }
            },
            "yogas_doshas": {
                "dhana_yogas": {
                    "yogas": [{"type": "Dhana Yoga", "strength": "strong"}],
                    "summary": "Dhana Yoga检测：共1个格局",
                }
            },
        }
    }

    strict = _collect_strict_evidence("finance", result)

    assert strict["present_evidence"]["ashtakavarga_finance_support"] == {
        "level": "obstructive",
        "source": "ashtakavarga_house_scores_bridge_v1",
        "target_houses": [2, 11],
        "signals": ["wealth_sav_low"],
        "raw_scores": {"2": 23, "11": 22},
    }
    assert "ashtakavarga_wealth_friction" in strict["event_judgement"]["secondary_context"]


def test_collect_strict_evidence_finance_combines_dhana_and_lakshmi_hooks() -> None:
    result = {
        "modules": {
            "varga_full": {"D2_Hora": {"summary": "ok"}, "D10_Dasamsa": {"summary": "ok"}},
            "shadbala": {"planets": {"Venus": {"total_rupa": 8.2}}},
            "ashtakavarga": {"house_scores": {"2": 31, "11": 36}},
            "dasha": {"current_dasha": {"mahadasha": "Venus", "antardasha": "Mercury"}},
            "narayana_dasha": {"current_dasha": {"sign": "Taurus", "lord": "Venus"}},
            "dasa_convergence": {
                "domain_activations": {
                    "wealth_family": {"convergence_level": "L1", "probability": "+15-20%"},
                    "gains_wishes": {"convergence_level": "L1", "probability": "+15-20%"},
                    "career_status": {"convergence_level": "L1", "probability": "+15-20%"},
                }
            },
            "yogas_doshas": {
                "dhana_yogas": {
                    "yogas": [
                        {"type": "Dhana Yoga", "strength": "moderate"},
                        {"type": "Lakshmi Yoga", "strength": "strong"},
                    ],
                    "summary": "Dhana/Lakshmi检测：共2个格局",
                }
            },
        }
    }

    strict = _collect_strict_evidence("finance", result)
    assert strict["present_evidence"]["wealth_promise_strength"] == {
        "level": "strong",
        "primary_source": "dhana_lakshmi_hooks",
        "count": 2,
        "source_diversity": 2,
        "supporting_sources": ["dhana", "lakshmi"],
        "yogi_support": None,
    }


def test_collect_strict_evidence_finance_collects_vedastro_range_scan_as_external_activation_context() -> None:
    result = {
        "modules": {
            "varga_full": {"D2_Hora": {"summary": "ok"}, "D10_Dasamsa": {"summary": "ok"}},
            "shadbala": {"planets": {"Venus": {"total_rupa": 8.2}}},
            "ashtakavarga": {"house_scores": {"2": 31, "11": 36}},
            "dasha": {"current_dasha": {"mahadasha": "Venus", "antardasha": "Mercury"}},
            "narayana_dasha": {"current_dasha": {"sign": "Taurus", "lord": "Venus"}},
            "dasa_convergence": {
                "domain_activations": {
                    "wealth_family": {"convergence_level": "L1", "probability": "+15-20%"},
                    "gains_wishes": {"convergence_level": "L1", "probability": "+15-20%"},
                    "career_status": {"convergence_level": "L1", "probability": "+15-20%"},
                }
            },
            "external_activation": {
                "evidence_ledger": [
                    {
                        "source": "vedastro_service_adapter_candidate",
                        "operation": "range_scan",
                        "domain": "wealth",
                        "event_id": "jupiter_2h_11h_window",
                        "score": 76,
                    }
                ]
            },
        }
    }

    strict = _collect_strict_evidence("finance", result)

    assert strict["present_evidence"]["external_activation"]["level"] == "moderate"
    assert strict["present_evidence"]["external_activation"]["source"] == "vedastro_service_adapter_candidate"
    assert "external_activation_support" in strict["event_judgement"]["secondary_context"]


def test_finance_dignity_guardrail_conflict_caps_to_zero_delta() -> None:
    result = {
        "modules": {
            "varga_full": {"D2_Hora": {"summary": "ok"}, "D10_Dasamsa": {"summary": "ok"}},
            "shadbala": {"planets": {"Venus": {"total_rupa": 8.2}}},
            "ashtakavarga": {"house_scores": {"2": 31, "11": 36}},
            "chart": {
                "ascendant": {"sign": "Leo"},
                "planets": {
                    "Mercury": {"status": "落陷取消(Neecha Bhanga)"},
                    "Venus": {"status": "极敌(Great Enemy)"},
                    "Jupiter": {"status": "中性(Neutral)"},
                },
            },
            "dasha": {"current_dasha": {"mahadasha": "Venus", "antardasha": "Mercury"}},
            "narayana_dasha": {"current_dasha": {"sign": "Taurus", "lord": "Venus"}},
            "dasa_convergence": {
                "domain_activations": {
                    "wealth_family": {"convergence_level": "L1", "probability": "+15-20%"},
                    "gains_wishes": {"convergence_level": "L1", "probability": "+15-20%"},
                    "career_status": {"convergence_level": "L1", "probability": "+15-20%"},
                }
            },
        }
    }

    strict = _collect_strict_evidence("finance", result)

    assert strict["present_evidence"]["dignity_guardrail"]["status"] == "conflict"
    assert strict["present_evidence"]["dignity_guardrail"]["score_delta"] == 0
    assert "dignity_conflict" in strict["event_judgement"]["secondary_context"]


def test_finance_dignity_guardrail_ignores_non_relevant_planets() -> None:
    result = {
        "modules": {
            "varga_full": {"D2_Hora": {"summary": "ok"}, "D10_Dasamsa": {"summary": "ok"}},
            "shadbala": {"planets": {"Venus": {"total_rupa": 8.2}}},
            "ashtakavarga": {"house_scores": {"2": 31, "11": 36}},
            "chart": {
                "ascendant": {"sign": "Leo"},
                "planets": {
                    "Mars": {"status": "落陷取消(Neecha Bhanga)"},
                    "Saturn": {"status": "极敌(Great Enemy)"},
                    "Venus": {"status": "中性(Neutral)"},
                    "Jupiter": {"status": "中性(Neutral)"},
                },
            },
            "dasha": {"current_dasha": {"mahadasha": "Venus", "antardasha": "Mercury"}},
            "narayana_dasha": {"current_dasha": {"sign": "Taurus", "lord": "Venus"}},
            "dasa_convergence": {
                "domain_activations": {
                    "wealth_family": {"convergence_level": "L1", "probability": "+15-20%"},
                    "gains_wishes": {"convergence_level": "L1", "probability": "+15-20%"},
                    "career_status": {"convergence_level": "L1", "probability": "+15-20%"},
                }
            },
        }
    }

    strict = _collect_strict_evidence("finance", result)

    assert strict["present_evidence"]["dignity_guardrail"]["score_delta"] == 0
    assert "dignity_supportive_recovery" not in strict["event_judgement"]["secondary_context"]
    assert "dignity_high_friction" not in strict["event_judgement"]["secondary_context"]


def test_collect_strict_evidence_finance_ignores_non_matching_external_activation_domains() -> None:
    result = {
        "modules": {
            "varga_full": {"D2_Hora": {"summary": "ok"}, "D10_Dasamsa": {"summary": "ok"}},
            "shadbala": {"planets": {"Venus": {"total_rupa": 8.2}}},
            "ashtakavarga": {"house_scores": {"2": 31, "11": 36}},
            "dasha": {"current_dasha": {"mahadasha": "Venus", "antardasha": "Mercury"}},
            "narayana_dasha": {"current_dasha": {"sign": "Taurus", "lord": "Venus"}},
            "dasa_convergence": {
                "domain_activations": {
                    "wealth_family": {"convergence_level": "L1", "probability": "+15-20%"},
                }
            },
            "external_activation": {
                "evidence_ledger": [
                    {
                        "source": "vedastro_service_adapter_candidate",
                        "operation": "range_scan",
                        "domain": "marriage",
                        "event_id": "relationship_window",
                        "score": 95,
                    }
                ]
            },
        }
    }

    strict = _collect_strict_evidence("finance", result)

    assert strict["present_evidence"]["external_activation"]["level"] == "none"
    assert "external_activation_support" not in strict["event_judgement"]["secondary_context"]


def test_derive_yogi_wealth_support_detects_strong_native_hook() -> None:
    modules = {
        "chart": {
            "ascendant": {"sign": "Aries", "degree_raw": 20.0},
            "planets": {
                "Sun": {"degree_raw": 140.0},
                "Moon": {"degree_raw": 240.0},
                "Venus": {"house": 11, "sign": "Aquarius", "status": "入友(Friendly Sign)"},
                "Saturn": {"house": 6, "sign": "Virgo", "status": "中性"},
            }
        },
    }
    support = _derive_yogi_wealth_support(modules)
    assert support is not None
    assert support["level"] == "strong"
    assert support["source"] == "yogi_asc_tight_orb_wealth"
    assert support["yogi_planet"] == "Venus"
    assert support["duplicate_yogi"] == "Mars"
    assert support["avayogi"] == "Saturn"
    assert support["yogi_point_house"] == 1
    assert support["tight_orb_hits"] == ["lagna_yogi_tight_orb"]
    assert support["wealth_lord_links"] == ["yogi_planet_is_2l"]
    assert support["risk_flags"] == []
    assert support["signals"] == [
        "yogi_planet_in_wealth_house",
        "yogi_planet_is_2l",
        "lagna_yogi_tight_orb",
    ]


def test_wealth_folding_dhana_keeps_yogi_quiet_when_native_support_is_weak() -> None:
    modules = {
        "yogas_doshas": {
            "dhana_yogas": {
                "yogas": [{"type": "dhana", "strength": "strong"}]
            }
        },
        "chart": {
            "ascendant": {"sign": "Taurus", "degree_raw": 45.0},
            "planets": {
                "Sun": {"degree_raw": 20.0},
                "Moon": {"degree_raw": 20.0},
                "Venus": {"house": 3, "sign": "Cancer", "status": "中性"},
                "Saturn": {"house": 8, "sign": "Sagittarius", "status": "中性"},
            }
        },
    }
    res = _derive_wealth_promise_strength(modules)
    assert res["primary_source"] == "dhana_yogas"
    assert res["source_diversity"] == 1
    assert res["supporting_sources"] == ["dhana"]
    assert res["level"] == "strong"
    assert res["yogi_support"] is None


def test_wealth_folding_adds_native_yogi_support_only_when_base_promise_exists() -> None:
    modules = {
        "yogas_doshas": {
            "dhana_yogas": {
                "yogas": [{"type": "dhana", "strength": "moderate"}]
            }
        },
        "chart": {
            "ascendant": {"sign": "Aries", "degree_raw": 20.0},
            "planets": {
                "Sun": {"degree_raw": 140.0},
                "Moon": {"degree_raw": 240.0},
                "Venus": {"house": 11, "sign": "Aquarius", "status": "入友(Friendly Sign)"},
                "Saturn": {"house": 6, "sign": "Virgo", "status": "中性"},
            }
        },
    }
    res = _derive_wealth_promise_strength(modules)
    assert res["level"] == "moderate"
    assert res["primary_source"] == "dhana_yogi_hooks"
    assert res["source_diversity"] == 2
    assert res["supporting_sources"] == ["dhana", "yogi"]
    assert res["yogi_support"]["level"] == "strong"
    assert res["yogi_support"]["wealth_lord_links"] == ["yogi_planet_is_2l"]


def test_wealth_folding_yogi_only_is_blocked_without_base_promise() -> None:
    modules = {
        "chart": {
            "ascendant": {"sign": "Aries", "degree_raw": 20.0},
            "planets": {
                "Sun": {"degree_raw": 140.0},
                "Moon": {"degree_raw": 240.0},
                "Venus": {"house": 11, "sign": "Aquarius", "status": "入友(Friendly Sign)"},
                "Saturn": {"house": 6, "sign": "Virgo", "status": "中性"},
            }
        },
    }
    assert _derive_wealth_promise_strength(modules) is None


def test_collect_strict_evidence_finance_adds_native_yogi_hook_without_external_truth() -> None:
    result = {
        "modules": {
            "chart": {
                "ascendant": {"sign": "Aries", "lord": "Mars", "degree_raw": 20.0},
                "planets": {
                    "Venus": {
                        "sign": "Aquarius",
                        "house": 11,
                        "status": "入友(Friendly Sign)",
                    },
                    "Saturn": {"sign": "Virgo", "house": 6, "status": "中性"},
                    "Sun": {"degree_raw": 140.0},
                    "Moon": {"degree_raw": 240.0},
                },
            },
            "varga_full": {"D2_Hora": {"summary": "ok"}, "D10_Dasamsa": {"summary": "ok"}},
            "shadbala": {"planets": {"Venus": {"total_rupa": 8.2}}},
            "ashtakavarga": {"house_scores": {"2": 31, "11": 36}},
            "dasha": {"current_dasha": {"mahadasha": "Venus", "antardasha": "Mercury"}},
            "narayana_dasha": {"current_dasha": {"sign": "Taurus", "lord": "Venus"}},
            "dasa_convergence": {
                "domain_activations": {
                    "wealth_family": {"convergence_level": "L1", "probability": "+15-20%"},
                    "gains_wishes": {"convergence_level": "L1", "probability": "+15-20%"},
                    "career_status": {"convergence_level": "L1", "probability": "+15-20%"},
                }
            },
            "yogas_doshas": {
                "dhana_yogas": {
                    "yogas": [{"type": "Dhana Yoga", "strength": "moderate"}],
                    "summary": "Dhana检测：共1个格局",
                }
            },
        },
    }

    strict = _collect_strict_evidence("finance", result)
    assert strict["present_evidence"]["wealth_promise_strength"] == {
        "level": "moderate",
        "primary_source": "dhana_yogi_hooks",
        "count": 1,
        "source_diversity": 2,
        "supporting_sources": ["dhana", "yogi"],
        "yogi_support": {
            "avayogi": "Saturn",
            "duplicate_yogi": "Mars",
            "lagna_yogi_distance_deg": 0.0,
            "level": "strong",
            "risk_flags": [],
            "signals": [
                "yogi_planet_in_wealth_house",
                "yogi_planet_is_2l",
                "lagna_yogi_tight_orb",
            ],
            "source": "yogi_asc_tight_orb_wealth",
            "tight_orb_hits": ["lagna_yogi_tight_orb"],
            "wealth_lord_links": ["yogi_planet_is_2l"],
            "yogi_planet": "Venus",
            "yogi_point_house": 1,
            "yogi_point_longitude": 20.0,
            "yogi_point_nakshatra": "Bharani",
        },
    }
    assert "yogi_active" in strict["event_judgement"]["secondary_context"]


def test_collect_strict_evidence_finance_keeps_native_yogi_quiet_when_support_is_weak() -> None:
    result = {
        "modules": {
            "chart": {
                "ascendant": {"sign": "Taurus", "lord": "Venus", "degree_raw": 45.0},
                "planets": {
                    "Venus": {
                        "sign": "Cancer",
                        "house": 3,
                        "status": "中性",
                    },
                    "Saturn": {"sign": "Sagittarius", "house": 8, "status": "中性"},
                    "Sun": {"degree_raw": 20.0},
                    "Moon": {"degree_raw": 20.0},
                },
            },
            "varga_full": {"D2_Hora": {"summary": "ok"}, "D10_Dasamsa": {"summary": "ok"}},
            "shadbala": {"planets": {"Venus": {"total_rupa": 8.2}}},
            "ashtakavarga": {"house_scores": {"2": 31, "11": 36}},
            "dasha": {"current_dasha": {"mahadasha": "Venus", "antardasha": "Mercury"}},
            "narayana_dasha": {"current_dasha": {"sign": "Taurus", "lord": "Venus"}},
            "dasa_convergence": {
                "domain_activations": {
                    "wealth_family": {"convergence_level": "L1", "probability": "+15-20%"},
                    "gains_wishes": {"convergence_level": "L1", "probability": "+15-20%"},
                    "career_status": {"convergence_level": "L1", "probability": "+15-20%"},
                }
            },
            "yogas_doshas": {
                "dhana_yogas": {
                    "yogas": [{"type": "Dhana Yoga", "strength": "moderate"}],
                    "summary": "Dhana检测：共1个格局",
                }
            },
        },
    }

    strict = _collect_strict_evidence("finance", result)
    assert strict["present_evidence"]["wealth_promise_strength"] == {
        "level": "moderate",
        "primary_source": "dhana_yogas",
        "count": 1,
        "source_diversity": 1,
        "supporting_sources": ["dhana"],
        "yogi_support": None,
    }
    assert "yogi_active" not in strict["event_judgement"]["secondary_context"]


def test_collect_strict_evidence_finance_adds_external_avayogi_risk_penalty() -> None:
    result = {
        "modules": {
            "chart": {
                "ascendant": {"sign": "Pisces", "lord": "Jupiter"},
                "planets": {
                    "Saturn": {
                        "sign": "Aries",
                        "house": 11,
                        "status": "Debilitated",
                    }
                },
            },
            "varga_full": {"D2_Hora": {"summary": "ok"}, "D10_Dasamsa": {"summary": "ok"}},
            "shadbala": {"planets": {"Venus": {"total_rupa": 8.2}}},
            "ashtakavarga": {"house_scores": {"2": 31, "11": 36}},
            "dasha": {"current_dasha": {"mahadasha": "Venus", "antardasha": "Mercury"}},
            "narayana_dasha": {"current_dasha": {"sign": "Taurus", "lord": "Venus"}},
            "dasa_convergence": {
                "domain_activations": {
                    "wealth_family": {"convergence_level": "L1", "probability": "+15-20%"},
                    "gains_wishes": {"convergence_level": "L1", "probability": "+15-20%"},
                    "career_status": {"convergence_level": "L1", "probability": "+15-20%"},
                }
            },
            "yogas_doshas": {
                "dhana_yogas": {
                    "yogas": [{"type": "Dhana Yoga", "strength": "moderate"}],
                    "summary": "Dhana检测：共1个格局",
                }
            },
        },
        "external_truth": {"avayogi_planet": "Saturn"},
    }

    strict = _collect_strict_evidence("finance", result)
    assert strict["present_evidence"]["avayogi_risk"] == {
        "planet": "Saturn",
        "house": 11,
        "status": "Debilitated",
        "source": "external_avayogi_planet",
        "risk_level": "moderate",
        "signals": ["avayogi_in_wealth_house"],
    }
    assert strict["event_judgement"]["score"] == 90
    assert "avayogi_active" in strict["event_judgement"]["secondary_context"]


def test_collect_strict_evidence_finance_keeps_external_avayogi_quiet_in_own_sign() -> None:
    result = {
        "modules": {
            "chart": {
                "ascendant": {"sign": "Pisces", "lord": "Jupiter"},
                "planets": {
                    "Saturn": {
                        "sign": "Capricorn",
                        "house": 11,
                        "status": "Own Sign",
                    }
                },
            },
            "varga_full": {"D2_Hora": {"summary": "ok"}, "D10_Dasamsa": {"summary": "ok"}},
            "shadbala": {"planets": {"Venus": {"total_rupa": 8.2}}},
            "ashtakavarga": {"house_scores": {"2": 31, "11": 36}},
            "dasha": {"current_dasha": {"mahadasha": "Venus", "antardasha": "Mercury"}},
            "narayana_dasha": {"current_dasha": {"sign": "Taurus", "lord": "Venus"}},
            "dasa_convergence": {
                "domain_activations": {
                    "wealth_family": {"convergence_level": "L1", "probability": "+15-20%"},
                    "gains_wishes": {"convergence_level": "L1", "probability": "+15-20%"},
                    "career_status": {"convergence_level": "L1", "probability": "+15-20%"},
                }
            },
            "yogas_doshas": {
                "dhana_yogas": {
                    "yogas": [{"type": "Dhana Yoga", "strength": "moderate"}],
                    "summary": "Dhana检测：共1个格局",
                }
            },
        },
        "external_truth": {"avayogi_planet": "Saturn"},
    }

    strict = _collect_strict_evidence("finance", result)
    assert strict["present_evidence"]["avayogi_risk"] is None
    assert strict["event_judgement"]["score"] == 95
    assert "avayogi_active" not in strict["event_judgement"]["secondary_context"]


def test_collect_strict_evidence_finance_does_not_add_avayogi_without_external_truth() -> None:
    result = {
        "modules": {
            "chart": {
                "ascendant": {"sign": "Pisces", "lord": "Jupiter"},
                "planets": {
                    "Saturn": {
                        "sign": "Aries",
                        "house": 11,
                        "status": "Debilitated",
                    }
                },
            },
            "varga_full": {"D2_Hora": {"summary": "ok"}, "D10_Dasamsa": {"summary": "ok"}},
            "shadbala": {"planets": {"Venus": {"total_rupa": 8.2}}},
            "ashtakavarga": {"house_scores": {"2": 31, "11": 36}},
            "dasha": {"current_dasha": {"mahadasha": "Venus", "antardasha": "Mercury"}},
            "narayana_dasha": {"current_dasha": {"sign": "Taurus", "lord": "Venus"}},
            "dasa_convergence": {
                "domain_activations": {
                    "wealth_family": {"convergence_level": "L1", "probability": "+15-20%"},
                    "gains_wishes": {"convergence_level": "L1", "probability": "+15-20%"},
                    "career_status": {"convergence_level": "L1", "probability": "+15-20%"},
                }
            },
            "yogas_doshas": {
                "dhana_yogas": {
                    "yogas": [{"type": "Dhana Yoga", "strength": "moderate"}],
                    "summary": "Dhana检测：共1个格局",
                }
            },
        },
    }

    strict = _collect_strict_evidence("finance", result)
    assert strict["present_evidence"].get("avayogi_risk") is None
    assert strict["event_judgement"]["score"] == 95
    assert "avayogi_active" not in strict["event_judgement"]["secondary_context"]


def test_finance_narrative_payload_forces_monthly_adjudication_layers_into_final_chinese_conclusion() -> None:
    strict = _collect_strict_evidence(
        "finance",
        {
            "modules": {
                "source_priority": {"mode": "vedastro_official_primary"},
                "varga_full": {
                    "D2_Hora": {"summary": "hora ready"},
                    "D10_Dasamsa": {"summary": "dasamsa ready"},
                },
                "shadbala": {
                    "planets": {
                        "Venus": {
                            "components": {
                                "sthana": 1,
                                "dig": 1,
                                "kala": 1,
                                "chesta": 1,
                                "naisargika": 1,
                                "drik": 1,
                            }
                        }
                    }
                },
                "ashtakavarga": {"house_scores": {"2": {"sav_score": 33}, "11": {"sav_score": 35}}},
                "dasha": {"current_dasha": {"mahadasha": "Venus", "antardasha": "Mercury"}},
                "narayana_dasha": {"current_dasha": {"sign": "Taurus", "lord": "Venus"}},
                "dasa_convergence": {
                    "domain_activations": {
                        "wealth_family": {"convergence_level": "L2", "probability": "35-50%"},
                        "gains_wishes": {"convergence_level": "L1", "probability": "+15-20%"},
                    }
                },
                "chart": {"ascendant": {"sign": "Leo"}},
                "dhana_yogas": [{"name": "Dhana Yoga"}],
                "lakshmi_yoga": {"present": True},
                "vedastro_range_scan_result": {
                    "backend": "vedastro_service_adapter_candidate",
                    "status": "ok",
                    "operation": "range_scan",
                    "domain": "wealth",
                    "evidence_ledger": [],
                    "daily_windows": [
                        {
                            "date": "2026-10-04",
                            "domain": "wealth",
                            "score": 5,
                            "confidence": "high",
                            "event_count": 2,
                            "signal_families": ["wealth_trigger"],
                            "event_ids": ["GoodForBorrowingMoneyForBusiness", "GoodForLendingMoney"],
                            "top_signal_label": "Good for borrowing money for business",
                        }
                    ],
                    "top_daily_window": {
                        "date": "2026-10-04",
                        "domain": "wealth",
                        "score": 5,
                        "confidence": "high",
                        "event_count": 2,
                        "signal_families": ["wealth_trigger"],
                        "event_ids": ["GoodForBorrowingMoneyForBusiness", "GoodForLendingMoney"],
                        "top_signal_label": "Good for borrowing money for business",
                    },
                    "source_metadata": {},
                },
            }
        },
    )

    payload = jyotish_engine._build_finance_narrative_payload(strict)

    assert "财富" in payload["headline"]
    assert payload["monthly_frame"]["primary_state"]["value"]
    assert payload["monthly_frame"]["manifestation_mode"]["value"]
    assert payload["monthly_frame"]["friction_source"]["value"]
    assert payload["monthly_frame"]["time_confidence"]["value"]
    assert any("月度主状态" in item for item in payload["strengths"])
    assert any("阻力来源" in item for item in payload["risks"])
    assert "时间置信度" in payload["markdown"]
