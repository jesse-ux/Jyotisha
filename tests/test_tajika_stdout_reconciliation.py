from __future__ import annotations

from pathlib import Path

from scripts.tajika_stdout_reconciliation import build_report


ROOT = Path(__file__).resolve().parents[1]


def test_reconciliation_confirms_archived_tajika_fields_without_truth_upgrade() -> None:
    report = build_report(
        ROOT / "references/oracle/artifacts/pyjhora_steve_jobs_varshaphala_1984_lahiri_stdout_20260627.txt",
        ROOT / "references/oracle/artifacts/pending_packets/external_template_steve_jobs_varshaphala_1984_lahiri.json",
    )

    assert report["status"] == "external_artifact_template_consistent_observation"
    assert report["claim_status"] == "observation_only"
    assert report["truth_matrix_allowed"] is False
    assert report["summary"]["field_count"] == 9
    assert report["summary"]["matched_field_count"] == 9
    assert report["summary"]["mismatched_field_count"] == 0
    assert report["raw_artifact"]["sha256"] == "9cdfca16f756ad8fbd297032c49e5744639804cf473ece8fc7f71b2039d964b9"
    assert {row["field"] for row in report["field_comparisons"]} == {
        "solar_return_datetime",
        "varsha_lagna_deg",
        "muntha_sign",
        "year_lord",
        "mudda_dasha_first_lord",
        "sahams.punya_saham",
        "sahams.rajya_saham",
        "sahams.vivah_saham",
        "tajika_yogas",
    }
