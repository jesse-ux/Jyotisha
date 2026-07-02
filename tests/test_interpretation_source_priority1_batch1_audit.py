#!/usr/bin/env python3
"""Regression tests for the first priority-1 reference promotion audit."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT_JSON = ROOT / "docs" / "research" / "interpretation_source_priority1_batch1_promotion_audit_2026_07_02.json"
AUDIT_MD = ROOT / "docs" / "research" / "interpretation_source_priority1_batch1_promotion_audit_2026_07_02.md"
INVENTORY_REPORT = ROOT / "docs" / "research" / "interpretation_source_full_classification_2026_07_02.md"


def _load_audit() -> dict:
    return json.loads(AUDIT_JSON.read_text(encoding="utf-8"))


def test_priority1_batch1_audit_has_required_shape_and_dispositions() -> None:
    audit = _load_audit()
    entries = audit["entries"]

    assert audit["scope"] == "interpretation_source_priority1_batch1_promotion_audit"
    assert audit["status"] == "triaged"
    assert 20 <= len(entries) <= 30
    assert audit["summary"]["batch_size"] == len(entries)
    assert audit["source_inventory_baseline"] == str(INVENTORY_REPORT.relative_to(ROOT))
    assert audit["runtime_effect"] == "none_audit_only"

    dispositions = {entry["disposition"] for entry in entries}
    assert dispositions == {"promote", "reference-only", "obsolete", "duplicate", "quarantine"}

    for entry in entries:
        assert entry["path"].startswith("references/")
        assert entry["inventory_priority"] == "priority_1"
        assert entry["inventory_classification"] == "reference_candidate"
        assert entry["promotion_layer"] in {
            "primary_truth_candidate",
            "reference_layer_candidate",
            "not_truth_source",
        }
        assert entry["reason"].strip()
        assert entry["next_action"].strip()
        assert entry["source_caution"].strip()


def test_priority1_batch1_audit_locks_high_risk_source_decisions() -> None:
    by_path = {entry["path"]: entry for entry in _load_audit()["entries"]}

    promote_paths = {
        "references/argala-complete-guide.md",
        "references/badhaka-obstacle-planet-guide.md",
        "references/event_judgment_skeleton.md",
        "references/planetary-dignity-complete-reference.md",
        "references/retrograde-combustion-war-guide.md",
        "references/transit-multi-reference-guide.md",
        "references/vimshottari_dasha_guide.md",
    }
    for path in promote_paths:
        assert by_path[path]["disposition"] == "promote"
        assert by_path[path]["promotion_layer"] in {
            "primary_truth_candidate",
            "reference_layer_candidate",
        }

    assert by_path["references/kp-practical-event-timing.md"]["disposition"] == "quarantine"
    assert by_path["references/analysis-full-reading-v1.8-review.md"]["disposition"] == "obsolete"
    assert by_path["references/varga-system-quick-reference.md"]["disposition"] == "duplicate"
    assert by_path["references/yoga-list-chinese.md"]["disposition"] == "duplicate"
    assert by_path["references/dasa-convergence-methodology.md"]["disposition"] == "reference-only"
    assert by_path["references/yoga-strength-scoring-system.md"]["disposition"] == "reference-only"


def test_priority1_batch1_audit_markdown_states_boundaries() -> None:
    text = AUDIT_MD.read_text(encoding="utf-8")

    assert "第一批升格审计" in text
    assert "`promote`" in text
    assert "`reference-only`" in text
    assert "`obsolete`" in text
    assert "`duplicate`" in text
    assert "`quarantine`" in text
    assert "不直接接入 runtime source pack" in text
    assert "promotion still requires" in text
