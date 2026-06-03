#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Golden case regression runner for Jyotish full-reading output contracts."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import Any, Dict, List

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE = os.path.join(ROOT_DIR, "scripts", "jyotish_engine.py")
DEFAULT_CASES = os.path.join(ROOT_DIR, "tests", "golden", "golden_cases.json")


def get_path(data: Dict[str, Any], dotted_path: str) -> Any:
    cur: Any = data
    for part in dotted_path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise KeyError(dotted_path)
        cur = cur[part]
    return cur


def run_full_reading(py: str, case: Dict[str, Any]) -> Dict[str, Any]:
    inp = case["input"]
    cmd = [
        py,
        ENGINE,
        "full-reading",
        "--year", str(inp["year"]),
        "--month", str(inp["month"]),
        "--day", str(inp["day"]),
        "--hour", str(inp["hour"]),
        "--minute", str(inp["minute"]),
        "--lat", str(inp["lat"]),
        "--lon", str(inp["lon"]),
        "--tz", str(inp["tz"]),
    ]
    if inp.get("today"):
        cmd.extend(["--today", inp["today"]])
    out = subprocess.check_output(cmd, text=True)
    return json.loads(out)


def run_cases(py: str, cases_path: str) -> Dict[str, Any]:
    with open(cases_path, "r", encoding="utf-8") as f:
        suite = json.load(f)
    results: List[Dict[str, Any]] = []
    for case in suite.get("cases", []):
        case_result = {"id": case.get("id"), "passed": True, "failures": []}
        try:
            data = run_full_reading(py, case)
            errors = data.get("errors", [])
            if len(errors) > case.get("max_errors", 0):
                case_result["passed"] = False
                case_result["failures"].append(f"too many errors: {len(errors)} > {case.get('max_errors', 0)}; {errors[:5]}")
            for path in case.get("expected_output_paths", []):
                try:
                    value = get_path(data, path)
                    if value is None or value == {} or value == []:
                        case_result["passed"] = False
                        case_result["failures"].append(f"empty output path: {path}")
                except KeyError:
                    case_result["passed"] = False
                    case_result["failures"].append(f"missing output path: {path}")
        except Exception as exc:
            case_result["passed"] = False
            case_result["failures"].append(str(exc))
        results.append(case_result)
    failed = [r for r in results if not r["passed"]]
    return {"valid": len(failed) == 0, "total": len(results), "failed": len(failed), "results": results}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Jyotish golden case regressions")
    parser.add_argument("--python", default=sys.executable, help="Python executable used to run jyotish_engine.py")
    parser.add_argument("--cases", default=DEFAULT_CASES, help="Path to golden_cases.json")
    args = parser.parse_args()
    result = run_cases(args.python, args.cases)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
