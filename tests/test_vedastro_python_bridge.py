from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_vedastro_python_bridge_schema_is_declared() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/vedastro_python_bridge.py", "--print-schema"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["bridge"] == "vedastro_python_bridge"
    assert report["intended_role"] == "python_sdk_bulk_calculation_bridge"
    assert report["package_name"] == "VedAstro"
    assert "call_method" in report["operations"]
    assert "status" in report["response_contract"]
    assert report["high_value_methods"]["event_tag_catalog"]["maps_to"] == "GetAllEventDataGroupedByTag"
    assert report["high_value_methods"]["vimshottari_snapshot"]["maps_to"] == "DasaAtTime"
    assert report["high_value_methods"]["official_full_snapshot_bundle"]["maps_to"] == (
        "AllPlanetData + AllHouseData + DasaAtRange + DasaAtTime + GetCharaDasaAtTime + "
        "AllPlanetStrength + AshtakvargaLifeMap"
    )


def test_vedastro_python_bridge_returns_controlled_missing_package_status() -> None:
    env = os.environ.copy()
    env["VEDASTRO_PYTHON_FORCE_UNAVAILABLE"] = "1"
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/vedastro_python_bridge.py",
            "--method",
            "DemoMethod",
            "--params-json",
            "{\"foo\":\"bar\"}",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
        env=env,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["available"] is False
    assert report["status"] == "python_package_not_installed"
    assert report["method"] == "DemoMethod"


def test_vedastro_python_bridge_can_return_stubbed_call_without_importing_package() -> None:
    env = os.environ.copy()
    env["VEDASTRO_PYTHON_BRIDGE_STUB_RESULT"] = json.dumps(
        {
            "method": "CalculateShadbala",
            "result": {"Sun": {"Strength": 152}},
        }
    )
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/vedastro_python_bridge.py",
            "--method",
            "CalculateShadbala",
            "--params-json",
            "{\"chart_id\":\"demo\"}",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
        env=env,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["available"] is True
    assert report["status"] == "ok"
    assert report["method"] == "CalculateShadbala"
    assert report["result"]["Sun"]["Strength"] == 152
    assert report["source"] == "stubbed_bridge_result"


def test_vedastro_python_bridge_can_use_project_venv_for_live_catalog_method() -> None:
    vedastro_python = ROOT / "venv_vedastro" / "bin" / "python3.11"
    if not vedastro_python.exists():
        return

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/vedastro_python_bridge.py",
            "--method",
            "GetAllEventDataGroupedByTag",
            "--params-json",
            "{}",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["available"] is True
    assert report["status"] == "ok"
    assert report["method"] == "GetAllEventDataGroupedByTag"
    assert report["module_name"] in {"vedastro", "VedAstro"}
    assert "venv_vedastro/bin/python" in report["python_bin"]
    assert "Marriage" in report["result"] or "LendingMoney" in report["result"] or "Empty" in report["result"]


def test_vedastro_python_bridge_supports_typed_enum_and_time_arguments() -> None:
    vedastro_python = ROOT / "venv_vedastro" / "bin" / "python3.11"
    if not vedastro_python.exists():
        return

    params = {
        "kwargs": {
            "time": {
                "__vedastro_type__": "Time",
                "year": REDACTED_YEAR,
                "month": 4,
                "day": 17,
                "hour": 14,
                "minute": 49,
                "offset": 8,
                "geolocation": {
                    "__vedastro_type__": "GeoLocation",
                    "location_name": "REDACTED_PLACE",
                    "longitude": 114.46,
                    "latitude": 36.6,
                },
            }
        }
    }
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/vedastro_python_bridge.py",
            "--method",
            "PlanetNirayanaLongitude",
            "--params-json",
            json.dumps(
                {
                    "kwargs": {
                        "planetName": {"__vedastro_enum__": "PlanetName", "value": "Sun"},
                        **params["kwargs"],
                    }
                }
            ),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["available"] is True
    assert report["status"] == "ok"
    assert report["method"] == "PlanetNirayanaLongitude"
    assert isinstance(report["result"], (int, float, str, dict, list))


def test_vedastro_python_bridge_high_value_method_can_return_stubbed_result() -> None:
    env = os.environ.copy()
    env["VEDASTRO_PYTHON_BRIDGE_STUB_RESULT"] = json.dumps(
        {
            "method": "GetAllEventDataGroupedByTag",
            "result": {"Marriage": [{"Name": "GoodForMarriage"}]},
        }
    )
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/vedastro_python_bridge.py",
            "--high-value",
            "event_tag_catalog",
            "--params-json",
            "{}",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
        env=env,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["available"] is True
    assert report["status"] == "ok"
    assert report["method"] == "GetAllEventDataGroupedByTag"
    assert "Marriage" in report["result"]


def test_vedastro_python_bridge_high_value_vimshottari_snapshot_uses_positional_args() -> None:
    vedastro_python = ROOT / "venv_vedastro" / "bin" / "python3.11"
    if not vedastro_python.exists():
        return

    payload = {
        "birth_time": {
            "__vedastro_type__": "Time",
            "year": REDACTED_YEAR,
            "month": 4,
            "day": 17,
            "hour": 14,
            "minute": 49,
            "offset": 8,
            "geolocation": {
                "__vedastro_type__": "GeoLocation",
                "location_name": "REDACTED_PLACE",
                "longitude": 114.46,
                "latitude": 36.6,
            },
        },
        "check_time": {
            "__vedastro_type__": "Time",
            "year": 2026,
            "month": 1,
            "day": 1,
            "hour": 12,
            "minute": 0,
            "offset": 8,
            "geolocation": {
                "__vedastro_type__": "GeoLocation",
                "location_name": "REDACTED_PLACE",
                "longitude": 114.46,
                "latitude": 36.6,
            },
        },
        "levels": 3,
    }
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/vedastro_python_bridge.py",
            "--high-value",
            "vimshottari_snapshot",
            "--params-json",
            json.dumps(payload, ensure_ascii=False),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["available"] is True
    assert report["status"] == "ok"
    assert report["method"] == "DasaAtTime"


def test_vedastro_python_bridge_high_value_chara_snapshot_uses_positional_args() -> None:
    vedastro_python = ROOT / "venv_vedastro" / "bin" / "python3.11"
    if not vedastro_python.exists():
        return

    payload = {
        "birth_time": {
            "__vedastro_type__": "Time",
            "year": REDACTED_YEAR,
            "month": 4,
            "day": 17,
            "hour": 14,
            "minute": 49,
            "offset": 8,
            "geolocation": {
                "__vedastro_type__": "GeoLocation",
                "location_name": "REDACTED_PLACE",
                "longitude": 114.46,
                "latitude": 36.6,
            },
        },
        "check_time": {
            "__vedastro_type__": "Time",
            "year": 2026,
            "month": 1,
            "day": 1,
            "hour": 12,
            "minute": 0,
            "offset": 8,
            "geolocation": {
                "__vedastro_type__": "GeoLocation",
                "location_name": "REDACTED_PLACE",
                "longitude": 114.46,
                "latitude": 36.6,
            },
        },
    }
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/vedastro_python_bridge.py",
            "--high-value",
            "chara_dasha_snapshot",
            "--params-json",
            json.dumps(payload, ensure_ascii=False),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["available"] is True
    assert report["status"] == "ok"
    assert report["method"] == "GetCharaDasaAtTime"
