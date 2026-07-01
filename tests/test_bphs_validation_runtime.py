#!/usr/bin/env python3
"""Runtime checks for BPHS validation and D9 entrypoint consistency."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "scripts" / "jyotish_engine.py"
BASE_BIRTH_ARGS = [
    "--year",
    "1990",
    "--month",
    "1",
    "--day",
    "1",
    "--hour",
    "12",
    "--minute",
    "0",
    "--lat",
    "39.9",
    "--lon",
    "116.4",
    "--tz",
    "8",
]


def _run_engine(*args: str) -> dict:
    completed = subprocess.run(
        [sys.executable, str(ENGINE), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def test_validate_bphs_invariants_uses_repo_varga_and_reports_zero_failures() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/validate_bphs_invariants.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "失败: 0" in completed.stdout
    assert ".workbuddy/skills/jyotish-vedic-astrology/scripts" not in completed.stdout


def test_varga_cli_d9_uses_same_navamsa_mapping_as_varga_full() -> None:
    short = _run_engine("varga", *BASE_BIRTH_ARGS, "--d9")["divisional_charts"]["D9_Navamsa"]
    full = _run_engine("varga-full", *BASE_BIRTH_ARGS, "--divisions", "9")["D9_Navamsa"]

    assert short["ascendant"] == full["Ascendant"]["sign"]
    for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
        assert short[planet]["sign"] == full[planet]["sign"]
