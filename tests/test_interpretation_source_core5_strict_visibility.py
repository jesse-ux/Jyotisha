#!/usr/bin/env python3
"""Strict workflow visibility tests for the first core promoted references."""

from __future__ import annotations

from mcp_server import _collect_strict_evidence, _existing_interpretation_source_pack


CORE5_SOURCE_REFS = [
    "references/prediction-boundary-protocol.md",
    "references/event_judgment_skeleton.md",
    "references/planetary-dignity-complete-reference.md",
    "references/retrograde-combustion-war-guide.md",
    "references/transit-multi-reference-guide.md",
]


def _base_modules() -> dict:
    return {
        "modules": {
            "chart": {
                "ascendant": {"sign": "Leo"},
                "planets": {
                    "Sun": {"status": "中性(Neutral)"},
                    "Moon": {"status": "中性(Neutral)"},
                    "Mercury": {"status": "中性(Neutral)"},
                    "Venus": {"status": "中性(Neutral)"},
                    "Jupiter": {"status": "中性(Neutral)"},
                    "Saturn": {"status": "中性(Neutral)"},
                },
            },
            "varga_full": {
                "D10_Dasamsa": {"summary": "career varga present"},
                "D9_Navamsha": {"summary": "relationship varga present"},
                "D2_Hora": {"summary": "wealth varga present"},
                "D11_Rudramsha": {"summary": "gains varga present"},
            },
            "special_lagnas": {
                "A10_Karma_Pada": {"sign": "Capricorn", "lord": "Saturn"},
                "Upapada_Lagna": {"sign": "Libra", "lord": "Venus"},
            },
            "jaimini": {
                "karakas": {
                    "Amatyakaraka": {"planet": "Mercury"},
                    "Atmakaraka": {"planet": "Sun"},
                    "Darakaraka": {"planet": "Venus"},
                },
                "karakamsha": {"karakamsha_sign": "Leo", "karakamsha_lord": "Sun"},
            },
            "dasha": {"current_dasha": {"mahadasha": "Mercury", "antardasha": "Sun"}},
            "narayana_dasha": {"current_dasha": {"sign": "Capricorn", "lord": "Saturn"}},
            "dasa_convergence": {
                "domain_activations": {
                    "career_status": {"convergence_level": "L2", "probability": "35-50%"},
                    "marriage_relationship": {"convergence_level": "L2", "probability": "35-50%"},
                    "wealth_income": {"convergence_level": "L2", "probability": "35-50%"},
                }
            },
        }
    }


def test_core5_sources_are_wired_into_interpretation_source_pack() -> None:
    source_pack = _existing_interpretation_source_pack()

    assert source_pack["core_rule_source_layer"]["status"] == "available"
    assert source_pack["core_rule_source_layer"]["promotion_batch"] == "priority1_batch1_core5"
    assert source_pack["core_rule_source_layer"]["source_refs"] == CORE5_SOURCE_REFS
    for path in CORE5_SOURCE_REFS:
        assert path in source_pack["source_refs"]

    inventory = source_pack["interpretation_source_inventory"]
    assert inventory["layers"]["core_rule_sources"]["source_refs"] == CORE5_SOURCE_REFS
    assert inventory["layers"]["core_rule_sources"]["promotion_status"] == "primary_truth_candidate"


def test_core5_sources_are_visible_to_all_strict_fortune_workflows() -> None:
    for route in ["career", "relationship", "finance"]:
        strict = _collect_strict_evidence(route, _base_modules())
        source_pack = strict["present_evidence"]["interpretation_source_pack"]
        audit = strict["technique_audit_summary"]["interpretation_source_pack"]

        assert source_pack["core_rule_source_layer"]["source_refs"] == CORE5_SOURCE_REFS
        assert audit["core_rule_source_refs"] == CORE5_SOURCE_REFS
        assert audit["used"] is True
        for path in CORE5_SOURCE_REFS:
            assert path in audit["source_refs"]
