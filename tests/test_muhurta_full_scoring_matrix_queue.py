import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/muhurta_full_scoring_matrix_queue_2026_07_22.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_muhurta_full_scoring_matrix_keeps_final_verdict_blocked():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    assert data["scope"] == "muhurta_full_scoring_matrix_queue"
    assert data["claim_status"] == "open_queue"
    assert data["truth_matrix_allowed"] is False
    assert data["production_tuning_allowed"] is False
    assert data["summary"]["final_verdict_allowed"] is False
    assert "no final electional verdict" in data["boundary"]
    assert "Do not show a final Muhurta score" in data["display_policy"]["forbidden"]


def test_muhurta_full_scoring_matrix_tracks_requested_factors():
    rows = {row["factor"]: row for row in json.loads(PACKET.read_text(encoding="utf-8"))["factor_rows"]}
    for factor in [
        "Panchaka",
        "Yamaganda",
        "Gulika Kalam",
        "Vyatipata",
        "Vaidhriti",
        "Sankranti",
    ]:
        assert factor in rows
        assert rows[factor]["missing_for_scoring"]
    assert rows["Yamaganda"]["runtime_status"] == "local_formula_available_not_packeted"
    assert rows["Gulika Kalam"]["runtime_status"] == "local_formula_available_not_packeted"
    assert rows["Panchaka"]["runtime_status"] == "gap"
    assert rows["Sankranti"]["runtime_status"] == "gap"


def test_muhurta_full_scoring_matrix_is_indexed():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    packet = packets["muhurta_full_scoring_matrix_queue_2026_07_22"]
    assert packet["claim_status"] == "open_queue"
    assert packet["consumer_policy"] == "research_observation_only"
