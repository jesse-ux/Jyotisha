import json
from pathlib import Path

from scripts.minute_rectification_source_audit import build_source_audit


def test_source_audit_supports_current_holdout_shape_and_counts_day_precision(tmp_path: Path) -> None:
    source = tmp_path / "cases.json"
    source.write_text(json.dumps({"cases": [{
        "case_id": "public-case",
        "subject_label": "Public case",
        "birth": {"source": {"rodden_rating": "AA", "url": "https://example.test/birth"}},
        "events": [
            {"date": "2001-01-01"},
            {"date": "2002"},
        ],
    }]}), encoding="utf-8")

    report = build_source_audit([source])

    assert report["public_aa_case_count"] == 1
    assert report["cases"][0]["existing_day_precision_event_count"] == 1
    assert report["cases"][0]["additional_day_precision_events_required"] == 2
    assert report["production_tuning_allowed"] is False
