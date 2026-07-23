import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/shadbala_component_closure_batch1_2026_07_23.json"


def test_batch1_generator_outputs_row_level_closure_for_priority_components():
    data = json.loads(
        subprocess.check_output(
            ["python3", "scripts/shadbala_component_closure_batch1.py"],
            cwd=ROOT,
            text=True,
        )
    )

    assert data["scope"] == "shadbala_component_closure_batch1"
    assert data["claim_status"] == "component_explanatory_partial"
    assert data["truth_matrix_allowed"] is False
    assert data["production_tuning_allowed"] is False
    assert data["summary"]["row_count"] == 21
    assert data["summary"]["component_counts"] == {
        "dig": 7,
        "drik": 7,
        "naisargika": 7,
    }


def test_batch1_closes_only_naisargika_as_same_unit_observation():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    statuses = data["summary"]["closure_status_counts"]

    assert statuses["within_tolerance_observation_closed"] == 7
    assert statuses["formula_mismatch_angular_reference_unresolved"] == 7
    assert statuses["formula_mismatch_aspect_model_unresolved"] == 7
    assert data["summary"]["absolute_truth_upgrade_count"] == 0
    assert data["summary"]["blocked_or_unresolved_row_count"] == 14


def test_batch1_rows_have_source_unit_and_boundary_contracts():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    for row in data["rows"]:
        assert row["ticket_id"].startswith("shadbala.")
        assert row["source_formula"].startswith("shadbala_")
        assert row["unit_contract"]
        assert row["source_evidence"]
        assert row["known_variants"]
        assert row["claim_upgrade"] == "none"
        assert row["truth_matrix_allowed"] is False
        assert row["production_tuning_allowed"] is False
        assert "no absolute Shadbala truth" in row["claim_boundary"]


def test_batch1_dig_rows_preserve_diagnostic_model_without_selecting_truth():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    dig_rows = [row for row in data["rows"] if row["component"] == "dig"]

    assert len(dig_rows) == 7
    assert any(
        row["dig_model_diagnostic"].get("best_local_candidate_model") == "bhava_madhya_angular_model"
        for row in dig_rows
    )
    assert all(
        row["closure_status"] == "formula_mismatch_angular_reference_unresolved"
        for row in dig_rows
    )
