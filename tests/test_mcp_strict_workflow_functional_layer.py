#!/usr/bin/env python3
"""Regression tests for functional benefic/malefic strict evidence integration."""

from __future__ import annotations

from mcp_server import _collect_strict_evidence


def _base_relationship_result() -> dict:
    return {
        "modules": {
            "chart": {
                "ascendant": {"sign": "Leo"},
                "planets": {
                    "Sun": {"sign": "Aquarius", "house": 7},
                    "Moon": {"sign": "Taurus", "house": 10},
                    "Mars": {"sign": "Gemini", "house": 11},
                    "Mercury": {"sign": "Capricorn", "house": 6},
                    "Jupiter": {"sign": "Sagittarius", "house": 5},
                    "Venus": {"sign": "Pisces", "house": 8},
                    "Saturn": {"sign": "Libra", "house": 3},
                },
            },
            "varga_full": {"D9_Navamsa": {"summary": "ok"}},
            "special_lagnas": {"Upapada_Lagna": {"sign": "Libra", "lord": "Venus"}},
            "jaimini": {"darakaraka": {"planet": "Venus", "house": 7}},
            "vivah_saham": {"sign": "Taurus", "house": 7},
            "dasha": {"current_dasha": {"mahadasha": "Venus", "antardasha": "Moon"}},
            "narayana_dasha": {"current_dasha": {"sign": "Libra", "lord": "Venus"}},
            "dasa_convergence": {
                "domain_activations": {
                    "marriage_partnership": {"convergence_level": "L3", "probability": "50-65%"}
                }
            },
        }
    }


def test_relationship_strict_workflow_exposes_functional_benefic_malefic_layer() -> None:
    strict = _collect_strict_evidence("relationship", _base_relationship_result())

    functional = strict["present_evidence"]["functional_benefic_malefic"]
    assert functional["status"] == "used"
    assert functional["ascendant"] == "Leo"
    assert isinstance(functional["functional_benefics"], list)
    assert isinstance(functional["functional_malefics"], list)
    assert "Sun" in functional["functional_benefics"]
    assert "Venus" in functional["functional_malefics"]
    assert "functional_benefic_malefic_used" in strict["event_judgement"]["secondary_context"]

