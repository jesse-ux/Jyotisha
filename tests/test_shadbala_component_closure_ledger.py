import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "references/oracle/shadbala_component_closure_ledger_2026_07_19.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_closure_ledger_builds_from_same_unit_matrix():
    data = json.loads(
        subprocess.check_output(
            ["python3", "scripts/shadbala_component_closure_ledger.py"],
            cwd=ROOT,
            text=True,
        )
    )
    assert data["scope"] == "shadbala_component_closure_ledger"
    assert data["claim_status"] == "partial"
    assert data["truth_matrix_allowed"] is False
    assert data["summary"]["row_count"] == 42
    assert data["source_matrix_hash"]
    assert data["ledger_hash"]


def test_closure_ledger_classifies_every_row_without_truth_upgrade():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    summary = data["summary"]
    assert summary["closed_observation_same_unit_count"] == 7
    assert summary["closed_as_method_variant_count"] == 8
    assert summary["open_formula_or_unit_mismatch_count"] == 27
    assert summary["open_insufficient_numeric_sources_count"] == 0
    assert (
        summary["closed_observation_same_unit_count"]
        + summary["closed_as_method_variant_count"]
        + summary["open_formula_or_unit_mismatch_count"]
        + summary["open_insufficient_numeric_sources_count"]
    ) == 42
    assert "does not assert absolute formula truth" not in data["boundary"]
    assert "worked examples" in data["boundary"]


def test_open_rows_keep_next_evidence_requirements():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    open_rows = [row for row in data["rows"] if row["closure_state"].startswith("open_")]
    closed_rows = [row for row in data["rows"] if row["closure_state"].startswith("closed_")]
    assert open_rows
    assert closed_rows
    assert all(row["required_next_evidence"] for row in open_rows)
    assert all(row["required_next_evidence"] == [] for row in closed_rows)


def test_evidence_index_registers_closure_ledger():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    assert packets["shadbala_component_closure_ledger"]["claim_status"] == "partial"
