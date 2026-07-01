#!/usr/bin/env python3
"""Report whether the current runtime is fast fallback or VedAstro official mode."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

try:
    from scripts.local_env import load_local_env
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from local_env import load_local_env


ROOT = Path(__file__).resolve().parents[1]
FAST_TIMEOUT_THRESHOLD_SECONDS = 5.0


def _bool_env(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _timeout_seconds() -> float:
    raw = os.environ.get("VEDASTRO_TIMEOUT_SECONDS", "").strip()
    if not raw:
        return 4.0
    try:
        return float(raw)
    except ValueError:
        return 4.0


def build_report() -> dict:
    load_local_env(ROOT)
    endpoint = os.environ.get("VEDASTRO_API_ENDPOINT", "").strip()
    network_enabled = _bool_env("VEDASTRO_ENABLE_NETWORK")
    timeout_seconds = _timeout_seconds()
    has_api_key = bool(os.environ.get("VEDASTRO_API_KEY", "").strip())
    missing = []
    if not endpoint:
        missing.append("VEDASTRO_API_ENDPOINT")
    if not network_enabled:
        missing.append("VEDASTRO_ENABLE_NETWORK=1")
    if timeout_seconds <= FAST_TIMEOUT_THRESHOLD_SECONDS:
        missing.append("VEDASTRO_TIMEOUT_SECONDS>5")
    official_ready = not missing
    mode = "official_extended" if official_ready else "fast_local_fallback"
    return {
        "mode": mode,
        "official_ready": official_ready,
        "endpoint_configured": bool(endpoint),
        "network_enabled": network_enabled,
        "timeout_seconds": timeout_seconds,
        "has_api_key": has_api_key,
        "missing": missing,
        "expected_fallback_status": (
            "none_if_official_endpoint_responds"
            if official_ready
            else "official_snapshot_budget_exhausted_or_endpoint_blocked"
        ),
        "next_step": (
            "Run full-reading or strict_workflow; verify vedastro_official.status is ok/partial."
            if official_ready
            else "Copy .env.official.example to .env.local and fill endpoint/network settings for official mode."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = parser.parse_args()
    report = build_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 0
    print(f"VedAstro runtime mode: {report['mode']}")
    print(f"official_ready: {str(report['official_ready']).lower()}")
    print(f"endpoint_configured: {str(report['endpoint_configured']).lower()}")
    print(f"network_enabled: {str(report['network_enabled']).lower()}")
    print(f"timeout_seconds: {report['timeout_seconds']}")
    print(f"has_api_key: {str(report['has_api_key']).lower()}")
    if report["missing"]:
        print("missing:")
        for item in report["missing"]:
            print(f"  - {item}")
    print(f"expected_fallback_status: {report['expected_fallback_status']}")
    print(f"next_step: {report['next_step']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

