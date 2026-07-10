#!/usr/bin/env python3
"""One-command smoke check for ordinary AI-app / skill invocation."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def _run(args: list[str], *, timeout: int = 120, env: dict[str, str] | None = None) -> dict[str, Any]:
    completed = subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
        env=env,
    )
    return {
        "command": " ".join(args),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def _entrypoint_env() -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "JYOTISH_SKIP_LOCAL_ENV": "1",
            "VEDASTRO_API_ENDPOINT": "",
            "VEDASTRO_ENABLE_NETWORK": "",
            "VEDASTRO_TIMEOUT_SECONDS": "",
        }
    )
    return env


def _engine_summary(report: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    engines = report.get("engines") if isinstance(report.get("engines"), dict) else {}
    for name, details in engines.items():
        if not isinstance(details, dict):
            continue
        summary[name] = {
            "status": details.get("status"),
            "readiness_blockers": details.get("readiness_blockers")
            or ([details["missing_dependency"]] if details.get("missing_dependency") else []),
            "license_boundary": details.get("license_boundary"),
        }
    return summary


def _runtime_summary(report: dict[str, Any]) -> dict[str, Any]:
    runtime = report.get("runtime_mode") if isinstance(report.get("runtime_mode"), dict) else {}
    return {
        "mode": runtime.get("mode"),
        "official_ready": runtime.get("official_ready"),
        "expected_fallback_status": runtime.get("expected_fallback_status"),
    }


def _strict_summary(report: dict[str, Any]) -> dict[str, Any]:
    strict = report.get("strict_workflow") if isinstance(report.get("strict_workflow"), dict) else {}
    return {
        "triggered": strict.get("triggered"),
        "primary_route": strict.get("primary_route"),
        "routes_available": strict.get("routes_available"),
        "source": strict.get("source"),
    }


def main() -> int:
    pytest_check = _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_user_invocation_acceptance_contract.py",
            "-k",
            "not one_command_user_invocation_acceptance_check",
        ],
        timeout=180,
    )
    entrypoint = _run(
        [
            sys.executable,
            "scripts/vedastro_user_entrypoint.py",
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
            "0.0",
            "--lon",
            "0.0",
            "--tz",
            "0",
            "--question",
            "请先生成 guided_topics 并推荐我最值得看的问题",
            "--themes",
            "career,marriage,wealth",
            "--reference-date",
            "2026-07-06",
            "--format",
            "json",
        ],
        env=_entrypoint_env(),
    )
    adapters = _run([sys.executable, "scripts/diagnose_external_engine_adapters.py", "--json"], timeout=120)

    errors: list[str] = []
    entrypoint_report: dict[str, Any] = {}
    adapter_report: dict[str, Any] = {}
    if pytest_check["returncode"] != 0:
        errors.append("user_invocation_pytest_failed")
    if entrypoint["returncode"] != 0:
        errors.append("user_entrypoint_failed")
    else:
        try:
            entrypoint_report = json.loads(entrypoint["stdout"])
        except json.JSONDecodeError:
            errors.append("user_entrypoint_invalid_json")
    if adapters["returncode"] != 0:
        errors.append("external_adapter_diagnostic_failed")
    else:
        try:
            adapter_report = json.loads(adapters["stdout"])
        except json.JSONDecodeError:
            errors.append("external_adapter_diagnostic_invalid_json")

    required_entrypoint_paths = [
        ("strict_workflow", "triggered"),
        ("strict_workflow", "routes_available"),
        ("runtime_mode", "expected_fallback_status"),
        ("honesty_boundary", "all_641_methods_executed"),
    ]
    for path in required_entrypoint_paths:
        cursor: Any = entrypoint_report
        for key in path:
            cursor = cursor.get(key) if isinstance(cursor, dict) else None
        if cursor in (None, [], ""):
            errors.append(f"missing_entrypoint_{'_'.join(path)}")

    usable_adapter_statuses = {"pass", "partial", "complete"}
    if adapter_report.get("status") not in usable_adapter_statuses:
        errors.append("external_adapter_status_unusable")

    result = {
        "scope": "user_invocation_acceptance_check",
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "checks": {
            "user_invocation_tests": pytest_check["returncode"] == 0,
            "guided_topics_entrypoint": entrypoint["returncode"] == 0 and not any(e.startswith("missing_entrypoint_") for e in errors),
            "external_adapter_diagnostics": adapter_report.get("status") in usable_adapter_statuses,
        },
        "entrypoint_runtime_mode": _runtime_summary(entrypoint_report),
        "entrypoint_strict_workflow": _strict_summary(entrypoint_report),
        "external_adapter_status": adapter_report.get("status"),
        "external_engines": _engine_summary(adapter_report),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
