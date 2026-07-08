from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_flying_star_audit_outputs_linkage_chains_and_motion_points() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/flying_star_audit.py",
            "--year",
            "2000",
            "--month",
            "1",
            "--day",
            "1",
            "--hour",
            "12",
            "--minute",
            "0",
            "--lat",
            "0",
            "--lon",
            "0",
            "--tz",
            "0",
            "--age",
            "30",
            "--planets",
            "Venus,Saturn",
            "--event-house",
            "7",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["scope"] == "flying_star_audit"
    assert "D1" in report["inter_chart_linkage"]["Venus"]
    assert report["dispositor_chains"]["Venus"]
    assert report["motion_points"]["bcp"]["status"] == "available_reference"
    assert "sudarshana" in report["motion_points"]
