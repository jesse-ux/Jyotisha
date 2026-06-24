#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Golden case regression runner for Jyotish full-reading output contracts."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import date
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


def is_non_empty(value: Any) -> bool:
    return value is not None and value != {} and value != []


def parse_date(value: str) -> date:
    return date.fromisoformat(str(value)[:10])


def current_period_covers_reference(period: Dict[str, Any], reference_date: str) -> bool:
    if not isinstance(period, dict):
        return False
    start = period.get("start") or period.get("start_date")
    end = period.get("end") or period.get("end_date")
    if not start or not end:
        return False
    ref = parse_date(reference_date)
    return parse_date(start) <= ref <= parse_date(end)


def check_quality_gates(data: Dict[str, Any], case: Dict[str, Any]) -> List[str]:
    gates = case.get("quality_gates", {})
    failures: List[str] = []
    modules = data.get("modules", {})
    if not isinstance(modules, dict):
        return ["modules must be an object"]

    min_modules = gates.get("min_modules")
    if min_modules is not None and len(modules) < min_modules:
        failures.append(f"module count too low: {len(modules)} < {min_modules}")

    for path in gates.get("non_empty_paths", []):
        try:
            value = get_path(data, path)
            if not is_non_empty(value):
                failures.append(f"empty quality path: {path}")
        except KeyError:
            failures.append(f"missing quality path: {path}")

    invariants = gates.get("invariants", {})
    if invariants.get("validation_valid") and modules.get("validation", {}).get("valid") is not True:
        failures.append("validation.valid is not true")

    expected_sav = invariants.get("ashtakavarga_sav_total")
    if expected_sav is not None:
        sav_total = modules.get("ashtakavarga", {}).get("sav", {}).get("total")
        if sav_total != expected_sav:
            failures.append(f"ashtakavarga SAV total mismatch: {sav_total} != {expected_sav}")

    min_remedy_evidence = invariants.get("min_remedies_evidence")
    if min_remedy_evidence is not None:
        evidence = modules.get("remedies", {}).get("evidence_chain", [])
        if len(evidence) < min_remedy_evidence:
            failures.append(f"remedies evidence too thin: {len(evidence)} < {min_remedy_evidence}")

    if invariants.get("dasha_current_covers_reference"):
        reference_date = case.get("input", {}).get("today")
        current = modules.get("dasha", {}).get("current_dasha", {})
        if not reference_date or not current_period_covers_reference(current, reference_date):
            failures.append("current dasha does not cover reference date")

    if invariants.get("dasa_convergence_non_empty"):
        domains = modules.get("dasa_convergence", {}).get("top_convergent_domains", [])
        if not domains:
            failures.append("dasa convergence has no top domains")

    if invariants.get("transit_has_references"):
        refs = modules.get("transit_multi_reference", {}).get("references", {})
        if len(refs) < 3:
            failures.append(f"transit references too thin: {len(refs)} < 3")

    boundaries = gates.get("boundaries", {})
    forbidden_terms = boundaries.get("forbidden_absolute_terms", [])
    if forbidden_terms:
        text = json.dumps({
            "summary": data.get("summary"),
            "warnings": data.get("warnings"),
            "remedies": modules.get("remedies"),
            "dasa_convergence": modules.get("dasa_convergence"),
        }, ensure_ascii=False)
        for term in forbidden_terms:
            if term and term in text:
                failures.append(f"forbidden absolute term found: {term}")

    return failures


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
            quality_failures = check_quality_gates(data, case)
            if quality_failures:
                case_result["passed"] = False
                case_result["failures"].extend(quality_failures)
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
