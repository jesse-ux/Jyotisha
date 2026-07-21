import json

from scripts.minute_rectification_holdout_intake import append_case


def _case():
    return {
        "case_id": "case-1",
        "adjudicator": "independent-reviewer",
        "independent_human_reviewed": True,
        "frozen_before_scoring": True,
        "birth_source": {"url": "https://birth.example/case-1", "time_accuracy_rating": "AA"},
        "events": [
            {"event_date": "2000-01-01", "source": {"url": "https://event.example/1"}},
            {"event_date": "2001-01-01", "source": {"url": "https://event.example/2"}},
            {"event_date": "2002-01-01", "source": {"url": "https://event.example/3"}},
        ],
        "negative_minutes": [
            {"control_id": "a", "offset_minutes": -5, "commitment_hash": "a" * 64},
            {"control_id": "b", "offset_minutes": -2, "commitment_hash": "b" * 64},
            {"control_id": "c", "offset_minutes": 2, "commitment_hash": "c" * 64},
            {"control_id": "d", "offset_minutes": 5, "commitment_hash": "d" * 64},
        ],
    }


def test_intake_only_appends_a_case_that_passes_the_minute_evidence_contract(tmp_path):
    manifest = tmp_path / "holdout.json"
    manifest.write_text(json.dumps({
        "benchmark_id": "test", "minimum_gate": {"public_aa_cases": 20, "events_per_case": 3, "negative_minutes_per_case": 4}, "cases": [],
    }), encoding="utf-8")

    result = append_case(manifest, _case())

    assert result["appended"] is True
    saved = json.loads(manifest.read_text(encoding="utf-8"))
    assert saved["cases"][0]["case_id"] == "case-1"


def test_intake_rejects_unreviewed_or_duplicate_cases(tmp_path):
    manifest = tmp_path / "holdout.json"
    manifest.write_text(json.dumps({
        "benchmark_id": "test", "minimum_gate": {"public_aa_cases": 20, "events_per_case": 3, "negative_minutes_per_case": 4}, "cases": [],
    }), encoding="utf-8")
    invalid = _case()
    invalid["adjudicator"] = ""

    assert append_case(manifest, invalid)["appended"] is False
    assert append_case(manifest, _case())["appended"] is True
    assert append_case(manifest, _case())["appended"] is False
