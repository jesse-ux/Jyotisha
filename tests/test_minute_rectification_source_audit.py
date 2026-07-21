import json
from pathlib import Path

from scripts.minute_rectification_source_audit import build_source_audit


ROOT = Path(__file__).resolve().parents[1]


def test_source_audit_deduplicates_public_aa_cases_and_reports_missing_evidence(tmp_path):
    manifest = tmp_path / "cases.json"
    manifest.write_text(json.dumps({
        "cases": [
            {
                "case_id": "case-a",
                "subject": {"name": "A", "birth_source": {"url": "https://birth.example/a", "time_accuracy_rating": "AA"}},
                "event_outcomes": [{"event_date": "2000-01-01"}],
            },
            {
                "case_id": "case-a-duplicate",
                "subject": {"name": "A", "birth_source": {"url": "https://birth.example/a", "time_accuracy_rating": "AA"}},
                "event_outcomes": [{"event_date": "2001-01-01"}],
            },
            {
                "case_id": "case-b",
                "subject": {"name": "B", "birth_source": {"url": "https://birth.example/b", "time_accuracy_rating": "A"}},
            },
        ],
    }), encoding="utf-8")

    audit = build_source_audit([manifest])

    assert audit["public_aa_case_count"] == 1
    assert audit["cases"][0]["subject"] == "A"
    assert audit["cases"][0]["additional_dated_events_required"] == 1
    assert audit["cases"][0]["negative_controls_required"] == 4


def test_frozen_source_audit_matches_the_reusable_public_case_manifests():
    artifact = json.loads((ROOT / "references/real_case_calibration/minute_rectification_public_aa_source_audit_v1.json").read_text(encoding="utf-8"))

    assert artifact == build_source_audit()
    assert artifact["public_aa_case_count"] == 17
    assert artifact["additional_public_aa_cases_required"] == 3
