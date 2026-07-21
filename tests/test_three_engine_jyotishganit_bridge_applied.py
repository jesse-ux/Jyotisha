import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/three_engine_jyotishganit_bridge_applied_2026_07_21.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_applied_bridge_maps_jyotishganit_fields_to_existing_temcq_tickets():
    data = json.loads(PACKET.read_text(encoding="utf-8"))

    assert data["scope"] == "three_engine_jyotishganit_bridge_applied"
    assert data["claim_status"] == "observation_only"
    assert data["truth_matrix_allowed"] is False
    assert data["source_bridge"] == "references/oracle/jyotishganit_three_engine_closure_bridge_2026_07_21.json"
    assert data["summary"]["existing_ticket_rows"] == 18
    assert data["summary"]["no_existing_ticket_rows"] == 1
    assert data["summary"]["truth_upgrades"] == 0


def test_applied_bridge_keeps_all_rows_open_or_comparison_ready():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    rows = data["rows"]
    ticket_rows = [row for row in rows if row["existing_ticket_id"]]
    panchanga = next(row for row in rows if row["field"] == "Panchanga")

    assert len(ticket_rows) == 18
    assert {row["closure_status"] for row in rows} == {
        "ready_for_field_comparison",
        "no_existing_ticket_create_next",
    }
    assert panchanga["existing_ticket_id"] is None
    assert panchanga["closure_status"] == "no_existing_ticket_create_next"
    assert all(row["claim_boundary"] == "field_comparison_only_no_formula_truth" for row in rows)


def test_applied_bridge_is_registered_in_evidence_index():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    entry = next(
        row for row in index["packets"]
        if row["packet_id"] == "three_engine_jyotishganit_bridge_applied_2026_07_21"
    )

    assert entry["domain"] == "three_engine_parity"
    assert entry["claim_status"] == "observation_only"
