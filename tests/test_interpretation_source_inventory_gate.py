#!/usr/bin/env python3
"""Regression tests for interpretation source inventory governance."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_interpretation_source_inventory_gate_reports_layered_source_pack() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/interpretation_source_inventory_gate.py",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)

    assert report["scope"] == "interpretation_source_inventory_gate"
    assert report["status"] == "pass"
    assert report["source_pack_status"] == "used"
    assert report["summary"]["missing_ref_count"] == 0
    assert report["summary"]["promoted_quarantined_count"] == 0
    assert report["summary"]["primary_truth_count"] >= 5
    assert report["summary"]["reference_layer_count"] >= 10
    assert report["summary"]["quarantined_draft_count"] >= 1

    layers = report["layers"]
    assert "jyotish-app/interpretation.js" in layers["frontend_interpretation"]["source_refs"]
    assert "references/open_source_sources/vedic-astro-skills/codex/skills/vedic-core/resources/qa_rules.md" in layers["qa_governance"]["source_refs"]
    assert "references/open_source_sources/vedic-astro-skills/codex/skills/vedic-reader/resources/validation_rules.md" in layers["reader_validation"]["source_refs"]
    assert "references/yoga_rules.json" in layers["yoga_rules"]["source_refs"]
    assert "references/saham_rules.json" in layers["saham_rules"]["source_refs"]
    assert layers["core_rule_sources"]["promotion_batch"] == "priority1_batch1_core5"
    assert layers["core_rule_sources"]["source_refs"] == [
        "references/prediction-boundary-protocol.md",
        "references/event_judgment_skeleton.md",
        "references/planetary-dignity-complete-reference.md",
        "references/retrograde-combustion-war-guide.md",
        "references/transit-multi-reference-guide.md",
    ]

    draft_refs = layers["quarantined_drafts"]["source_refs"]
    source_refs = set(report["runtime_source_refs"])
    assert any("docs/research/local_drafts/" in path for path in draft_refs)
    assert all(path not in source_refs for path in draft_refs)


def test_quality_gate_runs_interpretation_source_inventory_gate() -> None:
    quality_gate = (ROOT / "scripts" / "run_quality_gate.py").read_text(encoding="utf-8")

    assert '"scripts/interpretation_source_inventory_gate.py"' in quality_gate
    assert '[PYTHON, "scripts/interpretation_source_inventory_gate.py"]' in quality_gate


def test_interpretation_source_inventory_gate_classifies_full_candidate_pool() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/interpretation_source_inventory_gate.py",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    classification = report["full_classification"]

    assert classification["status"] == "classified"
    assert classification["candidate_count"] >= 900
    assert classification["unclassified_candidate_count"] == 0
    assert classification["priority_bucket_counts"]["priority_1"] >= 50
    assert classification["priority_bucket_counts"]["priority_2"] >= 50
    assert classification["priority_bucket_counts"]["priority_3"] >= 100

    by_path = classification["by_path"]
    assert by_path["references/real_case_studies/vedicka/career-success-poverty-prosperity.md"]["classification"] == "real_case_calibration"
    assert by_path["references/open_source_sources/rishi-ai-mcp/.agents/skills/career-analysis/SKILL.md"]["classification"] == "open_source_reference"
    assert by_path["references/open_source_sources/vedic-astro-skills/codex/skills/vedic-core/resources/qa_rules.md"]["classification"] == "runtime_reference_layer"
    assert by_path["references/advanced-techniques.md"]["classification"] == "reference_candidate"
    assert by_path["docs/research/local_drafts/2026-06/antigravity_round31_api_completion_top50_2026_06_26.md"]["classification"] == "quarantined_draft"
    assert by_path["docs/research/ACTIVE_FRONTS.md"]["classification"] == "research_governance"

    assert by_path["references/open_source_sources/rishi-ai-mcp/.agents/skills/career-analysis/SKILL.md"]["priority"] == "priority_1"
    assert by_path["references/real_case_studies/vedicka/career-success-poverty-prosperity.md"]["priority"] == "priority_1"
    assert by_path["docs/research/local_drafts/2026-06/antigravity_round31_api_completion_top50_2026_06_26.md"]["promotion_status"] == "not_truth_source"
