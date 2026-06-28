#!/usr/bin/env python3
"""Regression tests for functional benefic/malefic strict evidence integration."""

from __future__ import annotations

import json
import subprocess
import sys

from mcp_server import _collect_strict_evidence
from scripts.functional_benefics import derive_functional_benefic_malefic


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


def test_functional_benefic_module_calculates_lagna_roles_without_planets() -> None:
    functional = derive_functional_benefic_malefic("Leo")

    assert functional["status"] == "used"
    assert functional["ascendant"] == "Leo"
    assert functional["owned_houses"]["Sun"] == [1]
    assert functional["owned_houses"]["Venus"] == [3, 10]
    assert "Sun" in functional["functional_benefics"]
    assert "Venus" in functional["functional_malefics"]
    assert functional["source"] == "strict_functional_benefic_malefic_v1"


def test_relationship_functional_layer_uses_ascendant_even_when_planets_missing() -> None:
    result = _base_relationship_result()
    result["modules"]["chart"] = {"ascendant": {"sign": "Leo"}}

    strict = _collect_strict_evidence("relationship", result)

    functional = strict["present_evidence"]["functional_benefic_malefic"]
    assert functional["status"] == "used"
    assert functional["ascendant"] == "Leo"
    assert "Sun" in functional["functional_benefics"]
    assert "Venus" in functional["functional_malefics"]
    assert "functional_benefic_malefic_used" in strict["event_judgement"]["secondary_context"]


def test_oracle_functional_benefics_cli_exposes_json_contract() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/oracle_functional_benefics.py",
            "--ascendant",
            "Leo",
            "--format",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout)

    assert report["status"] == "used"
    assert report["ascendant"] == "Leo"
    assert "Sun" in report["functional_benefics"]
    assert "Venus" in report["functional_malefics"]
    assert "Mars" in report["yogakarakas"]
    assert report["source"] == "strict_functional_benefic_malefic_v1"
