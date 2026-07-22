import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/shadbala_hard_component_arbitration_2026_07_22.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_hard_component_arbitration_classifies_chesta_sthana_kala():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    assert data["scope"] == "shadbala_hard_component_arbitration"
    rows = {row["component"]: row for row in data["components"]}
    assert set(rows) == {"chesta", "sthana", "kala"}
    assert rows["chesta"]["dominant_issue"] == "method_variant"
    assert rows["sthana"]["dominant_issue"] == "mixed_method_and_formula"
    assert rows["kala"]["dominant_issue"] == "formula_or_unit_mismatch"
    assert data["truth_matrix_allowed"] is False


def test_hard_components_keep_actionable_boundaries():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    for row in data["components"]:
        assert row["claim_upgrade"] == "none"
        assert row["next_action"]
        assert row["blocked_reason"]


def test_hard_component_packet_is_indexed():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    packet = packets["shadbala_hard_component_arbitration_2026_07_22"]
    assert packet["claim_status"] == "partial"
    assert packet["consumer_policy"] == "research_observation_only"
