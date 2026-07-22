import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/kp_archive_numeric_extraction_result_2026_07_21.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_kp_archive_extraction_finds_partial_cusp_but_no_oracle():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    assert data["scope"] == "kp_archive_numeric_extraction_result"
    assert data["claim_status"] == "blocked_until_oracle"
    assert data["truth_matrix_allowed"] is False
    assert data["extracted_partial_numeric_fact"]["cusp"] == "11th"
    assert data["extracted_partial_numeric_fact"]["sign"] == "Sagittarius"
    assert data["extracted_partial_numeric_fact"]["degree_dms"] == "27°48'40\""
    assert data["numeric_oracle_ready"] is False


def test_kp_archive_extraction_result_is_indexed():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    packet = packets["kp_archive_numeric_extraction_result_2026_07_21"]
    assert packet["claim_status"] == "blocked_until_oracle"
    assert packet["consumer_policy"] == "research_observation_only"
