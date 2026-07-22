import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/horary_annual_sensitive_points_numeric_packet_queue_2026_07_22.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_horary_annual_queue_tracks_all_requested_families_without_claim_upgrade():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    assert data["scope"] == "horary_annual_sensitive_points_numeric_packet_queue"
    assert data["claim_status"] == "open_queue"
    assert data["truth_matrix_allowed"] is False
    assert data["production_tuning_allowed"] is False
    techniques = {row["technique"] for row in data["rows"]}
    assert {
        "Prashna input contract",
        "Sphuta / Trisphuta / Chatusphuta / Panchasphuta",
        "Gulika",
        "Saham",
        "Tajika / Varshaphala",
    } <= techniques
    assert "do not upgrade" in data["boundary"]


def test_sphuta_has_partial_numeric_candidate_but_tajika_remains_blocked():
    rows = {row["technique"]: row for row in json.loads(PACKET.read_text(encoding="utf-8"))["rows"]}
    sphuta = rows["Sphuta / Trisphuta / Chatusphuta / Panchasphuta"]
    assert sphuta["numeric_candidate_status"] == "partial_numeric_candidate_present_not_oracle"
    assert "trisphuta" in sphuta["numeric_fields_present"]
    assert "complete Prashna input" in sphuta["missing_for_oracle"]

    tajika = rows["Tajika / Varshaphala"]
    assert tajika["numeric_candidate_status"] == "source_hunt_blocked"
    assert "Yumpu snippets" in tajika["claim_boundary"]


def test_horary_annual_queue_is_indexed():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    packet = packets["horary_annual_sensitive_points_numeric_packet_queue_2026_07_22"]
    assert packet["claim_status"] == "open_queue"
    assert packet["consumer_policy"] == "research_observation_only"
