import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/shadbala_naisargika_closure_packet_2026_07_20.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_naisargika_packet_closes_same_unit_observation_without_truth_upgrade():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    assert data["scope"] == "shadbala_naisargika_closure_packet"
    assert data["component"] == "naisargika"
    assert data["claim_status"] == "partial"
    assert data["closure_classification"] == "within_tolerance_observation"
    assert data["absolute_parity_ready"] is False
    assert data["production_tuning_allowed"] is False
    assert data["truth_matrix_allowed"] is False
    assert data["summary"] == {
        "component_row_count": 7,
        "max_delta_virupa": 0.0,
        "source_count_per_row": 5,
        "within_tolerance_count": 7,
    }


def test_naisargika_packet_has_all_visible_planets_and_unit_contract():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    rows = {row["planet"]: row for row in data["rows"]}
    assert set(rows) == {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
    for row in rows.values():
        values = row["normalized_values_virupa"]
        assert set(values) == {"local", "jyotishganit", "xalen", "vp_jain_local", "vp_jain_published"}
        assert max(values.values()) - min(values.values()) == 0
        assert row["unit_contract"] == "Virupa fixed natural-strength table; 60 Virupa = 1 Rupa."
        assert row["closure_status"] == "same_unit_observation_frozen"


def test_naisargika_packet_is_indexed_as_partial_component_closure():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    packets = {row["packet_id"]: row for row in index["packets"]}
    packet = packets["shadbala_naisargika_closure_packet_2026_07_20"]
    assert packet["claim_status"] == "partial"
    assert packet["domain"] == "shadbala_component_closure"
