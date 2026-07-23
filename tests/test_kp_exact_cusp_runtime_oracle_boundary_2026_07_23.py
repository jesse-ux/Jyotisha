import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/kp_exact_cusp_runtime_oracle_boundary_2026_07_23.json"


def test_kp_runtime_oracle_boundary_builder_keeps_truth_blocked():
    data = json.loads(
        subprocess.check_output(
            ["python3", "scripts/kp_exact_cusp_runtime_oracle_boundary.py"],
            cwd=ROOT,
            text=True,
        )
    )

    assert data["scope"] == "kp_exact_cusp_runtime_oracle_boundary"
    assert data["runtime_raw_status"] == "single_engine_observation_ready"
    assert data["public_numeric_oracle_status"] == "blocked_missing_complete_worked_example"
    assert data["claim_status"] == "calculable_displayable_public_oracle_blocked"
    assert data["truth_matrix_allowed"] is False
    assert data["production_tuning_allowed"] is False


def test_kp_boundary_references_fresh_vedicastro_raw_and_missing_fields():
    data = json.loads(PACKET.read_text(encoding="utf-8"))

    assert data["runtime_raw"]["artifact"] == "references/oracle/vedicastro_kp_house_cusp_probe_steve_jobs_2026_07_23.json"
    assert data["runtime_raw"]["house_count"] == 12
    assert data["runtime_raw"]["fields"] == [
        "cusp_longitude",
        "star_lord",
        "sub_lord",
        "sub_sub_lord",
    ]
    assert data["required_oracle_fields"] == [
        "birth_or_question_input",
        "ayanamsa",
        "house_system_or_kp_cusp_method",
        "exact_cusp_longitudes",
        "cusp_star_lord",
        "cusp_sub_lord",
        "cusp_sub_sub_lord",
    ]
    assert data["complete_numeric_oracle_count"] == 0


def test_kp_boundary_keeps_candidate_sources_as_queue_only():
    data = json.loads(PACKET.read_text(encoding="utf-8"))

    assert {row["id"] for row in data["candidate_sources"]} >= {
        "archive_kp_reader_candidate",
        "astrosage_kp_cuspal_sub_lord",
        "vedicastro_python_surface",
    }
    for row in data["candidate_sources"]:
        assert row["promotion"] == "queue_only"
        assert row["missing"]
