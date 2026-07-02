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

    draft_refs = layers["quarantined_drafts"]["source_refs"]
    source_refs = set(report["runtime_source_refs"])
    assert any("docs/research/local_drafts/" in path for path in draft_refs)
    assert all(path not in source_refs for path in draft_refs)


def test_quality_gate_runs_interpretation_source_inventory_gate() -> None:
    quality_gate = (ROOT / "scripts" / "run_quality_gate.py").read_text(encoding="utf-8")

    assert '"scripts/interpretation_source_inventory_gate.py"' in quality_gate
    assert '[PYTHON, "scripts/interpretation_source_inventory_gate.py"]' in quality_gate
