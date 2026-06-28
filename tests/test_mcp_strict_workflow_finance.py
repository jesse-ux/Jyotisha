#!/usr/bin/env python3
"""Regression tests for MCP finance event adjudication."""

from __future__ import annotations

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
