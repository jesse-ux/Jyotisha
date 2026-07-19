from __future__ import annotations

import json
from pathlib import Path

from scripts.three_engine_mismatch_closure_queue import build_queue

ROOT = Path(__file__).resolve().parents[1]
ARBITRATION = ROOT / "references" / "oracle" / "three_engine_mismatch_arbitration_2026_07_19.json"
QUEUE = ROOT / "references" / "oracle" / "three_engine_mismatch_closure_queue_2026_07_19.json"


def test_closure_queue_turns_classified_mismatches_into_actionable_items() -> None:
    queue = build_queue(ARBITRATION)

    assert queue["scope"] == "three_engine_mismatch_closure_queue"
    assert queue["status"] == "open"
    assert queue["truth_policy"] == "no_majority_vote"
    assert queue["production_tuning_allowed"] is False
    assert queue["summary"]["source_mismatch_count"] == 60
    assert queue["summary"]["queue_count"] == 60
    assert queue["summary"]["priority_counts"]["P0"] >= 1

    first = queue["queue"][0]
    assert first["ticket_id"].startswith("TEMCQ-")
    assert first["owner_track"] in {"endpoint_contract", "formula_source", "unit_schema", "worked_example"}
    assert first["closure_status"] == "open"
    assert first["required_evidence"]
    assert first["commercial_visibility"] == "do_not_expose_raw"


def test_closure_queue_artifact_matches_mismatch_count() -> None:
    data = json.loads(QUEUE.read_text(encoding="utf-8"))

    assert data["summary"]["source_mismatch_count"] == 60
    assert data["summary"]["queue_count"] == 60
    assert data["production_tuning_allowed"] is False
    assert all(row["closure_status"] == "open" for row in data["queue"])
