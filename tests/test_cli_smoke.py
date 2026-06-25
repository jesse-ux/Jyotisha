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


def run_engine_text(*args: str) -> str:
    completed = subprocess.run(
        [sys.executable, str(ENGINE), *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def test_dignity_helper_uses_planet_attitude_to_sign_lord() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    import jyotish_engine

    assert jyotish_engine._get_dignity_level("Jupiter", "Virgo") == "ENEMY"
    assert jyotish_engine._get_dignity_level("Sun", "Sagittarius") == "FRIEND"


def test_dasha_accepts_birth_datetime_without_explicit_nakshatra() -> None:
    result = run_engine("dasha", *BASE_BIRTH_ARGS, "--today", "2026-01-01")
    assert "moon_nakshatra" in result
    assert len(result.get("timeline", [])) == 9
    assert result["timeline"][0]["is_balance"] is True


def test_dasha_accepts_second_for_auto_nakshatra_birth_datetime() -> None:
    birth_args = [
        "--year", "REDACTED_YEAR",
        "--month", "4",
        "--day", "17",
        "--hour", "14",
        "--minute", "45",
        "--second", "20",
        "--lat", "36.466667",
        "--lon", "114.2",
        "--tz", "8",
    ]

    result = run_engine("dasha", *birth_args, "--today", "2026-06-24")

    assert result["birth_date"] == "REDACTED_DATE"
    assert result["birth_time"] == "14:45:20"
    assert result["birth_datetime"] == "REDACTED_DATE 14:45:20"


def test_dasha_timeline_uses_full_birth_clock_for_audit_datetimes() -> None:
    moon_lon = "311.77867371832434"
    base_args = [
        "dasha",
        "--moon-lon", moon_lon,
        "--year", "REDACTED_YEAR",
        "--month", "4",
        "--day", "17",
        "--lat", "36.466667",
        "--lon", "114.2",
        "--tz", "8",
        "--today", "2026-06-24",
    ]

    midnight = run_engine(*base_args, "--hour", "0", "--minute", "0", "--second", "0")
    late = run_engine(*base_args, "--hour", "23", "--minute", "59", "--second", "59")

    assert midnight["timeline"][0]["start_datetime"].startswith("1986-05-23T07:59:50")
    assert late["timeline"][0]["start_datetime"].startswith("1986-05-24T07:59:49")
    assert midnight["timeline"][0]["start_datetime"] != late["timeline"][0]["start_datetime"]
    assert late["birth_datetime"] == "REDACTED_DATE 23:59:59"


def test_chart_accepts_second_and_preserves_birth_time_precision() -> None:
    birth_args = [
        "--year", "REDACTED_YEAR",
        "--month", "4",
        "--day", "17",
        "--hour", "14",
        "--minute", "45",
        "--lat", "36.466667",
        "--lon", "114.2",
        "--tz", "8",
    ]

    without_seconds = run_engine("chart", *birth_args)
    with_seconds = run_engine("chart", *birth_args, "--second", "20")

    assert with_seconds["birth_info"]["time"] == "14:45:20"
    assert with_seconds["birth_info"]["second"] == 20
    assert with_seconds["birth_info"]["julian_day"] > without_seconds["birth_info"]["julian_day"]


def test_chart_reports_friend_and_enemy_sign_dignity_for_user_case() -> None:
    result = run_engine(
        "chart",
        "--year", "REDACTED_YEAR",
        "--month", "4",
        "--day", "17",
        "--hour", "14",
        "--minute", "45",
        "--second", "20",
        "--lat", "36.466667",
        "--lon", "114.2",
        "--tz", "8",
    )

    assert result["planets"]["Jupiter"]["sign"] == "Virgo"
    assert result["planets"]["Jupiter"]["status"] == "入敌(Enemy Sign)"


def test_chart_table_mode_prints_readable_ascii_table() -> None:
    output = run_engine_text("chart", *BASE_BIRTH_ARGS, "--table")

    assert "Planet" in output
    assert "Sign" in output
    assert "House" in output
    assert "Ascendant" in output
    assert "Sun" in output
    assert "Moon" in output


def test_full_reading_accepts_second_and_preserves_birth_time_precision() -> None:
    result = run_engine(
        "full-reading",
        "--year", "REDACTED_YEAR",
        "--month", "4",
        "--day", "17",
        "--hour", "14",
        "--minute", "45",
        "--second", "20",
        "--lat", "36.466667",
        "--lon", "114.2",
        "--tz", "8",
        "--today", "2026-06-24",
        "--transit-date", "2026-06-24",
    )

    assert result["birth_info"]["time"] == "14:45:20"
    assert result["birth_info"]["second"] == 20
    assert result["modules"]["chart"]["birth_info"]["time"] == "14:45:20"
    assert result["modules"]["dasha"]["birth_time"] == "14:45:20"
    assert result["modules"]["dasha"]["timeline"][0]["start_datetime"].startswith("1986-05-23T22:45:10")


def test_full_reading_reports_ayanamsa_metadata_and_ai_prompt_pack() -> None:
    result = run_engine(
        "full-reading",
        "--year", "REDACTED_YEAR",
        "--month", "4",
        "--day", "17",
        "--hour", "14",
        "--minute", "45",
        "--second", "20",
        "--lat", "36.466667",
        "--lon", "114.2",
        "--tz", "8",
        "--ayanamsa", "raman",
        "--today", "2026-06-24",
        "--transit-date", "2026-06-24",
    )

    chart_birth = result["modules"]["chart"]["birth_info"]
    assert chart_birth["ayanamsa_name"] == "raman"
    assert chart_birth["ayanamsa_display"] == "Raman"
    assert chart_birth["ayanamsa"] < 23

    prompt_pack = result["ai_prompt_pack"]
    assert prompt_pack["schema_version"] == 1
    assert prompt_pack["mode"] == "jyotish_structured_prompt_pack"
    assert "Raman" in prompt_pack["prompt_zh"]
    assert "不要仅凭单一配置下结论" in prompt_pack["prompt_zh"]
    assert "references/ai-reading-workflow-prompt.md" in prompt_pack["retrieval_plan"]["local_reference_docs"]
    assert prompt_pack["evidence_snapshot"]["ayanamsa"]["name"] == "raman"
    assert prompt_pack["evidence_snapshot"]["core"]["ascendant"]["sign"] == result["chart"]["ascendant"]["sign"]
    oracle_progress = prompt_pack["evidence_snapshot"]["oracle_progress"]
    assert oracle_progress["scope"] == "external_oracle_evidence_validation"
    assert oracle_progress["valid_packets"] == 0
    assert oracle_progress["ready_for_calibration"] == 0
    assert oracle_progress["production_tuning_allowed"] is False
    assert oracle_progress["artifact_policy"] == "references/oracle/artifacts/"
    assert "external_verified" in oracle_progress["promotion_rule"]


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
