import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "references/oracle/jyotishganit_mismatch_attribution_queue_2026_07_19.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_comparison_d4_alias_is_not_counted_as_missing_local_schema():
    out = subprocess.check_output(["python3", "scripts/jyotishganit_vs_local_field_comparison.py"], cwd=ROOT, text=True)
    data = json.loads(out)
    mismatches = [r for r in data["rows"] if r["status"] == "mismatch"]
    assert all(not (r["section"] == "D4" and r["local_sign"] is None) for r in mismatches)


def test_mismatch_attribution_queue_marks_partial_not_truth():
    data = json.loads(QUEUE.read_text(encoding="utf-8"))
    assert data["scope"] == "jyotishganit_mismatch_attribution_queue"
    assert data["claim_status"] == "partial"
    assert data["production_tuning_allowed"] is False
    assert data["truth_matrix_allowed"] is False
    assert data["summary"]["mismatch_count"] >= 1
    assert all(row["attribution_status"] == "queued" for row in data["rows"])


def test_evidence_index_registers_mismatch_attribution_queue():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    packets = {row["packet_id"]: row for row in index["packets"]}
    assert packets["jyotishganit_mismatch_attribution_queue"]["claim_status"] == "partial"
