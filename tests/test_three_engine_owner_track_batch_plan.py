import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "references/oracle/three_engine_owner_track_batch_plan_2026_07_20.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_three_engine_owner_track_batch_plan_groups_remaining_open_rows():
    data = json.loads(
        subprocess.check_output(
            ["python3", "scripts/three_engine_owner_track_batch_plan.py", "--date", "2026-07-20"],
            cwd=ROOT,
            text=True,
        )
    )
    assert data["scope"] == "three_engine_owner_track_batch_plan"
    assert data["summary"]["source_queue_count"] == 60
    assert data["summary"]["already_attributed_count"] == 2
    assert data["summary"]["remaining_ticket_count"] == 58
    assert data["production_tuning_allowed"] is False


def test_three_engine_owner_track_batch_plan_has_owner_batches_and_boundaries():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    batches = {row["owner_track"]: row for row in data["batches"]}
    assert {"endpoint_contract", "formula_source", "unit_schema", "worked_example"} <= set(batches)
    assert batches["endpoint_contract"]["ticket_count"] >= 1
    assert all(batch["claim_boundary"].startswith("Batch planning only") for batch in data["batches"])


def test_three_engine_owner_track_batch_plan_is_indexed():
    packets = {row["packet_id"]: row for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]}
    assert packets["three_engine_owner_track_batch_plan_2026_07_20"]["claim_status"] == "open_queue"
