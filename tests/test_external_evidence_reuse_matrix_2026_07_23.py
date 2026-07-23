import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/external_evidence_reuse_matrix_2026_07_23.json"


def test_external_evidence_reuse_matrix_separates_code_reuse_from_truth_upgrade():
    data = json.loads(
        subprocess.check_output(
            ["python3", "scripts/external_evidence_reuse_matrix_2026_07_23.py"],
            cwd=ROOT,
            text=True,
        )
    )
    assert data["claim_status"] == "reuse_plan_only"
    assert data["truth_matrix_allowed"] is False
    assert data["summary"]["ready_to_upgrade_count"] == 0
    assert data["summary"]["open_source_can_help_count"] == 4


def test_external_evidence_reuse_matrix_keeps_holdout_human_blocked():
    data = json.loads(PACKET.read_text())
    rows = {row["gap"]: row for row in data["rows"]}
    holdout = rows["timing / birth-time rectification holdout"]
    assert holdout["can_open_source_help"] is False
    assert "independent human positive labels" in holdout["still_missing"]
    assert rows["KP 12 cusp exact longitude"]["current_status"] == "blocked_until_key_terms_version"
    assert data["boundary"].startswith("Open-source and local fragments can reduce")
