import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/shadbala_component_closure_all_rows_2026_07_23.json"


def test_all_rows_generator_merges_all_42_shadbala_components():
    data = json.loads(
        subprocess.check_output(
            ["python3", "scripts/shadbala_component_closure_all_rows.py"],
            cwd=ROOT,
            text=True,
        )
    )

    assert data["scope"] == "shadbala_component_closure_all_rows"
    assert data["summary"]["row_count"] == 42
    assert data["summary"]["component_counts"] == {
        "chesta": 7,
        "dig": 7,
        "drik": 7,
        "kala": 7,
        "naisargika": 7,
        "sthana": 7,
    }
    assert data["claim_status"] == "component_explanatory_partial"
    assert data["summary"]["truth_ready"] is False


def test_all_rows_manifest_preserves_truth_and_tuning_boundaries():
    data = json.loads(PACKET.read_text(encoding="utf-8"))

    assert data["truth_matrix_allowed"] is False
    assert data["production_tuning_allowed"] is False
    assert data["summary"]["absolute_truth_upgrade_count"] == 0
    assert data["summary"]["closed_observation_row_count"] == 7
    for row in data["rows"]:
        assert row["claim_upgrade"] == "none"
        assert row["truth_matrix_allowed"] is False
        assert row["production_tuning_allowed"] is False
        assert row["unit_contract"]
        assert row["source_evidence"]
        assert row["claim_boundary"]


def test_all_rows_manifest_keeps_chesta_as_unresolved_variant():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    chesta_rows = [row for row in data["rows"] if row["component"] == "chesta"]

    assert len(chesta_rows) == 7
    assert any(row["closure_status"] == "formula_mismatch_chesta_exception_unresolved" for row in chesta_rows)
    assert all("chesta" in row["closure_status"] for row in chesta_rows)
