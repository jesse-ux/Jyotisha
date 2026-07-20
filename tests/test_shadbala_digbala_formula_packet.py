import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/shadbala_digbala_formula_packet_2026_07_20.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_digbala_packet_classifies_all_rows_as_formula_or_unit_mismatch():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    assert data["scope"] == "shadbala_digbala_formula_packet"
    assert data["component"] == "dig"
    assert data["claim_status"] == "partial"
    assert data["closure_classification"] == "formula_or_unit_mismatch"
    assert data["absolute_parity_ready"] is False
    assert data["production_tuning_allowed"] is False
    assert data["truth_matrix_allowed"] is False
    assert data["summary"]["component_row_count"] == 7
    assert data["summary"]["formula_or_unit_mismatch_count"] == 7
    assert data["summary"]["within_tolerance_count"] == 0


def test_digbala_packet_splits_mismatch_families_without_majority_vote():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    rows = {row["planet"]: row for row in data["rows"]}
    assert rows["Moon"]["mismatch_family"] == "local_formula_outlier"
    assert rows["Mars"]["mismatch_family"] == "local_formula_outlier"
    assert rows["Jupiter"]["mismatch_family"] == "local_formula_outlier"
    assert rows["Saturn"]["mismatch_family"] == "small_delta_still_unfrozen"
    for planet, row in rows.items():
        assert row["next_evidence_owner"] == "formula_source_arbitration"
        assert "house-cusp vs whole-house angular distance" in row["known_variants"]
        assert row["claim_boundary"].startswith("Do not tune Digbala")


def test_digbala_packet_is_indexed_as_partial_component_closure():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    packets = {row["packet_id"]: row for row in index["packets"]}
    packet = packets["shadbala_digbala_formula_packet_2026_07_20"]
    assert packet["claim_status"] == "partial"
    assert packet["domain"] == "shadbala_component_closure"
