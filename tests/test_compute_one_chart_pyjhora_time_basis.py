#!/usr/bin/env python3
"""Regression tests for the PyJHora one-chart wrapper time basis."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / "venv_vedastro" / "bin" / "python3.11"
SCRIPT = ROOT / "scripts" / "_compute_one_chart.py"


def test_pyjhora_one_chart_uses_local_birth_time_for_ascendant() -> None:
    if not PYTHON.exists():
        raise AssertionError("venv_vedastro python is required for the PyJHora wrapper regression")

    chart = {
        "city": "Fengfeng",
        "lat": 36.42,
        "lon": 114.2,
        "tz": "+08:00",
        "date": "REDACTED_DATE",
        "time": "REDACTED_TIME:00",
    }
    completed = subprocess.run(
        [str(PYTHON), str(SCRIPT), json.dumps(chart)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    result = json.loads(completed.stdout.strip().splitlines()[-1])

    d1 = result["context"]["d1"]
    assert d1["ascendant"] == "Leo"
    assert 11.0 <= d1["ascendant_degree"] <= 14.5
    assert d1["planets"]["Moon"]["house"] == 7
    assert d1["planets"]["Ketu"]["house"] == 10
