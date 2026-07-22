import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/jyotishganit_field_closure_rows_2026_07_21.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_jyotishganit_field_closure_rows_are_observation_only():
    data = json.loads(PACKET.read_text(encoding="utf-8"))

    assert data["scope"] == "jyotishganit_field_closure_rows"
    assert data["claim_status"] == "observation_only"
    assert data["truth_matrix_allowed"] is False
    assert data["source_selected_hash"] == "4709b8ade84efdea4d0a67c15f3e32cea516a5aa2e8abe3885578feda20cb3f4"
    assert len(data["rows"]) == 7


def test_jyotishganit_field_rows_mark_shadbala_as_gap():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    rows = {row["field"]: row for row in data["rows"]}

    for field in ["D2", "D4", "D9", "D10", "Panchanga", "BAV", "SAV"]:
        assert rows[field]["closure_status"] == "ready_for_field_comparison"
    assert data["explicit_gaps"] == [{"field": "Shadbala", "reason": "jyotishganit probe did not expose shadbala/strengths in selected raw"}]


def test_jyotishganit_field_rows_are_registered():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    entry = next(
        row for row in index["packets"]
        if row["packet_id"] == "jyotishganit_field_closure_rows_2026_07_21"
    )

    assert entry["domain"] == "three_engine_parity"
    assert entry["claim_status"] == "observation_only"
