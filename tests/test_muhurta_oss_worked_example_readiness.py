import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/muhurta_oss_worked_example_readiness_2026_07_23.json"


def test_muhurta_oss_readiness_keeps_candidates_below_verdict_threshold():
    data = json.loads(
        subprocess.check_output(
            ["python3", "scripts/muhurta_oss_worked_example_readiness.py"],
            cwd=ROOT,
            text=True,
        )
    )
    assert data["scope"] == "muhurta_oss_worked_example_readiness"
    assert data["claim_status"] == "candidate_source_matrix"
    assert data["truth_matrix_allowed"] is False
    assert data["final_muhurta_verdict_allowed"] is False
    assert data["summary"]["numeric_oracle_ready_count"] == 0


def test_muhurta_oss_readiness_covers_full_factor_surface_without_oracle_upgrade():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    factors = set(data["summary"]["factor_surface"])
    assert {"tarabala", "chandrabalam", "rahu_kalam", "yamaganda", "gulika", "abhijit_muhurta", "panchaka"} <= factors
    assert all(row["reuse_policy"] != "runtime_dependency" for row in data["rows"])
    assert "do not authorize a final auspicious-date verdict" in data["boundary"]
