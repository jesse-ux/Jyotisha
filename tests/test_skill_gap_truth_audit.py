#!/usr/bin/env python3
"""Tests for the skill-level gap truth audit."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "references" / "skill_gap_truth_registry.json"


def test_skill_gap_truth_registry_lists_hard_fronts_and_past_corrections() -> None:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))

    assert data["scope"] == "jyotish_skill_gap_truth_registry"
    assert data["public_claim_rules"]["can_claim_global_first"] is False
    assert data["public_claim_rules"]["can_claim_all_skills_complete"] is False

    hard_fronts = data["hard_fronts"]
    required_fronts = {
        "dasha_external_oracle",
        "shadbala_external_absolute_values",
        "tajika_sahams_annual_closure",
        "article_template_industrialization",
        "long_term_public_benchmark",
    }
    assert required_fronts <= set(hard_fronts)
    for front_id in required_fronts:
        front = hard_fronts[front_id]
        assert front["status"] in {
            "blocked_external_evidence",
            "active_gap",
            "active_partial_external_evidence",
            "active_target_set_closed",
        }
        assert front["priority"] in {"P0", "P1", "P2"}
        assert front["completion_standard"]
        assert front["forbidden_claims"]
        assert front["next_actions"]

    corrections = data["past_case_analysis_corrections"]
    correction_ids = {item["id"] for item in corrections}
    assert "ashtakoot_not_all_zero" in correction_ids
    assert "panchanga_not_empty" in correction_ids
    assert "covered_is_not_complete" in correction_ids
    assert "single_factor_reading_risk" in correction_ids


def test_skill_gap_truth_audit_outputs_current_truth_boundary() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/skill_gap_truth_audit.py", "--format", "json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["scope"] == "jyotish_skill_gap_truth_audit"
    assert report["valid"] is True
    assert report["summary"]["technique_count"] >= 79
    assert report["summary"]["capability_valid"] is True
    assert report["summary"]["hard_front_count"] >= 5
    assert report["public_claim"]["can_claim_global_first"] is False
    assert report["public_claim"]["can_claim_all_skills_complete"] is False
    assert report["public_claim"]["can_claim_perfect_accuracy"] is False
    assert "Dasha" in report["must_not_overclaim"][0]
    assert report["oracle_closure"]["summary"]["can_claim_global_oracle_closure"] is False
    assert report["remaining_hard_fronts"][0]["id"] == "dasha_external_oracle"
    assert "covered_is_not_complete" in report["past_correction_ids"]


def test_skill_gap_truth_audit_markdown_is_human_readable() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/skill_gap_truth_audit.py", "--format", "markdown"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    markdown = completed.stdout
    assert "# Jyotish Skill Gap Truth Audit" in markdown
    assert "can_claim_global_first: `false`" in markdown
    assert "Dasha external oracle" in markdown
    assert "Past Corrections" in markdown
