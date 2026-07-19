from __future__ import annotations

import json
from pathlib import Path

from scripts.shadbala_av_component_registry import build_registry

ROOT = Path(__file__).resolve().parents[1]
ARBITRATION = ROOT / "references" / "oracle" / "three_engine_mismatch_arbitration_2026_07_19.json"


def test_component_registry_groups_shadbala_and_av_mismatches_without_truth_upgrade() -> None:
    registry = build_registry(ARBITRATION)

    assert registry["scope"] == "shadbala_av_component_provenance_registry"
    assert registry["truth_policy"] == "method_variant_not_majority_vote"
    assert registry["status"] == "classified_unresolved"
    assert registry["production_tuning_allowed"] is False
    assert registry["summary"]["source_mismatch_count"] == 60
    assert registry["summary"]["registry_count"] >= 4

    categories = {row["category"] for row in registry["registry"]}
    assert "shadbala_formula_variant" in categories
    assert "derived_total_from_component_variants" in categories
    assert "ashtakavarga_table_or_contributor_variant" in categories

    for row in registry["registry"]:
        assert row["allowed_claim"] in {
            "current_target_observation_only",
            "component_method_variant",
            "table_variant",
            "derived_total_blocked_until_components_close",
        }
        assert row["unit_contract"]
        assert row["next_evidence_required"]


def test_component_registry_json_artifact_matches_source_counts() -> None:
    artifact = ROOT / "references" / "oracle" / "shadbala_av_component_provenance_registry_2026_07_19.json"
    data = json.loads(artifact.read_text(encoding="utf-8"))

    assert data["summary"]["source_mismatch_count"] == 60
    assert data["summary"]["category_counts"]["shadbala_formula_variant"] == 35
    assert data["summary"]["category_counts"]["derived_total_from_component_variants"] == 7
    assert data["summary"]["category_counts"]["ashtakavarga_table_or_contributor_variant"] == 8
    assert data["production_tuning_allowed"] is False


def test_component_provenance_markdown_report_is_human_readable() -> None:
    report = ROOT / "docs" / "research" / "shadbala_av_component_provenance_report_2026_07_19.md"
    text = report.read_text(encoding="utf-8")

    for token in [
        "Shadbala / AV component provenance report",
        "method_variant_not_majority_vote",
        "Production tuning: `false`",
        "`shadbala_formula_variant`",
        "`derived_total_from_component_variants`",
        "`ashtakavarga_table_or_contributor_variant`",
        "Total Rupa/Virupa cannot be arbitrated until component units close",
        "Next source-evidence queue",
    ]:
        assert token in text
