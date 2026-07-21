import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_node_source_attribution_identifies_boundary_crossing_not_d10_formula():
    data = json.loads((ROOT / "references/oracle/jyotishganit_node_source_attribution_2026_07_19.json").read_text(encoding="utf-8"))
    assert data["scope"] == "jyotishganit_node_source_attribution"
    assert data["claim_status"] == "partial"
    assert data["production_tuning_allowed"] is False
    assert data["attribution"]["formula_delta"] == "not_d10_formula_shape"
    assert data["attribution"]["primary_delta"] == "node_longitude_source_plus_ayanamsa_boundary_crossing"
    assert data["local_engine"]["Rahu"]["d10_part_index_zero_based"] == 3
    assert data["jyotishganit_engine"]["Rahu"]["d10_part_index_zero_based"] == 2
    assert data["local_true_node_control"]["control_result"].startswith("true node moves farther")


def test_evidence_index_registers_node_source_attribution():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    packets = {row["packet_id"]: row for row in index["packets"]}
    assert packets["jyotishganit_node_source_attribution"]["claim_status"] == "partial"
