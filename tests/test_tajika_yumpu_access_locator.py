import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/tajika_yumpu_access_locator_2026_07_21.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_yumpu_access_locator_records_access_without_numeric_extraction():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    assert data["scope"] == "tajika_yumpu_access_locator"
    assert data["claim_status"] == "blocked_until_oracle"
    assert data["truth_matrix_allowed"] is False
    assert data["http_status"] == 200
    assert data["html_probe"]["steve_jobs_string_found"] is True
    assert data["numeric_extraction_status"] == "not_performed"


def test_yumpu_access_locator_is_indexed():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    packet = packets["tajika_yumpu_access_locator_2026_07_21"]
    assert packet["claim_status"] == "blocked_until_oracle"
    assert packet["consumer_policy"] == "research_observation_only"
