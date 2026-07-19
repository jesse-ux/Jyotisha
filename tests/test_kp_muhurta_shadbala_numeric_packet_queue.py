import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "references/oracle/kp_muhurta_shadbala_numeric_packet_queue_2026_07_19.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_numeric_packet_queue_attaches_kp_runtime_raw_but_no_truth_upgrade():
    data = json.loads(QUEUE.read_text(encoding="utf-8"))
    assert data["scope"] == "kp_muhurta_shadbala_numeric_packet_queue"
    assert data["claim_status"] == "open_queue"
    assert data["production_tuning_allowed"] is False
    assert data["truth_matrix_allowed"] is False
    assert data["runtime_observations"][0]["raw_hash"] == "2e7a6b17eb2965a60846f625f6bd8bc03555216d6225983647bcbfa23d0e345b"
    assert all(row["numeric_oracle_status"].startswith("blocked_") for row in data["packet_rows"])


def test_numeric_packet_queue_covers_requested_topics():
    data = json.loads(QUEUE.read_text(encoding="utf-8"))
    topics = {row["topic"] for row in data["packet_rows"]}
    assert {"KP cusp", "KP sub-lord table", "Tarabala/Chandrabala", "Rahu Kalam", "Shadbala Virupa"} <= topics
    for row in data["packet_rows"]:
        assert "raw_capture_hash" in row["required_fields"] or row["topic"] == "KP sub-lord table"


def test_evidence_index_registers_packet_queue():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    packets = {row["packet_id"]: row for row in index["packets"]}
    assert packets["kp_muhurta_shadbala_numeric_packet_queue"]["claim_status"] == "open_queue"
