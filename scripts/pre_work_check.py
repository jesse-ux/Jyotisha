#!/usr/bin/env python3
"""One-command pre-work governance check.

Runs the lightweight guardrails that should happen before substantial work:
ledger/docs presence, git status visibility, fragment scan, remote visibility,
and focused governance tests.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
DEFAULT_COMMAND_TIMEOUT_SECONDS = 45
DEFAULT_FRAGMENT_TIMEOUT_SECONDS = 90
FOCUSED_TEST_TARGETS = [
    "tests/test_runtime_import_boundaries.py",
    "tests/test_project_fragment_governance.py",
    "tests/test_preflight_fragment_scan.py",
    "tests/test_remote_repo_visibility_check.py",
    "tests/test_pre_work_check.py",
]
EXTERNAL_ENGINE_DIAGNOSTIC_TARGET = "scripts/diagnose_external_engine_adapters.py"
PRE_WORK_DOCS = [
    "AGENTS.md",
    "docs/research/pre_work_error_ledger.md",
    "docs/research/whole_machine_fragment_sweep_2026_07_05.md",
    "docs/research/whole_machine_fragment_sweep_2026_07_14.md",
    "docs/research/whole_machine_fragment_sweep_round25_2026_06_25.md",
]


def run(args: list[str], timeout: int, env: dict[str, str] | None = None) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            args,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "returncode": None,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "error": f"timeout after {timeout}s",
        }
    return {
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "error": "" if completed.returncode == 0 else (completed.stderr or completed.stdout).strip(),
    }


def classify_status(
    docs_ok: bool,
    fragment_ok: bool,
    pytest_ok: bool,
    remote_status: str,
    external_engine_ok: bool = True,
) -> str:
    if not docs_ok or not fragment_ok or not pytest_ok or not external_engine_ok:
        return "fail"
    if remote_status == "verified":
        return "pass"
    return "pass_with_remote_blocked"


def build_report(remote_timeout: int, command_timeout: int, fragment_timeout: int, skip_tests: bool = False) -> dict[str, Any]:
    docs = {path: (ROOT / path).exists() for path in PRE_WORK_DOCS}
    git_status = run(["git", "status", "--short", "--branch"], command_timeout)
    git_remote = run(["git", "remote", "-v"], command_timeout)
    fragment = run([PYTHON, "scripts/preflight_fragment_scan.py"], fragment_timeout)
    external_engine = run([PYTHON, EXTERNAL_ENGINE_DIAGNOSTIC_TARGET, "--json"], command_timeout)
    remote = run([PYTHON, "scripts/remote_repo_visibility_check.py", "--timeout", str(remote_timeout)], command_timeout)
    remote_report: dict[str, Any] = {}
    if remote["ok"]:
        try:
            remote_report = json.loads(remote["stdout"])
        except json.JSONDecodeError as exc:
            remote_report = {"status": "blocked", "must_not_claim_synced": True, "parse_error": str(exc)}
    pytest_result = {"ok": True, "stdout": "skipped", "stderr": "", "error": ""}
    if not skip_tests:
        env = dict(os.environ)
        if fragment["ok"] and fragment.get("stdout"):
            cache = Path(tempfile.gettempdir()) / "jyotish_preflight_fragment_scan_report.json"
            cache.write_text(fragment["stdout"], encoding="utf-8")
            env["PREFLIGHT_FRAGMENT_SCAN_REPORT"] = str(cache)
        pytest_result = run([PYTHON, "-m", "pytest", "-q", *FOCUSED_TEST_TARGETS], command_timeout, env=env)
    remote_status = str(remote_report.get("status") or "blocked")
    status = classify_status(
        docs_ok=all(docs.values()),
        fragment_ok=fragment["ok"],
        pytest_ok=pytest_result["ok"],
        remote_status=remote_status,
        external_engine_ok=external_engine["ok"],
    )
    return {
        "scope": "pre_work_check",
        "status": status,
        "must_not_claim_synced": remote_report.get("must_not_claim_synced", True),
        "docs": docs,
        "git": {
            "status_ok": git_status["ok"],
            "status": git_status["stdout"],
            "remote_ok": git_remote["ok"],
            "remote": git_remote["stdout"],
        },
        "checks": {
            "fragment_scan_ok": fragment["ok"],
            "external_engine_adapters_ok": external_engine["ok"],
            "remote_visibility_status": remote_status,
            "remote_visibility_ok": remote["ok"],
            "focused_tests_ok": pytest_result["ok"],
        },
        "errors": {
            "fragment_scan": fragment["error"],
            "external_engine_adapters": external_engine["error"],
            "remote_visibility": remote["error"],
            "focused_tests": pytest_result["error"],
        },
        "focused_test_targets": FOCUSED_TEST_TARGETS,
        "external_engine_diagnostic_target": EXTERNAL_ENGINE_DIAGNOSTIC_TARGET,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--remote-timeout", type=int, default=8)
    parser.add_argument("--command-timeout", type=int, default=DEFAULT_COMMAND_TIMEOUT_SECONDS)
    parser.add_argument("--fragment-timeout", type=int, default=DEFAULT_FRAGMENT_TIMEOUT_SECONDS)
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()
    report = build_report(args.remote_timeout, args.command_timeout, args.fragment_timeout, args.skip_tests)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
