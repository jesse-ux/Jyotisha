import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/tajika_yumpu_source_review_gate_2026_07_21.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_yumpu_source_review_gate_blocks_numeric_oracle_until_capture_is_legal():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    assert data["scope"] == "tajika_yumpu_source_review_gate"
    assert data["claim_status"] == "blocked_until_oracle"
    assert data["truth_matrix_allowed"] is False
    assert data["candidate_id"] == "steve_jobs_varshaphala_yumpu_candidate"
    assert data["copyright_boundary"] == "no_bulk_text_or_table_extraction"
    assert data["allowed_next_actions"]
    assert data["forbidden_actions"]


def test_yumpu_gate_is_indexed():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    packet = packets["tajika_yumpu_source_review_gate_2026_07_21"]
    assert packet["claim_status"] == "blocked_until_oracle"
    assert packet["consumer_policy"] == "research_observation_only"
