import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "references/oracle/three_engine_mismatch_progress_ledger_2026_07_19.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_three_engine_progress_ledger_reports_attributed_node_rows():
    data = json.loads(
        subprocess.check_output(
            ["python3", "scripts/three_engine_mismatch_progress_ledger.py"],
            cwd=ROOT,
            text=True,
        )
    )
    assert data["scope"] == "three_engine_mismatch_progress_ledger"
    assert data["claim_status"] == "partial"
    assert data["truth_matrix_allowed"] is False
    assert data["summary"] == {
        "source_queue_count": 60,
        "attributed_no_tuning_count": 2,
        "remaining_open_count": 58,
    }


def test_three_engine_progress_ledger_does_not_close_queue_or_vote():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert {row["field"] for row in data["attributed_rows"]} == {"Rahu", "Ketu"}
    assert all(row["closure_state"] == "attributed_no_tuning" for row in data["attributed_rows"])
    assert "no engine majority vote is allowed" in data["boundary"]


def test_evidence_index_registers_three_engine_progress_ledger():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    assert packets["three_engine_mismatch_progress_ledger"]["claim_status"] == "partial"
