import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/tajika_steve_jobs_1984_extraction_contract_2026_07_21.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_tajika_steve_jobs_contract_keeps_blank_template_blocked():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    assert data["scope"] == "tajika_steve_jobs_1984_extraction_contract"
    assert data["claim_status"] == "blocked_until_oracle"
    assert data["truth_matrix_allowed"] is False
    assert data["source_template"].endswith("tajika_steve_jobs_1984_first_packet.json")
    assert "varsha_lagna_deg" in data["required_numeric_fields"]
    assert "tajika_yogas" in data["required_numeric_fields"]


def test_tajika_extraction_contract_is_indexed():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    packet = packets["tajika_steve_jobs_1984_extraction_contract_2026_07_21"]
    assert packet["claim_status"] == "blocked_until_oracle"
    assert packet["consumer_policy"] == "research_observation_only"
