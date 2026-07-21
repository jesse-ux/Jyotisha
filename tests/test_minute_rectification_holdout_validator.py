from scripts.minute_rectification_holdout_validator import validate


def test_empty_public_minute_protocol_blocks_verified_claims() -> None:
    report = validate()
    assert report["status"] == "blocked_awaiting_public_aa_cases"
    assert report["verified_minute_claim_allowed"] is False
    assert report["valid_public_aa_cases"] == 0
import hashlib
import json

from scripts.minute_rectification_holdout_validator import validate


def _case(*, offsets=(-5, -2, 2, 5), event_count=3):
    controls = [
        {
            "control_id": f"control-{index}",
            "offset_minutes": offset,
            "commitment_hash": hashlib.sha256(f"fixed-control-{index}".encode()).hexdigest(),
        }
        for index, offset in enumerate(offsets)
    ]
    return {
        "case_id": "public-aa-case",
        "birth_source": {
            "url": "https://example.test/birth-record",
            "time_accuracy_rating": "AA",
        },
        "events": [
            {
                "event_date": f"200{index}-01-0{index + 1}",
                "source": {"url": f"https://independent.example.test/event-{index}"},
            }
            for index in range(event_count)
        ],
        "negative_minutes": controls,
    }


def _manifest(case):
    return {
        "benchmark_id": "test-minute-holdout",
        "minimum_gate": {"public_aa_cases": 1, "events_per_case": 3, "negative_minutes_per_case": 4},
        "boundary": "test boundary",
        "cases": [case],
    }


def test_validator_requires_independent_dated_events_and_committed_controls(tmp_path):
    path = tmp_path / "holdout.json"
    path.write_text(json.dumps(_manifest(_case())), encoding="utf-8")

    report = validate(path)

    assert report["status"] == "ready_for_blind_replay"
    assert report["valid_public_aa_cases"] == 1
    assert report["verified_minute_claim_allowed"] is False


def test_validator_rejects_one_sided_or_uncommitted_false_minutes(tmp_path):
    path = tmp_path / "holdout.json"
    case = _case(offsets=(-5, -2, -1, -1))
    case["negative_minutes"][0].pop("commitment_hash")
    path.write_text(json.dumps(_manifest(case)), encoding="utf-8")

    report = validate(path)

    assert report["status"] == "blocked_awaiting_public_aa_cases"
    assert report["invalid_cases"] == ["public-aa-case:negative_controls_invalid"]
