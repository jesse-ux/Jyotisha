import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/shadbala_chesta_variant_packet_2026_07_20.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_chesta_packet_keeps_method_variants_separate_from_formula_mismatch():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    assert data["scope"] == "shadbala_chesta_variant_packet"
    assert data["component"] == "chesta"
    assert data["claim_status"] == "partial"
    assert data["closure_classification"] == "method_variant_mixed_with_formula_mismatch"
    assert data["absolute_parity_ready"] is False
    assert data["production_tuning_allowed"] is False
    assert data["truth_matrix_allowed"] is False
    assert data["summary"]["component_row_count"] == 7
    assert data["summary"]["method_variant_count"] == 6
    assert data["summary"]["formula_or_unit_mismatch_count"] == 1
    assert data["summary"]["within_tolerance_count"] == 0


def test_chesta_packet_records_luminary_policy_conflict_and_venus_exception():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    rows = {row["planet"]: row for row in data["rows"]}
    assert rows["Sun"]["variant_family"] == "luminary_chesta_policy_conflict"
    assert rows["Moon"]["variant_family"] == "luminary_chesta_policy_conflict"
    assert rows["Venus"]["closure_classification"] == "formula_or_unit_mismatch"
    assert rows["Venus"]["next_evidence_owner"] == "formula_source_arbitration"
    for planet in ["Mars", "Mercury", "Jupiter", "Saturn"]:
        assert rows[planet]["variant_family"] == "mean_motion_seeghrochcha_variant"
        assert rows[planet]["closure_classification"] == "method_variant"


def test_chesta_packet_is_indexed_as_partial_component_closure():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    packets = {row["packet_id"]: row for row in index["packets"]}
    packet = packets["shadbala_chesta_variant_packet_2026_07_20"]
    assert packet["claim_status"] == "partial"
    assert packet["domain"] == "shadbala_component_closure"
