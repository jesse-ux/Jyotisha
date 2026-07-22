import hashlib
import json
from copy import deepcopy
from pathlib import Path

from scripts.minute_rectification_holdout_intake import DEFAULT_INTAKE, append_case
from scripts.minute_rectification_holdout_validator import DEFAULT_MANIFEST


def _reviewed_case() -> dict:
    case = deepcopy(json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))["cases"][0])
    case["case_id"] = "new-reviewed-case"
    case["adjudicator"] = "independent-reviewer"
    case["independent_human_reviewed"] = True
    case["frozen_before_scoring"] = True
    case["false_minute_commitments"] = [
        {
            "offset_minutes": offset,
            "commitment_hash": hashlib.sha256(f"control:{offset}".encode()).hexdigest(),
        }
        for offset in case["false_minute_offsets"]
    ]
    return case


def _queue(path: Path) -> None:
    path.write_text(json.dumps({
        "schema_version": "minute-rectification-holdout-v4-intake",
        "minimum_gate": {
            "events_per_case": 3,
            "domains_per_case": 2,
            "independent_event_sources_per_case": 2,
            "negative_minutes_per_case": 4,
            "day_precision_events_per_case": 3,
        },
        "cases": [],
    }), encoding="utf-8")


def test_intake_appends_reviewed_case_but_keeps_release_blocked(tmp_path: Path) -> None:
    path = tmp_path / "intake.json"
    _queue(path)

    report = append_case(path, _reviewed_case())
    data = json.loads(path.read_text(encoding="utf-8"))

    assert report["appended"] is True
    assert report["verified_minute_claim_allowed"] is False
    assert data["production_tuning_allowed"] is False
    assert data["verified_minute_claim_allowed"] is False
    assert data["cases"][0]["ingested_at"].endswith("Z")


def test_intake_rejects_missing_review_and_commitments(tmp_path: Path) -> None:
    path = tmp_path / "intake.json"
    _queue(path)
    case = _reviewed_case()
    case["independent_human_reviewed"] = False
    case["false_minute_commitments"] = []

    report = append_case(path, case)

    assert report["appended"] is False
    assert "independent_review_not_attested" in report["errors"]
    assert "false_minute_commitments_do_not_match_offsets" in report["errors"]


def test_default_intake_is_non_production_and_empty() -> None:
    data = json.loads(DEFAULT_INTAKE.read_text(encoding="utf-8"))

    assert data["cases"] == []
    assert data["production_tuning_allowed"] is False
    assert data["verified_minute_claim_allowed"] is False
