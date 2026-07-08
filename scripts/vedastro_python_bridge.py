#!/usr/bin/env python3
"""Thin bridge for the official VedAstro Python package.

This bridge exists to accelerate broad method coverage through the official
Python SDK while keeping the local adjudicator and REST adapter boundaries
separate. It stays deliberately thin:

- discover the real VedAstro runtime (current interpreter or local venv)
- route generic method calls into the official Python surface
- support a tiny typed-parameter contract for enums and Time/GeoLocation
- fail in a controlled way when the package is unavailable
"""

from __future__ import annotations

import argparse
import inspect
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "VedAstro"
MODULE_CANDIDATES = ("vedastro", "VedAstro")
FORCE_UNAVAILABLE_ENV = "VEDASTRO_PYTHON_FORCE_UNAVAILABLE"
STUB_RESULT_ENV = "VEDASTRO_PYTHON_BRIDGE_STUB_RESULT"
PYTHON_BIN_ENV = "VEDASTRO_PYTHON_BIN"
DEFAULT_VENV_PYTHONS = (
    ROOT / "venv_vedastro" / "bin" / "python3.11",
    ROOT / "venv_vedastro" / "bin" / "python3",
    ROOT / "venv_vedastro" / "bin" / "python",
)

CHILD_RUNNER = r"""
import contextlib
import enum
import importlib
import io
import json
import sys

MODULE_CANDIDATES = ("vedastro", "VedAstro")


def _offset_to_string(offset):
    if isinstance(offset, str):
        raw = offset.strip()
        if not raw:
            return "+00:00"
        if raw[0] in "+-" and ":" in raw:
            return raw
        try:
            offset = float(raw)
        except ValueError:
            return raw

    if isinstance(offset, (int, float)):
        sign = "+" if offset >= 0 else "-"
        absolute = abs(float(offset))
        hours = int(absolute)
        minutes = int(round((absolute - hours) * 60))
        if minutes == 60:
            hours += 1
            minutes = 0
        return f"{sign}{hours:02d}:{minutes:02d}"

    return "+00:00"


def _import_module():
    for name in MODULE_CANDIDATES:
        with contextlib.redirect_stdout(io.StringIO()):
            try:
                return name, importlib.import_module(name)
            except ModuleNotFoundError:
                continue
    return None, None


def _coerce(module, value):
    if isinstance(value, list):
        return [_coerce(module, item) for item in value]
    if isinstance(value, dict):
        enum_name = value.get("__vedastro_enum__")
        if enum_name:
            enum_type = getattr(module, enum_name)
            return getattr(enum_type, value["value"])

        type_name = value.get("__vedastro_type__")
        if type_name == "GeoLocation":
            return module.GeoLocation(
                value["location_name"],
                value["longitude"],
                value["latitude"],
            )
        if type_name == "Time":
            geolocation = _coerce(module, value["geolocation"]) if value.get("geolocation") else None
            if value.get("time_string") is not None:
                return module.Time(value["time_string"], geolocation)
            time_string = (
                f"{int(value['hour']):02d}:{int(value['minute']):02d} "
                f"{int(value['day']):02d}/{int(value['month']):02d}/{int(value['year'])} "
                f"{_offset_to_string(value.get('offset', '+00:00'))}"
            )
            return module.Time(time_string, geolocation)

        if type_name:
            target = getattr(module, type_name)
            args = [_coerce(module, item) for item in value.get("args", [])]
            kwargs = {
                key: _coerce(module, item)
                for key, item in value.get("kwargs", {}).items()
            }
            if args or kwargs:
                return target(*args, **kwargs)
            payload = {
                key: _coerce(module, item)
                for key, item in value.items()
                if not key.startswith("__")
            }
            return target(**payload)

        return {
            key: _coerce(module, item)
            for key, item in value.items()
        }
    return value


def _serialize(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, enum.Enum):
        return {
            "type": type(value).__name__,
            "name": value.name,
            "value": value.value,
        }
    if isinstance(value, (list, tuple, set)):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _serialize(item) for key, item in value.items()}
    if hasattr(value, "to_json"):
        try:
            payload = value.to_json()
            if isinstance(payload, str):
                try:
                    return json.loads(payload)
                except json.JSONDecodeError:
                    return payload
            return _serialize(payload)
        except Exception:
            pass
    if hasattr(value, "__dict__"):
        return {
            key: _serialize(item)
            for key, item in vars(value).items()
            if not key.startswith("_")
        }
    return str(value)


def _resolve_callable(module, method_name):
    parts = [part for part in method_name.split(".") if part]
    if not parts:
        raise AttributeError("empty_method_name")
    if len(parts) == 1:
        return getattr(module.Calculate, parts[0])

    current = module
    for part in parts:
        current = getattr(current, part)
    return current


def main():
    method = sys.argv[1]
    params = json.loads(sys.argv[2])
    module_name, module = _import_module()
    if module is None:
        print(json.dumps({
            "available": False,
            "status": "python_package_not_installed",
            "method": method,
            "source": "vedastro_python_bridge_child",
        }))
        return

    call_target = _resolve_callable(module, method)

    args = []
    kwargs = {}
    if isinstance(params, dict) and ("args" in params or "kwargs" in params):
        args = [_coerce(module, item) for item in params.get("args", [])]
        kwargs = {
            key: _coerce(module, item)
            for key, item in params.get("kwargs", {}).items()
        }
    elif isinstance(params, dict):
        kwargs = {
            key: _coerce(module, item)
            for key, item in params.items()
        }
    elif isinstance(params, list):
        args = [_coerce(module, item) for item in params]
    elif params is not None:
        args = [_coerce(module, params)]

    with contextlib.redirect_stdout(io.StringIO()):
        result = call_target(*args, **kwargs)

    print(json.dumps({
        "available": True,
        "status": "ok",
        "method": method,
        "module_name": module_name,
        "result": _serialize(result),
        "source": "vedastro_python_bridge",
    }))


if __name__ == "__main__":
    main()
"""


CAPABILITY_RUNNER = r"""
import contextlib
import importlib
import inspect
import io
import json

MODULE_CANDIDATES = ("vedastro", "VedAstro")


def _import_module():
    for name in MODULE_CANDIDATES:
        with contextlib.redirect_stdout(io.StringIO()):
            try:
                return name, importlib.import_module(name)
            except ModuleNotFoundError:
                continue
    return None, None


def _bucket(parameter_names, signature_text):
    lowered = [name.lower() for name in parameter_names]
    if not lowered:
        return "zero_arg"
    if lowered == ["time"]:
        return "time_only"
    if lowered == ["birthtime"]:
        return "birth_time_only"
    if lowered == ["planetname", "time"]:
        return "planet_time"
    if lowered == ["housename", "time"]:
        return "house_name_time"
    if lowered == ["housenumber", "time"]:
        return "house_number_time"
    if lowered == ["planet", "time"]:
        return "planet_alias_time"
    if lowered == ["birthtime", "checktime", "levels"]:
        return "dasha_at_time"
    if lowered == ["birthtime", "starttime", "endtime", "levels", "precisionhours"]:
        return "dasha_at_range"
    return signature_text.strip() or "unknown_signature"


def main():
    module_name, module = _import_module()
    if module is None:
        print(json.dumps({
            "available": False,
            "status": "python_package_not_installed",
            "source": "vedastro_python_bridge_child",
        }))
        return

    calculate = getattr(module, "Calculate", None)
    if calculate is None:
        print(json.dumps({
            "available": False,
            "status": "calculate_namespace_missing",
            "module_name": module_name,
            "source": "vedastro_python_bridge_child",
        }))
        return

    capabilities = []
    buckets = {}
    for name in sorted(dir(calculate)):
        if name.startswith("_"):
            continue
        obj = getattr(calculate, name)
        if not callable(obj):
            continue
        try:
            sig = inspect.signature(obj)
            signature_text = str(sig)
            parameter_names = [param.name for param in sig.parameters.values()]
        except Exception:
            signature_text = "<unknown>"
            parameter_names = []
        bucket = _bucket(parameter_names, signature_text)
        capabilities.append({
            "method": name,
            "signature": signature_text,
            "bucket": bucket,
            "parameter_names": parameter_names,
            "callable": True,
        })
        entry = buckets.setdefault(bucket, {"count": 0, "examples": []})
        entry["count"] += 1
        if len(entry["examples"]) < 10:
            entry["examples"].append(name)

    print(json.dumps({
        "available": True,
        "status": "ok",
        "module_name": module_name,
        "capabilities": capabilities,
        "summary": {
            "total_callable": len(capabilities),
            "signature_bucket_count": len(buckets),
        },
        "buckets": buckets,
        "source": "vedastro_python_bridge",
    }))


if __name__ == "__main__":
    main()
"""


def _package_available() -> bool:
    if os.environ.get(FORCE_UNAVAILABLE_ENV, "").strip().lower() in {"1", "true", "yes"}:
        return False
    return _discover_module_name() is not None


def _discover_module_name() -> str | None:
    for candidate in MODULE_CANDIDATES:
        if importlib.util.find_spec(candidate) is not None:
            return candidate
    return None


def _candidate_python_bins() -> list[str]:
    bins: list[str] = []

    configured = os.environ.get(PYTHON_BIN_ENV, "").strip()
    if configured:
        bins.append(configured)

    for candidate in DEFAULT_VENV_PYTHONS:
        if candidate.exists():
            bins.append(str(candidate))

    bins.append(sys.executable)

    seen: set[str] = set()
    ordered: list[str] = []
    for item in bins:
        if item and item not in seen:
            ordered.append(item)
            seen.add(item)
    return ordered


def _python_supports_vedastro(python_bin: str) -> bool:
    probe = (
        "import importlib.util; "
        "mods=('vedastro','VedAstro'); "
        "raise SystemExit(0 if any(importlib.util.find_spec(m) for m in mods) else 1)"
    )
    try:
        completed = subprocess.run(
            [python_bin, "-c", probe],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except OSError:
        return False
    return completed.returncode == 0


def _select_python_bin() -> str | None:
    for python_bin in _candidate_python_bins():
        if _python_supports_vedastro(python_bin):
            return python_bin
    return None


def _call_via_child_python(python_bin: str, method: str, params: dict[str, Any]) -> dict[str, Any]:
    child_env = os.environ.copy()
    completed = subprocess.run(
        [python_bin, "-c", CHILD_RUNNER, method, json.dumps(params, ensure_ascii=False)],
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
        env=child_env,
    )
    if completed.returncode != 0:
        return {
            "available": False,
            "status": "bridge_runtime_error",
            "method": method,
            "python_bin": python_bin,
            "stderr": (completed.stderr or "").strip(),
            "stdout_excerpt": (completed.stdout or "").strip()[:500],
            "source": "vedastro_python_bridge",
        }

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {
            "available": False,
            "status": "bridge_invalid_json",
            "method": method,
            "python_bin": python_bin,
            "stdout_excerpt": (completed.stdout or "").strip()[:500],
            "stderr": (completed.stderr or "").strip()[:500],
            "source": "vedastro_python_bridge",
        }

    payload["python_bin"] = python_bin
    return payload


def _list_capabilities_via_child_python(python_bin: str) -> dict[str, Any]:
    completed = subprocess.run(
        [python_bin, "-c", CAPABILITY_RUNNER],
        check=False,
        capture_output=True,
        text=True,
        timeout=240,
        env=os.environ.copy(),
    )
    if completed.returncode != 0:
        return {
            "available": False,
            "status": "bridge_runtime_error",
            "stderr": (completed.stderr or "").strip(),
            "stdout_excerpt": (completed.stdout or "").strip()[:500],
            "source": "vedastro_python_bridge",
        }
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {
            "available": False,
            "status": "bridge_invalid_json",
            "stdout_excerpt": (completed.stdout or "").strip()[:500],
            "stderr": (completed.stderr or "").strip()[:500],
            "source": "vedastro_python_bridge",
        }
    payload["python_bin"] = python_bin
    return payload


def schema() -> dict[str, Any]:
    return {
        "bridge": "vedastro_python_bridge",
        "package_name": PACKAGE_NAME,
        "module_candidates": list(MODULE_CANDIDATES),
        "intended_role": "python_sdk_bulk_calculation_bridge",
        "operations": ["call_method", "list_capabilities"],
        "request_contract": ["method", "params_json"],
        "typed_param_contract": {
            "enum": {"__vedastro_enum__": "PlanetName", "value": "Sun"},
            "geo": {
                "__vedastro_type__": "GeoLocation",
                "location_name": "San Francisco",
                "longitude": 114.46,
                "latitude": 36.6,
            },
            "time": {
                "__vedastro_type__": "Time",
                "year": 1955,
                "month": 2,
                "day": 24,
                "hour": 19,
                "minute": 15,
                "offset": 8,
                "geolocation": {
                    "__vedastro_type__": "GeoLocation",
                    "location_name": "San Francisco",
                    "longitude": 114.46,
                    "latitude": 36.6,
                },
            },
        },
        "response_contract": ["available", "status", "method", "result", "source", "python_bin"],
        "boundaries": [
            "Generic method routing only; local adjudicator remains authoritative.",
            "Do not treat Python SDK output as score/dominant label override by default.",
        ],
    }


def _missing_package_result(method: str) -> dict[str, Any]:
    return {
        "available": False,
        "status": "python_package_not_installed",
        "method": method,
        "reason": (
            f"Official Python package {PACKAGE_NAME} is not installed in the current runtime "
            "or detected project venv."
        ),
        "source": "vedastro_python_bridge",
    }


def call_method(method: str, params: dict[str, Any]) -> dict[str, Any]:
    stub = os.environ.get(STUB_RESULT_ENV, "").strip()
    if stub:
        payload = json.loads(stub)
        return {
            "available": True,
            "status": "ok",
            "method": payload.get("method") or method,
            "result": payload.get("result"),
            "source": "stubbed_bridge_result",
        }

    if os.environ.get(FORCE_UNAVAILABLE_ENV, "").strip().lower() in {"1", "true", "yes"}:
        return _missing_package_result(method)

    python_bin = _select_python_bin()
    if not python_bin:
        return _missing_package_result(method)
    return _call_via_child_python(python_bin, method, params)


def list_capabilities() -> dict[str, Any]:
    if os.environ.get(FORCE_UNAVAILABLE_ENV, "").strip().lower() in {"1", "true", "yes"}:
        return _missing_package_result("list_capabilities")
    python_bin = _select_python_bin()
    if not python_bin:
        return _missing_package_result("list_capabilities")
    return _list_capabilities_via_child_python(python_bin)


def call_high_value(method_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    if method_key == "event_tag_catalog":
        return call_method("GetAllEventDataGroupedByTag", {})

    if method_key == "planet_longitude":
        planet = payload["planet"]
        time = payload["time"]
        return call_method(
            "PlanetNirayanaLongitude",
            {
                "args": [
                    {"__vedastro_enum__": "PlanetName", "value": planet},
                    time,
                ]
            },
        )

    if method_key == "vimshottari_snapshot":
        birth_time = payload["birth_time"]
        check_time = payload["check_time"]
        levels = int(payload.get("levels", 3))
        return call_method("DasaAtTime", {"args": [birth_time, check_time, levels]})

    if method_key == "chara_dasha_snapshot":
        birth_time = payload["birth_time"]
        check_time = payload["check_time"]
        return call_method("GetCharaDasaAtTime", {"args": [birth_time, check_time]})

    if method_key == "official_full_snapshot_bundle":
        birth_time = payload["birth_time"]
        check_time = payload["check_time"]
        start_time = payload["start_time"]
        end_time = payload["end_time"]
        levels = int(payload.get("levels", 3))
        precision_hours = int(payload.get("precision_hours", 100))
        planets = list(payload.get("planets") or [])
        houses = list(payload.get("houses") or [])

        chart_core: dict[str, Any] = {}
        house_core: dict[str, Any] = {}
        section_statuses: dict[str, str] = {}

        for planet in planets:
            report = call_method(
                "AllPlanetData",
                {
                    "args": [
                        {"__vedastro_enum__": "PlanetName", "value": str(planet)},
                        birth_time,
                    ]
                },
            )
            chart_core[str(planet)] = {
                "Status": "Pass" if report.get("status") == "ok" else "Fail",
                "Payload": {"AllPlanetData": report.get("result")} if report.get("status") == "ok" else report,
            }
        if chart_core:
            section_statuses["chart_core"] = "ok"

        for house in houses:
            report = call_method(
                "AllHouseData",
                {
                    "args": [
                        {"__vedastro_enum__": "HouseName", "value": str(house)},
                        birth_time,
                    ]
                },
            )
            house_core[str(house)] = {
                "Status": "Pass" if report.get("status") == "ok" else "Fail",
                "Payload": {"AllHouseData": report.get("result")} if report.get("status") == "ok" else report,
            }
        if house_core:
            section_statuses["house_core"] = "ok"

        dasha_report = call_method(
            "DasaAtRange",
            {"args": [birth_time, start_time, end_time, levels, precision_hours]},
        )
        vimshottari_report = call_method(
            "DasaAtTime",
            {"args": [birth_time, check_time, levels]},
        )
        chara_report = call_method(
            "GetCharaDasaAtTime",
            {"args": [birth_time, check_time]},
        )
        strength_report = call_method("AllPlanetStrength", {"args": [birth_time]})
        ashtakavarga_report = call_method("AshtakvargaLifeMap", {"args": [birth_time]})

        snapshot_sections = {
            "chart_core": chart_core,
            "house_core": house_core,
            "dasha_all": {
                "Status": "Pass" if dasha_report.get("status") == "ok" else "Fail",
                "Payload": {"DasaAtRange": dasha_report.get("result")} if dasha_report.get("status") == "ok" else dasha_report,
            },
            "vimshottari_now": {
                "Status": "Pass" if vimshottari_report.get("status") == "ok" else "Fail",
                "Payload": {"DasaAtTime": vimshottari_report.get("result")} if vimshottari_report.get("status") == "ok" else vimshottari_report,
            },
            "chara_dasha_now": {
                "Status": "Pass" if chara_report.get("status") == "ok" else "Fail",
                "Payload": {"GetCharaDasaAtTime": chara_report.get("result")} if chara_report.get("status") == "ok" else chara_report,
            },
            "shadbala": {
                "Status": "Pass" if strength_report.get("status") == "ok" else "Fail",
                "Payload": {"AllPlanetStrength": strength_report.get("result")} if strength_report.get("status") == "ok" else strength_report,
            },
            "ashtakavarga": {
                "Status": "Pass" if ashtakavarga_report.get("status") == "ok" else "Fail",
                "Payload": {"AshtakvargaLifeMap": ashtakavarga_report.get("result")} if ashtakavarga_report.get("status") == "ok" else ashtakavarga_report,
            },
        }

        for section_name in ("dasha_all", "vimshottari_now", "chara_dasha_now", "shadbala", "ashtakavarga"):
            section_statuses[section_name] = "ok" if snapshot_sections[section_name]["Status"] == "Pass" else "fail"

        filled_sections = [name for name, status in section_statuses.items() if status == "ok"]
        overall_status = "ok" if filled_sections else "blocked"
        if filled_sections and len(filled_sections) != len(section_statuses):
            overall_status = "partial"

        return {
            "available": bool(filled_sections),
            "status": overall_status,
            "method": "official_full_snapshot_bundle",
            "result": {
                "snapshot_sections": snapshot_sections,
                "section_statuses": section_statuses,
                "coverage": {
                    "source_mode": "official_python_bridge_bundle",
                    "filled_sections": filled_sections,
                    "planet_count": len(chart_core),
                    "house_count": len(house_core),
                },
            },
            "source": "vedastro_python_bridge",
        }

    return {
        "available": False,
        "status": "unsupported_high_value_method",
        "method": method_key,
        "source": "vedastro_python_bridge",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="VedAstro Python bridge")
    parser.add_argument("--print-schema", action="store_true")
    parser.add_argument("--method", default="")
    parser.add_argument("--params-json", default="{}")
    parser.add_argument("--high-value", default="")
    parser.add_argument("--list-capabilities", action="store_true")
    args = parser.parse_args()

    if args.print_schema:
        result = schema()
        result["high_value_methods"] = {
            "event_tag_catalog": {
                "maps_to": "GetAllEventDataGroupedByTag",
                "request_contract": [],
            },
            "planet_longitude": {
                "maps_to": "PlanetNirayanaLongitude",
                "request_contract": ["planet", "time"],
            },
            "vimshottari_snapshot": {
                "maps_to": "DasaAtTime",
                "request_contract": ["birth_time", "check_time", "levels?"],
            },
            "chara_dasha_snapshot": {
                "maps_to": "GetCharaDasaAtTime",
                "request_contract": ["birth_time", "check_time"],
            },
            "official_full_snapshot_bundle": {
                "maps_to": (
                    "AllPlanetData + AllHouseData + DasaAtRange + DasaAtTime + "
                    "GetCharaDasaAtTime + AllPlanetStrength + AshtakvargaLifeMap"
                ),
                "request_contract": [
                    "birth_time",
                    "check_time",
                    "start_time",
                    "end_time",
                    "levels?",
                    "precision_hours?",
                    "planets[]",
                    "houses[]",
                ],
            },
        }
    elif args.list_capabilities:
        result = list_capabilities()
    elif args.high_value:
        params = json.loads(args.params_json or "{}")
        result = call_high_value(args.high_value, params)
    else:
        params = json.loads(args.params_json or "{}")
        result = call_method(args.method, params)

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
