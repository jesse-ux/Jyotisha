#!/usr/bin/env python3
"""Production smoke check for Jyotisha web deployment."""
from __future__ import annotations

import argparse
import json
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def fetch(url: str, timeout: float) -> tuple[int, str, float]:
    started = time.monotonic()
    request = Request(url, headers={"User-Agent": "jyotisha-production-smoke/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8", "replace"), time.monotonic() - started
    except HTTPError as error:
        return error.code, error.read().decode("utf-8", "replace"), time.monotonic() - started
    except URLError as error:
        raise RuntimeError(str(error.reason)) from error


def check(base_url: str, timeout: float, expected_git_sha: str | None = None) -> dict:
    base = base_url.rstrip("/")
    checks: list[dict] = []

    status, body, elapsed = fetch(f"{base}/", timeout)
    checks.append(
        {
            "name": "homepage",
            "ok": status == 200 and ("Jyotisha" in body or "账户与出生资料" in body),
            "status": status,
            "latency_ms": round(elapsed * 1000),
        }
    )

    status, body, elapsed = fetch(f"{base}/api/health", timeout)
    health = json.loads(body) if body.strip().startswith("{") else {}
    checks.append(
        {
            "name": "health",
            "ok": (
                status in {200, 503}
                and health.get("status") in {"ok", "degraded", "blocked"}
                and (not expected_git_sha or health.get("deployment", {}).get("gitCommit") == expected_git_sha)
            ),
            "status": status,
            "latency_ms": round(elapsed * 1000),
            "health_status": health.get("status"),
            "checks": sorted((health.get("checks") or {}).keys()),
            "deployment_git_commit": health.get("deployment", {}).get("gitCommit"),
        }
    )

    return {
        "base_url": base,
        "ok": all(item["ok"] for item in checks),
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="https://jyotisha.chat")
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument("--expected-git-sha")
    args = parser.parse_args()
    try:
        report = check(args.base_url, args.timeout, args.expected_git_sha)
    except Exception as error:  # noqa: BLE001 - CLI smoke should report compact failure.
        report = {"base_url": args.base_url, "ok": False, "error": str(error)}
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
