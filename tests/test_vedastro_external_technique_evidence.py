#!/usr/bin/env python3
"""VedAstro external calculation-method evidence boundary tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

from mcp_server import _collect_strict_evidence


ROOT = Path(__file__).resolve().parents[1]


def test_vedastro_adapter_declares_external_technique_evidence_policy() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/vedastro_service_adapter.py", "--print-schema"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    schema = json.loads(completed.stdout)

    assert "external_technique_request_contract" in schema
    assert "method" in schema["external_technique_request_contract"]
    assert "api_endpoint" in schema["external_technique_request_contract"]
    assert schema["external_technique_adjudicator_policy"] == {
        "role": "external_technique_evidence",
        "can_change_score": False,
        "can_set_dominant_label": False,
        "can_set_payout_label": False,
        "allowed_destinations": ["secondary_context", "technique_audit"],
    }


def test_vedastro_adapter_builds_external_technique_preview_without_network() -> None:
    env = os.environ.copy()
    env["VEDASTRO_API_ENDPOINT"] = "https://example.invalid/vedastro"
    env.pop("VEDASTRO_ENABLE_NETWORK", None)

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/vedastro_service_adapter.py",
            "--external-technique",
            "--domain",
            "wealth",
            "--method",
            "CalculateShadbala",
            "--api-endpoint",
            "Calculate/Shadbala",
            "--case",
            "beijing_first_use_demo",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
        env=env,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)

    assert report["backend"] == "vedastro_service_adapter_candidate"
    assert report["status"] == "network_execution_disabled"
    assert report["request_preview"]["operation"] == "calculation_method"
    assert report["request_preview"]["role"] == "external_technique_evidence"
    assert report["request_preview"]["domain"] == "wealth"
    assert report["request_preview"]["method"] == "CalculateShadbala"
    assert report["request_preview"]["api_endpoint"] == "Calculate/Shadbala"
    assert report["adjudicator_policy"]["can_change_score"] is False
    assert report["adjudicator_policy"]["can_set_dominant_label"] is False
    assert report["adjudicator_policy"]["can_set_payout_label"] is False


def _finance_modules() -> dict:
    return {
        "varga_full": {
            "D2_Hora": {"available": True},
            "D10_Dasamsa": {"available": True},
        },
        "shadbala": {
            "planets": {
                "Jupiter": {
                    "sthana_bala": 1,
                    "dig_bala": 1,
                    "kala_bala": 1,
                    "chesta_bala": 1,
                    "naisargika_bala": 1,
                    "drik_bala": 1,
                }
            }
        },
        "ashtakavarga": {
            "house_scores": {
                "2": 28,
                "11": 29,
            }
        },
        "dasha": {
            "current_dasha": {
                "mahadasha": "Saturn",
                "antardasha": "Mercury",
            }
        },
        "narayana_dasha": {
            "current_dasha": {
                "sign": "Gemini",
                "lord": "Mercury",
            }
        },
        "dasa_convergence": {
            "domain_activations": {
                "wealth_family": {
                    "convergence_level": "L1",
                    "probability": "+15-20%",
                }
            }
        },
        "chart": {
            "ascendant": {
                "sign": "Leo",
            }
        },
    }


def test_strict_workflow_uses_external_technique_as_context_only() -> None:
    base_result = {"modules": _finance_modules()}
    with_external = {"modules": deepcopy(base_result["modules"])}
    with_external["modules"]["external_technique_evidence"] = {
        "evidence_ledger": [
            {
                "source": "vedastro_service_adapter_candidate",
                "operation": "calculation_method",
                "role": "external_technique_evidence",
                "domain": "wealth",
                "method": "CalculateShadbala",
                "api_endpoint": "Calculate/Shadbala",
                "status": "ok",
                "summary": "VedAstro Shadbala node returned as external evidence.",
            }
        ]
    }

    base = _collect_strict_evidence("finance", base_result)
    strict = _collect_strict_evidence("finance", with_external)

    base_judgement = base["event_judgement"]
    judgement = strict["event_judgement"]

    assert strict["present_evidence"]["external_technique_evidence"]["level"] == "context_only"
    assert strict["present_evidence"]["external_technique_evidence"]["methods"] == ["CalculateShadbala"]
    assert "external_technique_evidence" in judgement["secondary_context"]
    assert {
        "technique": "VedAstro EventsAtRange / 596+ Calculator Radar",
        "status": "blocked",
        "role": "required_external_timing_radar",
        "effect": "confidence_boundary_only_no_score_or_label_lift",
    } in strict["technique_audit"]
    assert {
        "technique": "VedAstro External Technique Evidence",
        "status": "used",
        "role": "external_evidence_only",
        "methods": ["CalculateShadbala"],
        "effect": "secondary_context_only_no_score_or_label_lift",
    } in strict["technique_audit"]
    assert judgement["score"] == base_judgement["score"]
    assert judgement["dominant_label"] == base_judgement["dominant_label"]
    assert judgement["payout_label"] == base_judgement["payout_label"]


def test_strict_workflow_requires_vedastro_range_scan_boundary_for_timing_routes() -> None:
    strict = _collect_strict_evidence("finance", {"modules": _finance_modules()})

    assert strict["present_evidence"]["external_activation"]["level"] == "missing_required_external_radar"
    assert strict["present_evidence"]["external_activation"]["source"] == "vedastro_service_adapter_candidate"
    assert strict["present_evidence"]["external_activation"]["required"] is True
    assert "vedastro_range_scan_missing" in strict["event_judgement"]["secondary_context"]
    assert {
        "technique": "VedAstro EventsAtRange / 596+ Calculator Radar",
        "status": "blocked",
        "role": "required_external_timing_radar",
        "effect": "confidence_boundary_only_no_score_or_label_lift",
    } in strict["technique_audit"]


def test_strict_workflow_marks_vedastro_range_scan_used_without_score_or_label_override() -> None:
    base_result = {"modules": _finance_modules()}
    with_range_scan = {"modules": deepcopy(base_result["modules"])}
    with_range_scan["modules"]["external_activation"] = {
        "evidence_ledger": [
            {
                "source": "vedastro_service_adapter_candidate",
                "operation": "range_scan",
                "domain": "wealth",
                "event_id": "GocharJupiterIn11th",
                "signal_label": "Jupiter in 11th gains window",
                "score": 76,
                "tags": ["wealth", "transit"],
            }
        ]
    }

    base = _collect_strict_evidence("finance", base_result)
    strict = _collect_strict_evidence("finance", with_range_scan)

    assert strict["present_evidence"]["external_activation"]["level"] == "moderate"
    assert "external_activation_support" in strict["event_judgement"]["secondary_context"]
    assert "vedastro_range_scan_missing" not in strict["event_judgement"]["secondary_context"]
    assert any(
        row["technique"] == "VedAstro EventsAtRange / 596+ Calculator Radar"
        and row["status"] == "used"
        and row["event_count"] == 1
        for row in strict["technique_audit"]
    )
    assert strict["missing_evidence"] == ["wealth_promise_strength"]
    assert strict["event_judgement"]["score"] == base["event_judgement"]["score"]
    assert strict["event_judgement"]["dominant_label"] == base["event_judgement"]["dominant_label"]
    assert strict["event_judgement"]["payout_label"] == base["event_judgement"]["payout_label"]
