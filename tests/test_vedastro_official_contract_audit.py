from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.vedastro_official_contract_audit import (
    REQUIRED_CONTRACT_FIELDS,
    build_audit_report,
    expected_confidence_cap,
    validate_contract,
)


ROOT = Path(__file__).resolve().parents[1]


def test_official_contract_audit_reports_all_required_fields() -> None:
    report = build_audit_report()

    assert report["scope"] == "vedastro_official_evidence_contract_audit"
    assert report["required_fields"] == REQUIRED_CONTRACT_FIELDS
    assert report["summary"]["invalid_routes"] == 0
    assert report["summary"]["confidence_cap_policy"] == "enforced"
    assert "does not prove VedAstro official raw response availability" in report["boundary"]

    for route in report["routes"]:
        assert route["valid"] is True
        assert route["missing_fields"] == []
        assert route["confidence_cap"] in {"high", "medium", "low", "blocked"}


def test_confidence_cap_policy_blocks_unbacked_official_failures() -> None:
    contract = {
        "source_priority_mode": "local_fallback_official_blocked",
        "official_primary_evidence": {"status": "blocked", "required": True},
        "local_supplemental_evidence": {"status": "missing_required_sections"},
        "fallback_used": [],
        "blocked_items": ["vedastro_official_full_snapshot"],
        "conflicts": [],
        "confidence_cap": "low",
    }

    assert expected_confidence_cap(contract) == "blocked"
    result = validate_contract("health", contract)
    assert result["valid"] is False
    assert "blocked_state_must_use_blocked_confidence_cap" in result["errors"]


def test_confidence_cap_policy_downgrades_partial_or_fallback_states() -> None:
    contract = {
        "source_priority_mode": "vedastro_official_primary_partial",
        "official_primary_evidence": {"status": "partial", "required": True},
        "local_supplemental_evidence": {"status": "missing_required_sections"},
        "fallback_used": ["local_chart_core"],
        "blocked_items": ["D2"],
        "conflicts": [],
        "confidence_cap": "medium",
    }

    assert expected_confidence_cap(contract) == "low"
    result = validate_contract("wealth", contract)
    assert result["valid"] is False
    assert "partial_or_fallback_state_must_not_exceed_low" in result["errors"]


def test_cli_emits_machine_readable_json() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/vedastro_official_contract_audit.py", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["summary"]["invalid_routes"] == 0
    assert payload["route_count"] >= 3
