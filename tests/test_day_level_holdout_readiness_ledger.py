import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "references/real_case_calibration/day_level_holdout_readiness_ledger_2026_07_19.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_holdout_readiness_script_keeps_unlabeled_pilot_blocked():
    data = json.loads(
        subprocess.check_output(
            ["python3", "scripts/day_level_holdout_readiness_ledger.py"],
            cwd=ROOT,
            text=True,
        )
    )
    assert data["scope"] == "day_level_holdout_readiness_ledger"
    assert data["claim_status"] == "blocked"
    assert data["production_tuning_allowed"] is False
    assert data["truth_matrix_allowed"] is False
    assert data["current"]["candidate_annotation_count"] == 9
    assert data["current"]["frozen_final_count"] == 0


def test_holdout_readiness_counts_real_remaining_frozen_labels():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert data["remaining"] == {"positive_needed": 20, "negative_needed": 80}
    assert data["required"] == {
        "minimum_frozen_positive": 20,
        "minimum_frozen_negative": 80,
    }
    assert "cannot be used as negative intervals" in data["blocked_reason"]
    assert "No day/month timing claim" in data["boundary"]


def test_evidence_index_registers_holdout_readiness():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    assert packets["day_level_holdout_readiness_ledger"]["claim_status"] == "blocked"
