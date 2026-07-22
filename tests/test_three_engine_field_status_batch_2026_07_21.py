import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/three_engine_field_status_batch_2026_07_21.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_field_status_batch_adds_panchanga_ticket_and_keeps_truth_closed():
    data = json.loads(PACKET.read_text(encoding="utf-8"))

    assert data["scope"] == "three_engine_field_status_batch"
    assert data["claim_status"] == "observation_only"
    assert data["truth_matrix_allowed"] is False
    assert data["summary"]["truth_upgrades"] == 0
    assert data["panchanga_ticket"]["ticket_id"] == "TEMCQ-061"
    assert data["panchanga_ticket"]["closure_status"] == "open"


def test_field_status_batch_classifies_all_mapped_rows():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    rows = data["rows"]

    assert len(rows) == 18
    assert data["summary"]["rows_total"] == 18
    assert data["summary"]["endpoint_semantics"] == 10
    assert data["summary"]["worked_example_required"] == 8
    assert {row["status_after_bridge"] for row in rows} == {
        "ready_for_endpoint_semantics_check",
        "ready_for_worked_example_comparison",
    }
    assert all(row["claim_boundary"] == "status_classification_only_no_numeric_truth" for row in rows)


def test_field_status_batch_is_registered():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    entry = next(
        row for row in index["packets"]
        if row["packet_id"] == "three_engine_field_status_batch_2026_07_21"
    )

    assert entry["domain"] == "three_engine_parity"
    assert entry["claim_status"] == "observation_only"
