import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "references" / "oracle" / "three_engine_worked_example_bridge_2026_07_20.json"
INDEX = ROOT / "references" / "oracle" / "evidence_packet_index_2026_07_19.json"


def test_three_engine_worked_example_bridge_links_owner_tracks_to_intake_domains():
    data = json.loads(
        subprocess.check_output(
            ["python3", "scripts/three_engine_worked_example_bridge.py", "--date", "2026-07-20"],
            cwd=ROOT,
            text=True,
        )
    )
    assert data["scope"] == "three_engine_worked_example_bridge"
    assert data["claim_status"] == "open_queue"
    assert data["production_tuning_allowed"] is False
    tracks = {row["owner_track"]: row for row in data["owner_track_links"]}
    assert "formula_source" in tracks
    assert tracks["formula_source"]["linked_intake_domains"] == ["shadbala_component_closure"]
    assert tracks["formula_source"]["ticket_count"] >= 30
    assert tracks["formula_source"]["claim_boundary"].startswith("Bridge only")


def test_three_engine_worked_example_bridge_identifies_unlinked_tracks():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    tracks = {row["owner_track"]: row for row in data["owner_track_links"]}
    assert tracks["endpoint_contract"]["linked_intake_domains"] == []
    assert "method contract" in tracks["endpoint_contract"]["next_non_numeric_evidence"][0]
    assert data["summary"]["linked_owner_track_count"] >= 1
    assert data["summary"]["closed_mismatch_count"] == 0


def test_three_engine_worked_example_bridge_is_indexed():
    packets = {row["packet_id"]: row for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]}
    packet = packets["three_engine_worked_example_bridge_2026_07_20"]
    assert packet["domain"] == "three_engine_parity"
    assert packet["claim_status"] == "open_queue"
