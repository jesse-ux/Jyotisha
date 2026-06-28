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
