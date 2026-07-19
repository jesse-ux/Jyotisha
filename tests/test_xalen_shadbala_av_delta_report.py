from __future__ import annotations

from pathlib import Path

from scripts.xalen_shadbala_av_delta_report import build_report

ROOT = Path(__file__).resolve().parents[1]


def test_xalen_shadbala_av_delta_report_groups_component_differences() -> None:
    report = build_report(
        ROOT / "references/oracle/three_engine_parity_replay_manifest.json",
        ROOT / "references/oracle/artifacts/xalen_steve_jobs_high_rigor_raw.json",
        ROOT / "references/oracle/shadbala_av_component_provenance_registry_2026_07_19.json",
    )

    assert report["scope"] == "xalen_shadbala_av_component_delta_report"
    assert report["truth_policy"] == "method_variant_not_majority_vote"
    assert report["production_tuning_allowed"] is False
    assert report["source_commit"] == "cc6edbec1f748ebdc4950ae6198f575c5ada73fa"
    assert report["license"] == "Apache-2.0"
    assert report["summary"]["shadbala_component_rows"] == 42
    assert report["summary"]["shadbala_component_mismatch_count"] == 35
    assert report["summary"]["ashtakavarga_rows"] == 8
    assert report["summary"]["ashtakavarga_mismatch_count"] == 4
    assert report["summary"]["shadbala_total_mismatch_count"] == 7


def test_xalen_shadbala_av_delta_report_preserves_evidence_requirements() -> None:
    report = build_report(
        ROOT / "references/oracle/three_engine_parity_replay_manifest.json",
        ROOT / "references/oracle/artifacts/xalen_steve_jobs_high_rigor_raw.json",
        ROOT / "references/oracle/shadbala_av_component_provenance_registry_2026_07_19.json",
    )

    for row in report["component_groups"]:
        assert row["closure_status"] == "open"
        assert row["required_evidence"]
        assert row["unit_contract"]
        assert row["allowed_claim"] in {
            "component_method_variant",
            "table_variant",
            "derived_total_blocked_until_components_close",
            "derived_total_only_after_components_close",
        }
