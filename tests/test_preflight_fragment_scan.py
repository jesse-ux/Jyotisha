#!/usr/bin/env python3
"""Regression tests for preflight fragment scan discipline."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def report() -> dict:
    cached_report = os.environ.get("PREFLIGHT_FRAGMENT_SCAN_REPORT")
    if cached_report and Path(cached_report).exists():
        return json.loads(Path(cached_report).read_text(encoding="utf-8"))
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/preflight_fragment_scan.py",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    return json.loads(completed.stdout)


def test_preflight_fragment_scan_reports_authority_layers_and_risk_buckets(report: dict) -> None:
    assert report["scope"] == "preflight_fragment_scan"
    assert report["summary"]["authority_layers_scanned"] == 4
    assert report["summary"]["production_truth_layer"] == "main_repo_truth"
    assert report["summary"]["real_capability_status"] in {
        "engineering_surfaces_covered_but_external_accuracy_not_closed",
        "needs_manual_review",
    }

    layers = report["layers"]
    assert layers["main_repo_truth"]["status"] == "authoritative"
    assert layers["repo_local_drafts"]["status"] == "draft_reference_only"
    assert layers["external_work_brain"]["status"] == "recovery_reference_only"
    assert layers["distribution_mirror"]["status"] == "mirror_do_not_reverse_sync"

    findings = report["findings"]
    assert findings["high_value_unpromoted_count"] == len(report["high_value_unpromoted"])
    assert findings["redundant_or_mirror_count"] >= 1
    assert findings["workspace_residue_count"] >= 0
    assert findings["real_capability_risk_count"] >= 1

    categories = {item["category"] for item in report["high_value_unpromoted"]}
    if categories:
        assert "repo_local_draft" in categories or "external_work_brain" in categories

    mirror_paths = [item["path"] for item in report["redundant_or_mirror"]]
    assert any(".workbuddy/skills/jyotish-vedic-astrology" in path for path in mirror_paths)

    risk_ids = {item["id"] for item in report["real_capability_risks"]}
    assert "external_oracle_not_closed" in risk_ids
    assert "historical_event_accuracy_not_proven" in risk_ids


def test_preflight_fragment_scan_preserves_audit_capability_and_oracle_boundaries(report: dict) -> None:
    audit = report["upstream_audits"]
    assert audit["capability_audit"]["valid"] is True
    assert audit["capability_audit"]["technique_count"] >= 89
    assert audit["fragment_audit"]["valid"] is True
    assert audit["fragment_audit"]["candidate_count"] >= (
        report["summary"]["high_value_unpromoted_count"]
        + report["summary"]["workspace_residue_count"]
    )
    assert audit["fragment_audit"]["workspace_residue_count"] == report["summary"]["workspace_residue_count"]

    oracle_boundary = report["real_capability_boundary"]["oracle_boundary"]
    assert oracle_boundary["scope"] == "external_oracle_boundary_audit"
    assert oracle_boundary["production_tuning_recommended"] is False
    assert oracle_boundary["dasha_cases"] == 0
    assert oracle_boundary["shadbala_cases"] == 0
    assert oracle_boundary["longitude_cases"] == 0

    cleanup_map = report["cleanup_map"]
    assert cleanup_map["exists"] is True
    assert cleanup_map["path"].endswith("repo_cleanup_promotion_map_2026_07_01.md")
    assert "docs/research/local_drafts/2026-06" in cleanup_map["focus_layers"]
    assert any(".gemini/antigravity-ide/brain" in layer for layer in cleanup_map["focus_layers"])
    assert any(".workbuddy/skills/jyotish-vedic-astrology" in layer for layer in cleanup_map["focus_layers"])


def test_preflight_fragment_scan_emits_repo_cleanup_priorities(report: dict) -> None:
    priorities = report["cleanup_priorities"]
    assert len(priorities) >= 2
    assert all(item["id"] != "remove_mirror_runtime_dependency" for item in priorities)
    assert all("validate_bphs_invariants.py" not in str(item.get("evidence", {})) for item in priorities)
    assert any(item["id"] == "triage_workspace_residue" for item in priorities)
    assert any(item["id"] == "promote_or_archive_high_value_drafts" for item in priorities)


def test_preflight_fragment_scan_links_pre_work_governance(report: dict) -> None:
    governance = report["governance"]
    assert governance["pre_work_error_ledger"]["exists"] is True
    assert governance["pre_work_error_ledger"]["path"].endswith("pre_work_error_ledger.md")
    assert governance["latest_fragment_sweep"]["exists"] is True
    assert governance["latest_fragment_sweep"]["remote_ref_parity"] == "blocked_until_git_ls_remote_succeeds"
    assert governance["prior_fragment_sweep"]["exists"] is True
    assert "python3 -m pytest" in governance["acceptance_command"]
    assert "tests/test_remote_repo_visibility_check.py" in governance["acceptance_command"]
    assert "tests/test_pre_work_check.py" in governance["acceptance_command"]
