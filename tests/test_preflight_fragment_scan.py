#!/usr/bin/env python3
"""Regression tests for preflight fragment scan discipline."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_preflight_fragment_scan_reports_authority_layers_and_risk_buckets() -> None:
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
    report = json.loads(completed.stdout)

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
    assert findings["high_value_unpromoted_count"] >= 1
    assert findings["redundant_or_mirror_count"] >= 1
    assert findings["workspace_residue_count"] >= 1
    assert findings["real_capability_risk_count"] >= 1

    categories = {item["category"] for item in report["high_value_unpromoted"]}
    assert "repo_local_draft" in categories or "external_work_brain" in categories

    mirror_paths = [item["path"] for item in report["redundant_or_mirror"]]
    assert any(".workbuddy/skills/jyotish-vedic-astrology" in path for path in mirror_paths)

    risk_ids = {item["id"] for item in report["real_capability_risks"]}
    assert "external_oracle_not_closed" in risk_ids
    assert "historical_event_accuracy_not_proven" in risk_ids


def test_preflight_fragment_scan_preserves_audit_capability_and_oracle_boundaries() -> None:
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
    report = json.loads(completed.stdout)

    audit = report["upstream_audits"]
    assert audit["capability_audit"]["valid"] is True
    assert audit["capability_audit"]["technique_count"] >= 89
    assert audit["fragment_audit"]["valid"] is True
    assert audit["fragment_audit"]["candidate_count"] == 0

    oracle_boundary = report["real_capability_boundary"]["oracle_boundary"]
    assert oracle_boundary["scope"] == "external_oracle_boundary_audit"
    assert oracle_boundary["production_tuning_recommended"] is False
    assert oracle_boundary["dasha_cases"] >= 1
    assert oracle_boundary["shadbala_cases"] >= 1
    assert oracle_boundary["longitude_cases"] >= 1

    cleanup_map = report["cleanup_map"]
    assert cleanup_map["exists"] is True
    assert cleanup_map["path"].endswith("repo_cleanup_promotion_map_2026_07_01.md")
    assert "docs/research/local_drafts/2026-06" in cleanup_map["focus_layers"]
    assert any(".gemini/antigravity-ide/brain" in layer for layer in cleanup_map["focus_layers"])
    assert any(".workbuddy/skills/jyotish-vedic-astrology" in layer for layer in cleanup_map["focus_layers"])


def test_preflight_fragment_scan_emits_repo_cleanup_priorities() -> None:
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
    report = json.loads(completed.stdout)

    priorities = report["cleanup_priorities"]
    assert len(priorities) >= 2
    assert all(item["id"] != "remove_mirror_runtime_dependency" for item in priorities)
    assert all("validate_bphs_invariants.py" not in str(item.get("evidence", {})) for item in priorities)
    assert any(item["id"] == "triage_workspace_residue" for item in priorities)
    assert any(item["id"] == "promote_or_archive_high_value_drafts" for item in priorities)


def test_preflight_fragment_scan_excludes_promoted_first_five_drafts_from_unpromoted_pool() -> None:
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
    report = json.loads(completed.stdout)
    unpromoted_paths = {item["path"] for item in report["high_value_unpromoted"]}

    blocked_names = {
        "antigravity_round36_tajika_sahams_external_closure_pack_2026_06_26.md",
        "antigravity_round37_dasha_external_oracle_shortest_closure_board_2026_06_26.md",
        "antigravity_round37_shadbala_absolute_value_frontier_board_2026_06_26.md",
        "antigravity_round39_yogi_wealth_bridge_audit_2026_06_28.md",
        "three_fronts_skill_depth_audit_2026_06_26.md",
    }
    assert all(not any(name in path for path in unpromoted_paths) for name in blocked_names)


def test_preflight_fragment_scan_excludes_promoted_third_batch_drafts_from_unpromoted_pool() -> None:
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
    report = json.loads(completed.stdout)
    unpromoted_paths = {item["path"] for item in report["high_value_unpromoted"]}

    blocked_names = {
        "antigravity_round36_asc_degree_yogi_tight_orb_wealth_pack_2026_06_26.md",
        "antigravity_round37_tajika_sahams_annual_closure_board_2026_06_26.md",
        "antigravity_round38_whole_machine_fragment_reuse_sixth_pass_2026_06_26.md",
        "antigravity_round40_shadbala_absolute_authority_ladder_2026_06_27.md",
        "antigravity_round40_tajika_annual_second_wave_board_2026_06_27.md",
    }
    assert all(not any(name in path for path in unpromoted_paths) for name in blocked_names)


def test_preflight_fragment_scan_excludes_promoted_fourth_batch_drafts_from_unpromoted_pool() -> None:
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
    report = json.loads(completed.stdout)
    unpromoted_paths = {item["path"] for item in report["high_value_unpromoted"]}

    blocked_names = {
        "antigravity_round40_whole_machine_fragment_reuse_shortlist_2026_06_27.md",
        "dasha_accuracy_closure_status_2026_06_26.md",
        "dasha_code_only_priority_rerank_2026_06_26.md",
        "skill_fragment_map_and_source_of_truth_2026_06_26.md",
        "skill_truth_conflict_matrix_2026_06_26.md",
    }
    assert all(not any(name in path for path in unpromoted_paths) for name in blocked_names)
