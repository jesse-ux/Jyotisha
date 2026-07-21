import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "references/oracle/jyotishganit_three_engine_closure_bridge_2026_07_21.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_jyotishganit_bridge_routes_only_available_fields_to_closure_queue():
    data = json.loads(BRIDGE.read_text(encoding="utf-8"))

    assert data["scope"] == "jyotishganit_three_engine_closure_bridge"
    assert data["claim_status"] == "observation_only"
    assert data["truth_matrix_allowed"] is False
    assert data["source_probe"] == "scripts/jyotishganit_field_probe.py"
    assert data["source_raw_hash"] == "19fa9ea862b68c4cffb6756fa6cbf0466daf47a8b008b3fe8809e9fc6a1ed30c"
    assert set(data["field_routes"]["ready_for_field_comparison"]) == {
        "D2",
        "D4",
        "D9",
        "D10",
        "Panchanga",
        "BAV_SAV",
    }
    assert data["field_routes"]["explicit_gaps"] == ["Shadbala"]


def test_jyotishganit_bridge_is_registered():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    entry = next(
        row for row in index["packets"]
        if row["packet_id"] == "jyotishganit_three_engine_closure_bridge_2026_07_21"
    )

    assert entry["domain"] == "three_engine_parity"
    assert entry["claim_status"] == "observation_only"
