import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/kp_archive_numeric_locator_packet_2026_07_21.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_kp_archive_locator_has_hash_and_candidate_lines():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    assert data["scope"] == "kp_archive_numeric_locator_packet"
    assert data["claim_status"] == "open_queue"
    assert data["truth_matrix_allowed"] is False
    assert data["source_sha256"] == "3c5c714f3f15af4784c8b647268b8349e1a11bf045481abbd56d263432dd2a9a"
    assert data["source_length_bytes"] > 300000
    assert data["candidate_numeric_line_count"] >= 40
    assert data["locator_status"] == "candidate_lines_found_not_oracle"


def test_kp_archive_locator_is_indexed():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    packet = packets["kp_archive_numeric_locator_packet_2026_07_21"]
    assert packet["claim_status"] == "open_queue"
    assert packet["consumer_policy"] == "research_observation_only"
