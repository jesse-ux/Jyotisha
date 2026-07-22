import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/shadbala_formula_arbitration_queue_v2_2026_07_22.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_shadbala_formula_arbitration_queue_tracks_five_unclosed_components():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    assert data["scope"] == "shadbala_formula_arbitration_queue_v2"
    assert data["claim_status"] == "partial"
    assert data["truth_matrix_allowed"] is False
    assert data["production_tuning_allowed"] is False
    assert data["summary"]["component_count"] == 5
    assert data["summary"]["absolute_truth_upgrade_count"] == 0
    assert "do not make Shadbala absolute Virupa parity truth-ready" in data["boundary"]


def test_shadbala_formula_arbitration_queue_has_requested_component_policies():
    rows = {row["component"]: row for row in json.loads(PACKET.read_text(encoding="utf-8"))["components"]}
    assert rows["dig"]["research_policy_to_test"] == "house_cusp_angular_distance"
    assert "whole_house_angular_distance" in rows["dig"]["alternative_variants"]
    assert rows["drik"]["research_policy_to_test"] == "classical_graha_drishti_with_signed_benefic_malefic_sum"
    assert "functional_benefic_malefic_overlay" in rows["drik"]["alternative_variants"]
    assert "hora" in rows["kala"]["subcomponents_required"]
    assert "moolatrikona_or_dignity_variant" in rows["sthana"]["subcomponents_required"]
    assert rows["chesta"]["research_policy_to_test"] == "explicit_mean_motion_seeghrochcha_variant_selection"


def test_shadbala_formula_arbitration_queue_is_indexed():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    packet = packets["shadbala_formula_arbitration_queue_v2_2026_07_22"]
    assert packet["claim_status"] == "partial"
    assert packet["consumer_policy"] == "research_observation_only"
