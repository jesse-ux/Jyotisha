#!/usr/bin/env python3
"""Regression tests for MCP relationship event adjudication."""

from __future__ import annotations

import sys
from pathlib import Path

from mcp_server import _collect_strict_evidence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import jyotish_engine  # noqa: E402


def _base_relationship_result() -> dict:
    return {
        "modules": {
            "varga_full": {"D9_Navamsa": {"summary": "ok"}},
            "special_lagnas": {"Upapada_Lagna": {"sign": "Libra", "lord": "Venus"}},
            "jaimini": {
                "darakaraka": {"planet": "Venus", "house": 7},
                "marriage_support": {"dk_7h_link": True},
            },
            "vivah_saham": {"sign": "Taurus", "house": 7},
            "dasha": {"current_dasha": {"mahadasha": "Venus", "antardasha": "Moon"}},
            "narayana_dasha": {"current_dasha": {"sign": "Libra", "lord": "Venus"}},
            "dasa_convergence": {
                "domain_activations": {
                    "marriage_partnership": {"convergence_level": "L1", "probability": "+15-20%"}
                }
            },
            "argala": {
                "houses": {
                    "house_7": {
                        "net_result": "obstructed",
                        "argala_count": 1,
                        "virodhargala_count": 2,
                    }
                }
            },
        }
    }


def test_relationship_jaimini_bridge_lifts_legal_marriage_label() -> None:
    strict = _collect_strict_evidence("relationship", _base_relationship_result())

    assert strict["present_evidence"]["jaimini_marriage_support"] == {
        "level": "moderate",
        "signals": ["darakaraka_active", "dk_7h_link"],
        "source": "jaimini_bridge_v1",
    }
    assert strict["event_judgement"]["dominant_label"] == "legal_marriage"
    assert strict["event_judgement"]["secondary_context"] == [
        "darakaraka_active",
        "jaimini_support",
        "ul_support",
        "virodhargala_obstruction",
        "vedastro_range_scan_missing",
    ]


def test_relationship_jaimini_bridge_stays_context_only_when_d9_missing() -> None:
    result = _base_relationship_result()
    del result["modules"]["varga_full"]["D9_Navamsa"]

    strict = _collect_strict_evidence("relationship", result)

    assert strict["present_evidence"]["jaimini_marriage_support"] == {
        "level": "moderate",
        "signals": ["darakaraka_active", "dk_7h_link"],
        "source": "jaimini_bridge_v1",
    }
    assert strict["event_judgement"]["dominant_label"] is None
    assert strict["event_judgement"]["secondary_context"] == [
        "darakaraka_active",
        "jaimini_support",
        "ul_support",
        "virodhargala_obstruction",
        "vedastro_range_scan_missing",
    ]


def test_relationship_jaimini_bridge_cannot_lift_legal_marriage_when_narayana_is_missing() -> None:
    result = _base_relationship_result()
    del result["modules"]["narayana_dasha"]

    strict = _collect_strict_evidence("relationship", result)

    assert strict["present_evidence"]["jaimini_marriage_support"] == {
        "level": "moderate",
        "signals": ["darakaraka_active", "dk_7h_link"],
        "source": "jaimini_bridge_v1",
    }
    assert strict["event_judgement"]["dominant_label"] is None
    assert "jaimini_support" in strict["event_judgement"]["secondary_context"]
    assert "public_formalization_candidate" not in strict["event_judgement"]["secondary_context"]


def test_relationship_jaimini_bridge_uses_public_formalization_as_context_only_when_marriage_gate_is_open_but_label_support_missing() -> None:
    result = _base_relationship_result()
    del result["modules"]["vivah_saham"]
    del result["modules"]["dasa_convergence"]
    result["modules"]["external_activation"] = {
        "evidence_ledger": [
            {
                "source": "vedastro_service_adapter_candidate",
                "operation": "range_scan",
                "domain": "marriage",
                "event_id": "public_relationship_window",
                "signal_key": "public_relationship_window",
                "score": 78,
            }
        ]
    }
    result["modules"]["synastry"] = {
        "total_score": 28.0,
        "max_score": 36.0,
        "is_approved": True,
        "additional_kutas": {
            "Mahendra": "good",
            "Vedha": "good",
            "Rajju": {"result": "good", "group": None, "effect": ""},
        },
    }

    strict = _collect_strict_evidence("relationship", result)

    assert strict["event_judgement"]["dominant_label"] is None
    assert "jaimini_support" in strict["event_judgement"]["secondary_context"]
    assert "external_activation_support" in strict["event_judgement"]["secondary_context"]
    assert "synastry_support" in strict["event_judgement"]["secondary_context"]
    assert "public_formalization_candidate" in strict["event_judgement"]["secondary_context"]


def test_relationship_argala_bridge_uses_seventh_house_as_modifier_only() -> None:
    result = _base_relationship_result()

    strict = _collect_strict_evidence("relationship", result)

    assert strict["present_evidence"]["argala_support"] == {
        "level": "obstructive",
        "target_house": 7,
        "source": "argala_house_bridge_v1",
        "signals": ["virodhargala_obstruction"],
        "raw": {
            "net_result": "obstructed",
            "argala_count": 1,
            "virodhargala_count": 2,
        },
    }
    assert strict["event_judgement"]["dominant_label"] == "legal_marriage"
    assert "virodhargala_obstruction" in strict["event_judgement"]["secondary_context"]


def test_relationship_collects_vedastro_range_scan_as_external_activation_context() -> None:
    result = _base_relationship_result()
    result["modules"]["external_activation"] = {
        "evidence_ledger": [
            {
                "source": "vedastro_service_adapter_candidate",
                "operation": "range_scan",
                "domain": "marriage",
                "event_id": "jupiter_7h_window",
                "score": 72,
            }
        ]
    }

    strict = _collect_strict_evidence("relationship", result)

    assert strict["present_evidence"]["external_activation"]["level"] == "moderate"
    assert strict["present_evidence"]["external_activation"]["source"] == "vedastro_service_adapter_candidate"
    assert "external_activation_support" in strict["event_judgement"]["secondary_context"]


def test_relationship_synastry_bridge_adds_context_and_small_score_bump_without_overriding_label_gate() -> None:
    base = _collect_strict_evidence("relationship", _base_relationship_result())
    result = _base_relationship_result()
    result["modules"]["synastry"] = {
        "total_score": 29.0,
        "max_score": 36.0,
        "is_approved": True,
        "additional_kutas": {
            "Mahendra": "good",
            "StreeDeergha": "good",
            "Vedha": "good",
            "Rajju": {"result": "good", "group": None, "effect": ""},
            "BadConstellations": "good",
        },
    }

    strict = _collect_strict_evidence("relationship", result)

    assert strict["present_evidence"]["synastry_relationship_support"] == {
        "level": "supportive",
        "source": "synastry_relationship_bridge_v1",
        "signals": [
            "ashtakoot_approved",
            "ashtakoot_high_score",
            "mahendra_support",
            "stree_deergha_support",
            "vedha_clean",
            "rajju_clean",
            "bad_constellations_clean",
            "kuta_exception_clean",
        ],
        "total_score": 29.0,
        "approved": True,
    }
    assert strict["event_judgement"]["dominant_label"] == "legal_marriage"
    assert strict["event_judgement"]["score"] == base["event_judgement"]["score"] + 5
    assert "synastry_support" in strict["event_judgement"]["secondary_context"]


def test_relationship_synastry_bridge_cannot_lift_label_when_core_marriage_layers_are_missing() -> None:
    result = _base_relationship_result()
    del result["modules"]["varga_full"]["D9_Navamsa"]
    del result["modules"]["special_lagnas"]["Upapada_Lagna"]
    result["modules"]["synastry"] = {
        "total_score": 31.0,
        "is_approved": True,
        "additional_kutas": {
            "Vedha": "good",
            "Rajju": {"result": "good"},
            "BadConstellations": "good",
        },
    }

    strict = _collect_strict_evidence("relationship", result)

    assert strict["present_evidence"]["synastry_relationship_support"]["level"] == "supportive"
    assert strict["event_judgement"]["dominant_label"] is None
    assert "synastry_support" in strict["event_judgement"]["secondary_context"]
    assert "d9_navamsa" in strict["missing_evidence"]
    assert "upapada_lagna" in strict["missing_evidence"]


def test_relationship_synastry_bridge_understands_nested_bad_constellations_and_exception_mitigation() -> None:
    result = _base_relationship_result()
    result["modules"]["synastry"] = {
        "total_score": 18.0,
        "max_score": 36.0,
        "is_approved": True,
        "exceptions": ["Nadi Dosha mitigated by good Bhakoot and Rajju."],
        "additional_kutas": {
            "Mahendra": "good",
            "StreeDeergha": "good",
            "Vedha": "good",
            "Rajju": {"result": "good", "group": None, "effect": ""},
            "BadConstellations": {"result": "good", "issues": []},
        },
    }

    strict = _collect_strict_evidence("relationship", result)

    assert strict["present_evidence"]["synastry_relationship_support"] == {
        "level": "moderate",
        "source": "synastry_relationship_bridge_v1",
        "signals": [
            "ashtakoot_approved",
            "exception_mitigated_match",
            "mahendra_support",
            "stree_deergha_support",
            "vedha_clean",
            "rajju_clean",
            "bad_constellations_clean",
            "kuta_exception_clean",
        ],
        "total_score": 18.0,
        "approved": True,
    }
    assert "synastry_support" in strict["event_judgement"]["secondary_context"]
    assert "synastry_compatibility_support" in strict["event_judgement"]["secondary_context"]
    assert "synastry_protective_kuta_support" in strict["event_judgement"]["secondary_context"]
    assert "synastry_exception_mitigated" in strict["event_judgement"]["secondary_context"]
    assert "synastry_kuta_exception_clean" in strict["event_judgement"]["secondary_context"]
    assert "mahendra_support" in strict["event_judgement"]["secondary_context"]
    assert "stree_deergha_support" in strict["event_judgement"]["secondary_context"]
    assert "vedha_clean" in strict["event_judgement"]["secondary_context"]
    assert "rajju_clean" in strict["event_judgement"]["secondary_context"]
    assert "bad_constellations_clean" in strict["event_judgement"]["secondary_context"]


def test_relationship_synastry_exception_alone_cannot_create_false_lift_or_clean_kuta_context() -> None:
    result = _base_relationship_result()
    del result["modules"]["varga_full"]["D9_Navamsa"]
    del result["modules"]["special_lagnas"]["Upapada_Lagna"]
    del result["modules"]["vivah_saham"]
    del result["modules"]["narayana_dasha"]
    result["modules"]["synastry"] = {
        "total_score": 14.0,
        "max_score": 36.0,
        "is_approved": False,
        "exceptions": ["Nadi exception discussed but not fully mitigated."],
        "additional_kutas": {
            "Mahendra": "good",
            "StreeDeergha": "good",
            "Vedha": "bad",
            "Rajju": {"result": "bad", "group": "same", "effect": "dosha"},
            "BadConstellations": {"result": "bad", "issues": ["vedha clash"]},
        },
    }

    strict = _collect_strict_evidence("relationship", result)

    assert strict["present_evidence"]["synastry_relationship_support"] == {
        "level": "none",
        "source": "synastry_relationship_bridge_v1",
        "signals": [
            "exception_mitigated_match",
            "mahendra_support",
            "stree_deergha_support",
        ],
        "total_score": 14.0,
        "approved": False,
    }
    assert strict["event_judgement"]["dominant_label"] is None
    assert "synastry_support" not in strict["event_judgement"]["secondary_context"]
    assert "synastry_compatibility_support" not in strict["event_judgement"]["secondary_context"]
    assert "synastry_protective_kuta_support" not in strict["event_judgement"]["secondary_context"]
    assert "synastry_exception_mitigated" not in strict["event_judgement"]["secondary_context"]
    assert "synastry_kuta_exception_clean" not in strict["event_judgement"]["secondary_context"]
    assert "mahendra_support" not in strict["event_judgement"]["secondary_context"]
    assert "rajju_clean" not in strict["event_judgement"]["secondary_context"]


def test_relationship_good_kutas_cannot_override_weak_core_marriage_promise() -> None:
    result = _base_relationship_result()
    del result["modules"]["vivah_saham"]
    del result["modules"]["dasa_convergence"]
    result["modules"]["jaimini"] = {
        "darakaraka": {"planet": "Venus", "house": 3},
    }
    result["modules"]["synastry"] = {
        "total_score": 31.0,
        "max_score": 36.0,
        "is_approved": True,
        "additional_kutas": {
            "Mahendra": "good",
            "StreeDeergha": "good",
            "Vedha": "good",
            "Rajju": {"result": "good", "group": None, "effect": ""},
            "BadConstellations": {"result": "good", "issues": []},
        },
    }

    strict = _collect_strict_evidence("relationship", result)

    assert strict["present_evidence"]["jaimini_marriage_support"] == {
        "level": "weak",
        "signals": ["darakaraka_active"],
        "source": "jaimini_bridge_v1",
    }
    assert strict["present_evidence"]["synastry_relationship_support"]["level"] == "supportive"
    assert strict["event_judgement"]["dominant_label"] is None
    assert "synastry_support" in strict["event_judgement"]["secondary_context"]
    assert "synastry_compatibility_support" in strict["event_judgement"]["secondary_context"]
    assert "synastry_protective_kuta_support" in strict["event_judgement"]["secondary_context"]
    assert "jaimini_support" not in strict["event_judgement"]["secondary_context"]


def test_relationship_protective_kutas_do_not_block_confidence_downgrade_when_timing_layers_conflict() -> None:
    result = _base_relationship_result()
    result["modules"]["synastry"] = {
        "total_score": 31.0,
        "max_score": 36.0,
        "is_approved": True,
        "additional_kutas": {
            "Mahendra": "good",
            "StreeDeergha": "good",
            "Vedha": "good",
            "Rajju": {"result": "good", "group": None, "effect": ""},
            "BadConstellations": {"result": "good", "issues": []},
        },
    }
    result["modules"]["external_activation"] = {
        "evidence_ledger": [
            {
                "source": "vedastro_service_adapter_candidate",
                "operation": "range_scan",
                "domain": "career",
                "event_id": "career_window_only",
                "signal_key": "career_only_external_window",
                "score": 74,
            }
        ]
    }
    result["modules"]["dasa_convergence"] = {
        "domain_activations": {
            "career_status": {"convergence_level": "L4", "probability": "70-85%"}
        }
    }

    strict = _collect_strict_evidence("relationship", result)

    assert "synastry_protective_kuta_support" in strict["event_judgement"]["secondary_context"]
    assert strict["event_judgement"]["dominant_label"] == "legal_marriage"
    assert strict["confidence_cap"] == "low"


def test_relationship_narrative_payload_turns_synastry_taxonomy_into_user_readable_boundary() -> None:
    strict = _collect_strict_evidence("relationship", _base_relationship_result())
    strict["present_evidence"]["synastry_relationship_support"] = {
        "level": "supportive",
        "source": "synastry_relationship_bridge_v1",
        "signals": [
            "ashtakoot_approved",
            "mahendra_support",
            "stree_deergha_support",
            "vedha_clean",
            "rajju_clean",
        ],
        "total_score": 29.0,
        "approved": True,
    }
    strict["event_judgement"]["secondary_context"] = strict["event_judgement"]["secondary_context"] + [
        "synastry_support",
        "synastry_compatibility_support",
        "synastry_protective_kuta_support",
    ]
    strict["confidence_cap"] = "low"

    payload = jyotish_engine._build_relationship_narrative_payload(strict)

    assert "婚恋" in payload["headline"]
    assert any("合盘" in item for item in payload["strengths"])
    assert any("protective kuta" in item.lower() for item in payload["strengths"])
    assert any("dual dasha" in item.lower() for item in payload["risks"])
    assert any("legal_marriage" in item for item in payload["boundaries"])
    assert "D9" in payload["markdown"]
    assert "dual dasha" in payload["markdown"]


def test_relationship_narrative_payload_exposes_public_formalization_candidate_as_context_only() -> None:
    strict = _collect_strict_evidence("relationship", _base_relationship_result())
    strict["event_judgement"]["dominant_label"] = None
    strict["event_judgement"]["secondary_context"] = [
        "darakaraka_active",
        "jaimini_support",
        "ul_support",
        "external_activation_support",
        "public_formalization_candidate",
    ]
    strict["present_evidence"].pop("vivah_saham", None)
    strict["present_evidence"].pop("marriage_convergence", None)
    strict["confidence_cap"] = "low"

    payload = jyotish_engine._build_relationship_narrative_payload(strict)

    assert any("public_formalization" in item for item in payload["strengths"])
    assert any("不等于法律婚姻" in item for item in payload["boundaries"])
    assert "public_formalization_candidate" in payload["markdown"]
    assert "legal_marriage" in payload["markdown"]


def test_relationship_narrative_payload_for_public_formalization_candidate_with_timing_conflict_explicitly_warns_not_to_misread_as_near_marriage() -> None:
    strict = _collect_strict_evidence("relationship", _base_relationship_result())
    strict["event_judgement"]["dominant_label"] = None
    strict["event_judgement"]["secondary_context"] = [
        "darakaraka_active",
        "jaimini_support",
        "ul_support",
        "external_activation_support",
        "public_formalization_candidate",
    ]
    strict["present_evidence"].pop("vivah_saham", None)
    strict["present_evidence"].pop("marriage_convergence", None)
    strict["confidence_cap"] = "low"

    payload = jyotish_engine._build_relationship_narrative_payload(strict)

    assert any("public_formalization_candidate" in item for item in payload["strengths"])
    assert any("不能误读成接近结婚" in item for item in payload["risks"])
    assert any("不等于法律婚姻" in item for item in payload["boundaries"])
    assert "不能误读成接近结婚" in payload["markdown"]


def test_relationship_narrative_payload_does_not_translate_public_formalization_candidate_plus_synastry_support_plus_weak_core_promise_into_marriage_approach() -> None:
    strict = _collect_strict_evidence("relationship", _base_relationship_result())
    strict["event_judgement"]["dominant_label"] = None
    strict["event_judgement"]["secondary_context"] = [
        "darakaraka_active",
        "ul_support",
        "synastry_support",
        "synastry_compatibility_support",
        "public_formalization_candidate",
    ]
    strict["present_evidence"]["jaimini_marriage_support"] = {
        "level": "weak",
        "signals": ["darakaraka_active"],
        "source": "jaimini_bridge_v1",
    }
    strict["present_evidence"].pop("vivah_saham", None)
    strict["present_evidence"].pop("marriage_convergence", None)
    strict["confidence_cap"] = "low"

    payload = jyotish_engine._build_relationship_narrative_payload(strict)

    assert any("合盘支持已进入婚恋主链" in item for item in payload["strengths"])
    assert any("公开化/关系可见度候选" in item for item in payload["strengths"])
    assert any("不能误读成接近结婚" in item for item in payload["risks"])
    assert any("不得越权抬升 legal_marriage" in item for item in payload["boundaries"])
    assert "public_formalization_candidate" in payload["markdown"]
    assert "legal_marriage" in payload["markdown"]


def test_relationship_dignity_guardrail_ignores_non_relevant_planets() -> None:
    result = _base_relationship_result()
    result["modules"]["chart"] = {
        "ascendant": {"sign": "Leo"},
        "planets": {
            "Mars": {"status": "落陷取消(Neecha Bhanga)"},
            "Mercury": {"status": "极敌(Great Enemy)"},
            "Venus": {"status": "中性(Neutral)"},
            "Jupiter": {"status": "中性(Neutral)"},
        },
    }

    strict = _collect_strict_evidence("relationship", result)

    assert strict["present_evidence"]["dignity_guardrail"]["score_delta"] == 0
    assert strict["event_judgement"]["dominant_label"] == "legal_marriage"
    assert "dignity_supportive_recovery" not in strict["event_judgement"]["secondary_context"]
    assert "dignity_high_friction" not in strict["event_judgement"]["secondary_context"]


def test_relationship_dignity_guardrail_uses_relevant_planets_only() -> None:
    result = _base_relationship_result()
    result["modules"]["chart"] = {
        "ascendant": {"sign": "Aries"},
        "planets": {
            "Venus": {"status": "落陷取消(Neecha Bhanga)"},
            "Jupiter": {"status": "中性(Neutral)"},
            "Saturn": {"status": "极敌(Great Enemy)"},
        },
    }

    strict = _collect_strict_evidence("relationship", result)

    assert strict["present_evidence"]["dignity_guardrail"]["score_delta"] == 5
    assert "dignity_supportive_recovery" in strict["event_judgement"]["secondary_context"]


def test_relationship_dignity_guardrail_treats_great_friend_on_relevant_planet_as_supportive_context() -> None:
    result = _base_relationship_result()
    result["modules"]["chart"] = {
        "ascendant": {"sign": "Leo"},
        "planets": {
            "Venus": {"status": "极友(Great Friend)"},
            "Jupiter": {"status": "中性(Neutral)"},
            "Saturn": {"status": "中性(Neutral)"},
        },
    }

    strict = _collect_strict_evidence("relationship", result)

    assert strict["present_evidence"]["dignity_guardrail"]["status"] == "caution"
    assert strict["present_evidence"]["dignity_guardrail"]["score_delta"] == 3
    assert "dignity_supportive_friendship" in strict["event_judgement"]["secondary_context"]


def test_relationship_caps_confidence_when_provided_shadbala_components_are_incomplete() -> None:
    result = _base_relationship_result()
    result["modules"]["dasa_convergence"]["domain_activations"]["marriage_partnership"] = {
        "convergence_level": "L4",
        "probability": "70-85%",
    }
    result["modules"]["shadbala"] = {"planets": {"Venus": {"total_rupa": 8.2}}}

    strict = _collect_strict_evidence("relationship", result)

    assert strict["present_evidence"]["shadbala_component_audit"] == {
        "status": "incomplete",
        "source": "shadbala.planets",
        "required_components": ["sthana", "dig", "kala", "chesta", "naisargika", "drik"],
        "missing": {"Venus": ["sthana", "dig", "kala", "chesta", "naisargika", "drik"]},
    }
    assert strict["confidence_cap"] == "low"
    assert "shadbala_component_gap" in strict["event_judgement"]["secondary_context"]


def test_relationship_accepts_complete_shadbala_components_without_cap_penalty() -> None:
    result = _base_relationship_result()
    result["modules"]["dasa_convergence"]["domain_activations"]["marriage_partnership"] = {
        "convergence_level": "L4",
        "probability": "70-85%",
    }
    result["modules"]["shadbala"] = {
        "planets": {
            "Venus": {
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

    strict = _collect_strict_evidence("relationship", result)

    assert strict["present_evidence"]["shadbala_component_audit"]["status"] == "complete"
    assert strict["confidence_cap"] == "medium-high"
    assert "shadbala_component_gap" not in strict["event_judgement"]["secondary_context"]
