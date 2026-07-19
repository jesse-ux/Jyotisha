import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_jyotishganit_vs_local_comparison_outputs_sign_rows_and_hash():
    out = subprocess.check_output(["python3", "scripts/jyotishganit_vs_local_field_comparison.py"], cwd=ROOT, text=True)
    data = json.loads(out)
    assert data["scope"] == "jyotishganit_vs_local_field_comparison"
    assert data["claim_status"] == "observation_only"
    assert data["production_tuning_allowed"] is False
    assert data["truth_matrix_allowed"] is False
    assert data["summary"]["row_count"] >= 32
    assert data["comparison_hash"]
    assert {row["section"] for row in data["rows"]} == {"D2", "D4", "D9", "D10"}
    assert data["coverage"]["panchanga_jyotishganit"] is True
    assert data["coverage"]["BAV_SAV_jyotishganit"] is True
    assert data["coverage"]["Shadbala_jyotishganit"] is False


def test_d1_d60_generic_gap_queue_lists_all_generic_only_rows():
    data = json.loads((ROOT / "references/oracle/d1_d60_generic_gap_queue_2026_07_19.json").read_text(encoding="utf-8"))
    assert data["scope"] == "d1_d60_generic_gap_queue"
    assert data["claim_status"] == "partial"
    assert data["production_tuning_allowed"] is False
    assert len(data["generic_only_divisions"]) == 40
    assert "D13" in data["generic_only_divisions"]
    assert "D59" in data["generic_only_divisions"]
    assert "external_worked_example" in data["required_closure_fields"]


def test_evidence_index_registers_comparison_and_generic_gap_queue():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    packets = {row["packet_id"]: row for row in index["packets"]}
    assert packets["jyotishganit_vs_local_field_comparison"]["claim_status"] == "observation_only"
    assert packets["d1_d60_generic_gap_queue"]["claim_status"] == "partial"
