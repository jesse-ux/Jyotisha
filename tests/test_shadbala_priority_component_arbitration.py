import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/shadbala_priority_component_arbitration_2026_07_22.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_priority_arbitration_covers_naisargika_dig_drik():
    data = json.loads(
        subprocess.check_output(
            ["python3", "scripts/shadbala_priority_component_arbitration.py"],
            cwd=ROOT,
            text=True,
        )
    )
    assert data["scope"] == "shadbala_priority_component_arbitration"
    assert data["claim_status"] == "partial"
    rows = {row["component"]: row for row in data["components"]}
    assert set(rows) == {"naisargika", "dig", "drik"}
    assert rows["naisargika"]["closure_status"] == "observation_tolerance_ready"
    assert rows["dig"]["closure_status"] == "formula_source_arbitration_required"
    assert rows["drik"]["closure_status"] == "formula_source_arbitration_required"
    assert data["truth_matrix_allowed"] is False


def test_priority_arbitration_preserves_no_absolute_truth_upgrade():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    assert data["summary"]["absolute_truth_upgrade_count"] == 0
    for row in data["components"]:
        assert row["claim_upgrade"] == "none"
        assert row["next_action"]
        assert row["source_formula"]


def test_priority_arbitration_is_indexed():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    packet = packets["shadbala_priority_component_arbitration_2026_07_22"]
    assert packet["claim_status"] == "partial"
    assert packet["consumer_policy"] == "research_observation_only"
