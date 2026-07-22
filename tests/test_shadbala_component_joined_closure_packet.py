import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/shadbala_component_joined_closure_packet_2026_07_21.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_joined_closure_generator_attaches_pyjhora_rows_to_all_42_tickets():
    data = json.loads(
        subprocess.check_output(
            ["python3", "scripts/shadbala_component_joined_closure.py"],
            cwd=ROOT,
            text=True,
        )
    )
    assert data["scope"] == "shadbala_component_joined_closure_packet"
    assert data["claim_status"] == "partial"
    assert data["truth_matrix_allowed"] is False
    assert data["summary"]["joined_ticket_count"] == 42
    assert data["summary"]["pyjhora_component_rows_joined"] == 42
    assert data["summary"]["absolute_truth_upgrade_count"] == 0


def test_stable_components_are_grouped_before_harder_components():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    priority = [row["component"] for row in data["component_priority"]]
    assert priority[:3] == ["naisargika", "dig", "drik"]
    assert priority[-3:] == ["chesta", "sthana", "kala"]
    rows = {row["component"]: row for row in data["component_priority"]}
    assert rows["naisargika"]["recommended_next_action"] == "freeze_observation_tolerance_after_second_case"
    assert rows["chesta"]["recommended_next_action"] == "preserve_method_variant"


def test_joined_rows_keep_formula_unit_method_variant_statuses():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    statuses = {row["closure_bucket"] for row in data["joined_rows"]}
    assert {"within_tolerance", "formula_or_unit_mismatch", "method_variant"} <= statuses
    for row in data["joined_rows"]:
        assert row["pyjhora_workbuddy_virupa"] is not None
        assert row["claim_upgrade"] == "none"


def test_joined_closure_packet_is_indexed():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    packet = packets["shadbala_component_joined_closure_packet_2026_07_21"]
    assert packet["claim_status"] == "partial"
    assert packet["consumer_policy"] == "research_observation_only"
