#!/usr/bin/env python3
"""Regression tests for MCP relationship event adjudication."""

from __future__ import annotations

from mcp_server import _collect_strict_evidence


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
    ]


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
        "signals": ["ashtakoot_approved", "ashtakoot_high_score", "kuta_exception_clean"],
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
        "signals": ["ashtakoot_approved", "exception_mitigated_match", "kuta_exception_clean"],
        "total_score": 18.0,
        "approved": True,
    }
    assert "synastry_support" in strict["event_judgement"]["secondary_context"]


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
