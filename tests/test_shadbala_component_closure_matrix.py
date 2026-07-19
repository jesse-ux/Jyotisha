import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "references/oracle/shadbala_component_closure_matrix_2026_07_19.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_matrix_generator_outputs_42_component_rows():
    data = json.loads(subprocess.check_output(["python3", "scripts/shadbala_component_closure_matrix.py"], cwd=ROOT, text=True))
    assert data["scope"] == "shadbala_component_closure_matrix"
    assert data["summary"]["row_count"] == 42
    assert data["summary"]["jyotishganit_raw_available_count"] == 42
    assert data["summary"]["absolute_parity_ready_count"] == 0
    assert data["production_tuning_allowed"] is False
    assert data["truth_matrix_allowed"] is False


def test_matrix_artifact_links_existing_xalen_vp_jain_and_provenance():
    data = json.loads(MATRIX.read_text(encoding="utf-8"))
    assert data["claim_status"] == "partial"
    assert data["matrix_hash"]
    assert data["sources"]["jyotishganit_raw"] == "references/oracle/jyotishganit_shadbala_surface_probe_steve_jobs_2026_07_19.json"
    assert data["sources"]["xalen_delta_report"].endswith("xalen_shadbala_av_component_delta_report_2026_07_19.json")
    assert all(row["closure_status"] == "component_observation_ready_unit_parity_pending" for row in data["rows"])


def test_matrix_has_all_six_components_for_visible_planets():
    data = json.loads(MATRIX.read_text(encoding="utf-8"))
    by_planet = {}
    for row in data["rows"]:
        by_planet.setdefault(row["planet"], set()).add(row["component"])
    expected = {"Sthanabala", "Digbala", "Kaalabala", "Cheshtabala", "Naisargikabala", "Drikbala"}
    assert set(by_planet) == {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
    assert all(components == expected for components in by_planet.values())


def test_evidence_index_registers_shadbala_component_matrix():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    packets = {row["packet_id"]: row for row in index["packets"]}
    assert packets["shadbala_component_closure_matrix"]["claim_status"] == "partial"
