import hashlib
import json
from copy import deepcopy
from pathlib import Path

from scripts.minute_rectification_blind_eval import _candidate_moments, implementation_sha256, summarize_trials
from scripts.minute_rectification_holdout_validator import DEFAULT_MANIFEST, validate


def _manifest() -> dict:
    return json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))


def test_seeded_public_minute_protocol_remains_blocked_below_twenty_cases() -> None:
    report = validate()
    assert report["status"] == "blocked_awaiting_public_aa_cases"
    assert report["verified_minute_claim_allowed"] is False
    assert report["valid_public_aa_cases"] == 1
    assert report["invalid_cases"] == []


def test_frozen_implementation_hash_matches_manifest() -> None:
    manifest = _manifest()
    frozen = manifest["frozen_scoring"]
    assert implementation_sha256(frozen["files"]) == frozen["implementation_sha256"]


def test_validator_accepts_the_new_sealed_schema_version(tmp_path: Path) -> None:
    manifest = _manifest()
    manifest["schema_version"] = "minute-rectification-holdout-v3"
    manifest["source_audit_status"] = "passed_before_freeze"
    path = tmp_path / "v3.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate(path)

    assert "unsupported_schema_version" not in report["manifest_errors"]


def test_v3_validator_requires_content_source_audit_before_freeze(tmp_path: Path) -> None:
    manifest = _manifest()
    manifest["schema_version"] = "minute-rectification-holdout-v3"
    manifest["source_audit_status"] = "invalidated_after_replay"
    path = tmp_path / "invalid-source-audit.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate(path)

    assert "source_content_audit_not_passed_before_freeze" in report["manifest_errors"]
    assert report["status"] == "blocked_awaiting_public_aa_cases"


def _add_v4_review_safeguards(manifest: dict) -> None:
    manifest["schema_version"] = "minute-rectification-holdout-v4"
    manifest["source_audit_status"] = "passed_before_freeze"
    manifest["minimum_gate"]["day_precision_events_per_case"] = 3
    for case in manifest["cases"]:
        case["adjudicator"] = "independent-reviewer"
        case["independent_human_reviewed"] = True
        case["frozen_before_scoring"] = True
        case["false_minute_commitments"] = [
            {
                "offset_minutes": offset,
                "commitment_hash": hashlib.sha256(
                    f"{case['case_id']}:{offset}:sealed".encode()
                ).hexdigest(),
            }
            for offset in case["false_minute_offsets"]
        ]


def test_v4_validator_accepts_reviewed_cases_with_committed_false_minutes(tmp_path: Path) -> None:
    manifest = deepcopy(_manifest())
    _add_v4_review_safeguards(manifest)
    path = tmp_path / "v4.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate(path)

    assert report["manifest_errors"] == []
    assert report["invalid_case_details"] == []


def test_v4_validator_rejects_unreviewed_or_uncommitted_cases(tmp_path: Path) -> None:
    manifest = deepcopy(_manifest())
    _add_v4_review_safeguards(manifest)
    case = manifest["cases"][0]
    case["independent_human_reviewed"] = False
    case["false_minute_commitments"].pop()
    path = tmp_path / "invalid-v4.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    errors = validate(path)["invalid_case_details"][0]["errors"]

    assert "independent_review_not_attested" in errors
    assert "false_minute_commitments_do_not_match_offsets" in errors


def test_validator_rejects_tuning_case_and_non_independent_event_source(tmp_path: Path) -> None:
    manifest = deepcopy(_manifest())
    case = manifest["cases"][0]
    case["excluded_from_tuning"] = False
    case["events"][0]["source"]["url"] = case["birth"]["source"]["url"]
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate(path)
    errors = report["invalid_case_details"][0]["errors"]
    assert "case_not_excluded_from_tuning" in errors
    assert "event_1_source_not_independent_of_birth" in errors
    assert report["valid_public_aa_cases"] == 0


def test_validator_requires_adjacent_false_minutes_on_both_sides(tmp_path: Path) -> None:
    manifest = deepcopy(_manifest())
    manifest["cases"][0]["false_minute_offsets"] = [1, 2, 5, 10]
    path = tmp_path / "one-sided.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    errors = validate(path)["invalid_case_details"][0]["errors"]
    assert "false_minutes_do_not_cover_both_sides" in errors
    assert "false_minutes_missing_adjacent_controls" in errors


def test_metric_summary_reports_accuracy_error_and_rejection() -> None:
    trials = [
        {
            "true_rank": 1,
            "minute_error": 0,
            "false_confirmation": False,
            "insufficient_evidence_rejected": True,
            "would_confirm": True,
        },
        {
            "true_rank": 4,
            "minute_error": 4,
            "false_confirmation": True,
            "insufficient_evidence_rejected": False,
            "would_confirm": True,
        },
    ]
    gates = {
        "top_1_rate_minimum": 0.5,
        "top_3_rate_minimum": 0.5,
        "mean_absolute_minute_error_maximum": 2.0,
        "false_confirmation_rate_maximum": 0.5,
        "correct_insufficient_evidence_rejection_rate_minimum": 0.5,
    }

    report = summarize_trials(trials, gates)

    assert report["metrics"] == {
        "top_1_rate": 0.5,
        "top_3_rate": 0.5,
        "mean_absolute_minute_error": 2.0,
        "false_confirmation_rate": 0.5,
        "correct_insufficient_evidence_rejection_rate": 0.5,
        "confirmation_coverage_rate": 1.0,
    }
    assert report["metric_gates_passed"] is True


def test_blind_candidate_moments_preserve_real_dates_across_midnight() -> None:
    case = {
        "candidate_radius_minutes": 5,
        "birth": {"date": "2000-01-02", "time": "00:03"},
    }

    moments = _candidate_moments(case)

    assert moments[0].isoformat() == "2000-01-01T23:58:00"
    assert moments[5].isoformat() == "2000-01-02T00:03:00"
    assert moments[-1].isoformat() == "2000-01-02T00:08:00"
