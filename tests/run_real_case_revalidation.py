#!/usr/bin/env python3
"""Revalidate public real-person chart fixtures against the local engine.

This is a chart-calculation regression gate, not an event_prediction_accuracy
claim. It checks sign-level and optional degree-level agreement for public
reference cases, while keeping known controversial_reference rows visible in
the JSON report.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "scripts" / "jyotish_engine.py"
PUBLIC_CASES_RELATIVE = "tests/celebrity_cases.json"
INDASTRO_CASES_RELATIVE = "tests/indastro_cases.json"
PUBLIC_CASES = ROOT / PUBLIC_CASES_RELATIVE
INDASTRO_CASES = ROOT / INDASTRO_CASES_RELATIVE

DEFAULT_MIN_PASS_RATE = 0.98
DEFAULT_DEGREE_TOLERANCE = 1.0
CONTROVERSIAL_HINTS = [
    "内部矛盾",
    "需进一步验证",
    "存在重大偏差",
    "存在约",
    "边界案例",
]


def load_cases(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_engine(case: dict[str, Any], python: str) -> dict[str, Any]:
    cmd = [
        python,
        str(ENGINE),
        "chart",
        "--year",
        str(case["year"]),
        "--month",
        str(case["month"]),
        "--day",
        str(case["day"]),
        "--hour",
        str(case["hour"]),
        "--minute",
        str(case["minute"]),
        "--lat",
        str(case["lat"]),
        "--lon",
        str(case["lon"]),
        "--tz",
        str(case["tz"]),
    ]
    completed = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=45,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    return json.loads(completed.stdout)


def is_controversial(case: dict[str, Any]) -> bool:
    note = case.get("tz_note", "")
    return any(hint in note for hint in CONTROVERSIAL_HINTS)


def add_check(
    checks: list[dict[str, Any]],
    label: str,
    expected: Any,
    actual: Any,
    *,
    gated: bool,
    tolerance: float | None = None,
) -> None:
    if expected in (None, ""):
        return
    if tolerance is None:
        passed = actual == expected
    else:
        passed = actual is not None and abs(float(actual) - float(expected)) <= tolerance
    checks.append(
        {
            "label": label,
            "expected": expected,
            "actual": actual,
            "passed": passed,
            "gated": gated,
        }
    )


def validate_public_case(case: dict[str, Any], chart: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    planets = chart.get("planets", {})
    add_check(checks, "lagna_sign", case.get("known_lagna"), chart.get("ascendant", {}).get("sign"), gated=True)
    add_check(checks, "sun_sign", case.get("known_sun_sign"), planets.get("Sun", {}).get("sign"), gated=True)
    add_check(checks, "moon_sign", case.get("known_moon_sign"), planets.get("Moon", {}).get("sign"), gated=True)
    return summarize_case(case, "public_reference", checks)


def validate_indastro_case(case: dict[str, Any], chart: dict[str, Any], tolerance: float) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    planets = chart.get("planets", {})
    gated = not is_controversial(case)
    category = "controversial_reference" if not gated else "public_reference"
    asc = chart.get("ascendant", {})
    sun = planets.get("Sun", {})
    moon = planets.get("Moon", {})

    add_check(checks, "lagna_sign", case.get("expected_lagna"), asc.get("sign"), gated=gated)
    add_check(checks, "sun_sign", case.get("expected_sun"), sun.get("sign"), gated=gated)
    add_check(checks, "moon_sign", case.get("expected_moon"), moon.get("sign"), gated=gated)
    add_check(checks, "lagna_degree", case.get("expected_lagna_degree"), asc.get("degree_in_sign"), gated=False, tolerance=tolerance)
    add_check(checks, "sun_degree", case.get("expected_sun_degree"), sun.get("degree_in_sign"), gated=False, tolerance=tolerance)
    add_check(checks, "moon_degree", case.get("expected_moon_degree"), moon.get("degree_in_sign"), gated=False, tolerance=tolerance)

    result = summarize_case(case, category, checks)
    result["source"] = case.get("source", "Indastro.com")
    result["note"] = case.get("tz_note", "")
    return result


def summarize_case(case: dict[str, Any], category: str, checks: list[dict[str, Any]]) -> dict[str, Any]:
    gated = [check for check in checks if check["gated"]]
    return {
        "id": case["id"],
        "name": case["name"],
        "category": category,
        "passed_checks": sum(1 for check in checks if check["passed"]),
        "total_checks": len(checks),
        "gated_passed_checks": sum(1 for check in gated if check["passed"]),
        "gated_total_checks": len(gated),
        "checks": checks,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for case in load_cases(PUBLIC_CASES):
        chart = run_engine(case, args.python)
        results.append(validate_public_case(case, chart))
    for case in load_cases(INDASTRO_CASES):
        chart = run_engine(case, args.python)
        results.append(validate_indastro_case(case, chart, args.degree_tolerance))

    total_checks = sum(item["total_checks"] for item in results)
    passed_checks = sum(item["passed_checks"] for item in results)
    gated_total_checks = sum(item["gated_total_checks"] for item in results)
    gated_passed_checks = sum(item["gated_passed_checks"] for item in results)
    pass_rate = gated_passed_checks / gated_total_checks if gated_total_checks else 1.0
    failures = [
        {
            "id": item["id"],
            "name": item["name"],
            "category": item["category"],
            "failed_checks": [check for check in item["checks"] if check["gated"] and not check["passed"]],
        }
        for item in results
        if any(check["gated"] and not check["passed"] for check in item["checks"])
    ]
    controversial = [item for item in results if item["category"] == "controversial_reference"]

    return {
        "valid": pass_rate >= args.min_pass_rate and not failures,
        "scope": "public real-person chart revalidation; not event_prediction_accuracy",
        "min_pass_rate": args.min_pass_rate,
        "pass_rate": round(pass_rate, 4),
        "passed_checks": passed_checks,
        "total_checks": total_checks,
        "gated_passed_checks": gated_passed_checks,
        "gated_total_checks": gated_total_checks,
        "controversial_reference_cases": len(controversial),
        "failures": failures,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run public real-case Jyotish chart revalidation")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--min-pass-rate", type=float, default=DEFAULT_MIN_PASS_RATE)
    parser.add_argument("--degree-tolerance", type=float, default=DEFAULT_DEGREE_TOLERANCE)
    parser.add_argument("--summary", action="store_true", help="Print a compact human-readable line before JSON")
    args = parser.parse_args()

    report = build_report(args)
    if args.summary:
        print(
            "真实案例复验: "
            f"gated={report['gated_passed_checks']}/{report['gated_total_checks']} "
            f"all={report['passed_checks']}/{report['total_checks']} "
            f"controversial={report['controversial_reference_cases']}"
        )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        raise SystemExit(0)
