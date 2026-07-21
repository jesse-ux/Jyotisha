import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "references/oracle/shadbala_component_closure_queue_v2_2026_07_19.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_queue_generator_builds_42_field_level_tickets():
    data = json.loads(
        subprocess.check_output(
            ["python3", "scripts/shadbala_component_closure_queue_v2.py"],
            cwd=ROOT,
            text=True,
        )
    )
    assert data["scope"] == "shadbala_component_closure_queue_v2"
    assert data["claim_status"] == "partial"
    assert data["production_tuning_allowed"] is False
    assert data["summary"]["ticket_count"] == 42
    assert data["summary"]["formula_or_unit_mismatch_count"] == 27
    assert data["summary"]["method_variant_count"] == 8
    assert data["summary"]["within_1_virupa_observation_count"] == 7


def test_queue_artifact_attaches_source_unit_variant_and_owner():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    ticket = next(row for row in data["tickets"] if row["planet"] == "Sun" and row["component"] == "dig")
    assert ticket["unit_contract"]
    assert ticket["known_variants"]
    assert ticket["next_evidence_owner"] in {
        "worked_example_numeric_oracle",
        "formula_source_arbitration",
        "method_variant_decision",
        "ready_for_tolerance_freeze",
    }
    assert ticket["closure_status"] != "absolute_parity_ready"
    assert ticket["claim_boundary"].startswith("Do not promote")


def test_queue_has_component_hotspot_summary():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    hotspots = {row["component"]: row for row in data["component_hotspots"]}
    assert set(hotspots) == {"sthana", "dig", "kala", "chesta", "naisargika", "drik"}
    assert hotspots["naisargika"]["within_1_virupa_observation_count"] == 7
    assert hotspots["dig"]["formula_or_unit_mismatch_count"] >= 1


def test_evidence_index_registers_queue_v2():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    packets = {row["packet_id"]: row for row in index["packets"]}
    assert packets["shadbala_component_closure_queue_v2"]["claim_status"] == "partial"
