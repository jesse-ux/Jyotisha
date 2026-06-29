#!/usr/bin/env python3
"""Build a compact closure report for VedAstro strict ingestion."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def _run_json(args: list[str], env: dict[str, str] | None = None) -> dict[str, Any]:
    completed = subprocess.run(
        [PYTHON, "scripts/vedastro_service_adapter.py", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
        env=env,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    return json.loads(completed.stdout)


def build_report() -> dict[str, Any]:
    schema = _run_json(["--print-schema"])

    unconfigured_env = os.environ.copy()
    unconfigured_env.pop("VEDASTRO_API_ENDPOINT", None)
    unconfigured_env.pop("VEDASTRO_ENABLE_NETWORK", None)
    unconfigured_env["JYOTISH_SKIP_LOCAL_ENV"] = "1"
    unconfigured = _run_json(
        ["--range-scan", "--domain", "marriage", "--case", "beijing_first_use_demo", "--start-date", "2026-01-01", "--end-date", "2031-01-01"],
        env=unconfigured_env,
    )

    preview_env = os.environ.copy()
    preview_env["VEDASTRO_API_ENDPOINT"] = "https://example.invalid/vedastro"
    preview_env.pop("VEDASTRO_ENABLE_NETWORK", None)
    preview_env["JYOTISH_SKIP_LOCAL_ENV"] = "1"
    preview = _run_json(
        ["--range-scan", "--domain", "wealth", "--case", "beijing_first_use_demo", "--start-date", "2026-01-01", "--end-date", "2031-01-01"],
        env=preview_env,
    )

    life_event_graph_test = subprocess.run(
        [
            PYTHON,
            "-m",
            "pytest",
            "tests/test_life_event_graph_v1.py",
            "-q",
            "-k",
            "vedastro or strict_workflow_accepts_adapter_range_scan_result_without_manual_repackaging",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    life_event_graph_accepts_external_window = life_event_graph_test.returncode == 0

    return {
        "scope": "vedastro_ingestion_closure_pack",
        "schema_version": 1,
        "summary": {
            "range_scan_domains": sorted(schema["range_scan_event_allowlist"].keys()),
            "schema_declares_allowlist": "range_scan_event_allowlist" in schema,
            "unconfigured_status": unconfigured["status"],
            "network_preview_status": preview["status"],
            "life_event_graph_accepts_external_window": life_event_graph_accepts_external_window,
            "global_live_closure_blocked": True,
        },
        "rows": [
            {
                "kind": "schema",
                "allowlist_domains": sorted(schema["range_scan_event_allowlist"].keys()),
                "coverage": schema["vedastro_calculation_coverage"],
            },
            {
                "kind": "blocked_boundary",
                "status": unconfigured["status"],
                "domain": unconfigured["request_preview"]["domain"],
                "event_method": unconfigured["request_preview"]["vedastro_event_method"],
            },
            {
                "kind": "network_preview",
                "status": preview["status"],
                "domain": preview["request_preview"]["domain"],
                "event_method": preview["request_preview"]["vedastro_event_method"],
            },
            {
                "kind": "life_event_graph",
                "status": "pass" if life_event_graph_accepts_external_window else "fail",
                "test_selector": (
                    "tests/test_life_event_graph_v1.py "
                    "-k 'vedastro or strict_workflow_accepts_adapter_range_scan_result_without_manual_repackaging'"
                ),
            },
        ],
        "boundary": (
            "This pack reuses the existing VedAstro adapter schema, blocked boundary, network-preview boundary, "
            "and Life Event Graph ingestion tests. It does not claim live official endpoint closure."
        ),
        "next_actions": [
            "Keep using the adapter allowlist contract instead of inventing a second filtering layer.",
            "Keep the live path blocked until a real endpoint-backed smoke is configured.",
            "Only promote allowlisted external_window signals into strict workflow secondary evidence.",
        ],
    }


def main() -> None:
    report = build_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
