import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/shadbala_component_closure_rollup_2026_07_22.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_shadbala_rollup_summarizes_all_42_same_unit_rows():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    assert data["scope"] == "shadbala_component_closure_rollup"
    assert data["claim_status"] == "component_explanatory_partial"
    assert data["truth_matrix_allowed"] is False
    assert data["production_tuning_allowed"] is False
    assert data["summary"]["total_rows"] == 42
    assert data["summary"]["bucket_counts"] == {
        "method_variant": 8,
        "formula_or_unit_mismatch": 27,
        "within_tolerance": 7,
    }
    assert data["summary"]["absolute_truth_upgrade_count"] == 0


def test_shadbala_rollup_marks_only_naisargika_tolerance_ready():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    rows = {row["component"]: row for row in data["components"]}
    assert rows["naisargika"]["closure_status"] == "observation_tolerance_ready"
    assert rows["naisargika"]["bucket_counts"] == {"within_tolerance": 7}
    for component in ["dig", "drik", "kala", "sthana"]:
        assert rows[component]["closure_status"] == "formula_or_unit_arbitration_required"
    assert rows["chesta"]["closure_status"] == "method_variant_requires_source_choice"
    assert "absolute Virupa parity" in data["boundary"]


def test_shadbala_rollup_is_indexed():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    packet = packets["shadbala_component_closure_rollup_2026_07_22"]
    assert packet["claim_status"] == "partial"
    assert packet["consumer_policy"] == "research_observation_only"
