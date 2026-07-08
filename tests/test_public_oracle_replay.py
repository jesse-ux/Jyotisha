from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_public_oracle_replay_quick_matrix_runs_on_public_case() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/public_oracle_replay.py", "--quick", "--timeout", "60"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["case_count"] == 1
    assert report["summary"]["tested"] >= 10
    assert report["oracle_summary"]
    assert any(row["engine"] == "chart_d1" and row["status"] == "tested" for row in report["rows"])
    assert any(row["provider"] == "pyjhora" for row in report["expected_oracles"])
    assert any(row["engine"] == "VedAstro official full snapshot" and row["status"] == "blocked" for row in report["blocked_or_untested"])
