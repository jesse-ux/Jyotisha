#!/usr/bin/env python3
"""CLI smoke tests for critical Jyotish engine commands."""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path

from tests.run_golden_cases import run_cases

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "scripts" / "jyotish_engine.py"
GOLDEN_CASES = ROOT / "tests" / "golden" / "golden_cases.json"
BASE_BIRTH_ARGS = [
    "--year", "1990",
    "--month", "1",
    "--day", "1",
    "--hour", "12",
    "--minute", "0",
    "--lat", "39.9",
    "--lon", "116.4",
    "--tz", "8",
]


def run_engine(*args: str) -> dict:
    completed = subprocess.run(
        [sys.executable, str(ENGINE), *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def test_dasha_accepts_birth_datetime_without_explicit_nakshatra() -> None:
    result = run_engine("dasha", *BASE_BIRTH_ARGS, "--today", "2026-01-01")
    assert "moon_nakshatra" in result
    assert len(result.get("timeline", [])) == 9
    assert result["timeline"][0]["is_balance"] is True


def test_varga_cli_outputs_d9_and_d10() -> None:
    result = run_engine("varga", *BASE_BIRTH_ARGS, "--d9", "--d10")
    charts = result.get("divisional_charts", {})
    assert "D9_Navamsa" in charts
    assert "D10_Dasamsa" in charts
    assert "Moon" in charts["D9_Navamsa"]


def test_ashtakavarga_cli_keeps_sav_invariant() -> None:
    result = run_engine("ashtakavarga", *BASE_BIRTH_ARGS)
    assert result["sav"]["total"] == 337
    assert result["sav"]["valid"] is True
    assert result["all_bav_valid"] is True


def test_audit_capabilities_cli_validates_registry() -> None:
    result = run_engine("audit-capabilities", "--mode", "validate")
    assert result.get("valid") is True


def test_full_reading_golden_cases_cover_user_ready_output() -> None:
    result = run_cases(sys.executable, str(GOLDEN_CASES))
    assert result["valid"] is True, result
    assert result["total"] >= 3


def test_yoga_logic_validation_tolerates_algorithmic_yogas_without_rule_id() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    import validate_logic_v2

    results = [
        {"rule_id": "bvr_vosi_precise", "name": "Vosi Yoga"},
        {"id": "bvr_sunaphaa_precise", "name": "Sunapha Yoga"},
        {"name": "Algorithmic Solar Yoga"},
    ]

    assert validate_logic_v2.extract_skill_rule_ids(results) == {
        "bvr_vosi_precise",
        "bvr_sunaphaa_precise",
    }


def test_yoga_logic_validation_import_does_not_shadow_project_modules() -> None:
    before = list(sys.path)
    sys.path.insert(0, str(ROOT / "scripts"))
    import validate_logic_v2  # noqa: F401

    assert not sys.path[0].endswith(".workbuddy/skills/jyotish-vedic-astrology/scripts")
    sys.path[:] = before


def test_pytest_import_guard_restores_project_scripts_first() -> None:
    before = list(sys.path)
    try:
        sys.path.insert(0, str(ROOT / ".workbuddy" / "skills" / "jyotish-vedic-astrology" / "scripts"))

        import tests.conftest as conftest

        importlib.reload(conftest)
        assert sys.path[0] == str(ROOT / "scripts")
        assert str(ROOT / "scripts") == conftest.SCRIPTS
        assert conftest.WORKBUDDY_SKILL_SCRIPTS == ".workbuddy/skills/jyotish-vedic-astrology/scripts"
    finally:
        sys.path[:] = before
