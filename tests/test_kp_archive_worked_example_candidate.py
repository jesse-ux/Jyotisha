import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/kp_archive_worked_example_candidate_2026_07_21.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_kp_archive_candidate_is_closer_but_not_oracle():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    assert data["scope"] == "kp_archive_worked_example_candidate"
    assert data["claim_status"] == "open_queue"
    assert data["truth_matrix_allowed"] is False
    assert data["candidate_strength"] == "worked_example_text_candidate"
    assert "Sub-Sub lord" in data["observed_public_snippet_topics"]
    assert "cusp significator example" in data["observed_public_snippet_topics"]
    assert data["oracle_status"] == "blocked_pending_structured_numeric_extraction"


def test_kp_archive_candidate_is_indexed():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    packet = packets["kp_archive_worked_example_candidate_2026_07_21"]
    assert packet["claim_status"] == "open_queue"
    assert packet["consumer_policy"] == "research_observation_only"
