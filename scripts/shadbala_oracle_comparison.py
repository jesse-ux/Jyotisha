#!/usr/bin/env python3
"""Compare local Shadbala absolute values against external oracle packets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import oracle_boundary_audit


ROOT = Path(__file__).resolve().parents[1]
VIRUPAS_PER_RUPA = 60.0


def _load_oracle(path: str) -> dict[str, Any]:
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = ROOT / resolved
    return oracle_boundary_audit._load_oracle(str(resolved))


def _find_case(oracle: dict[str, Any], case_id: str) -> dict[str, Any]:
    for key in ("template_cases", "shadbala_cases"):
        for case in oracle.get(key, []):
            if case.get("id") == case_id or case.get("case_id") == case_id:
                return case
    raise KeyError(f"Unknown Shadbala oracle case: {case_id}")


def _normalize_planet_rows(rows: dict[str, Any]) -> dict[str, Any]:
    comparison: dict[str, Any] = {}
    max_abs_total_delta = 0.0
    within_total_tolerance = 0

    for planet, row in rows.items():
        local_total = row.get("engine_total_rupa")
        oracle_total = row.get("external_total_rupa")
        diff_total = row.get("total_rupa_delta")
        abs_diff_total = row.get("total_abs_delta_rupa")
        if isinstance(abs_diff_total, (int, float)):
            max_abs_total_delta = max(max_abs_total_delta, float(abs_diff_total))
        if row.get("total_within_tolerance") is True:
            within_total_tolerance += 1

        component_rows = {}
        for component, component_row in (row.get("component_deltas") or {}).items():
            local_rupa = component_row.get("engine_rupa")
            if isinstance(local_rupa, (int, float)):
                local_rupa = round(float(local_rupa) / VIRUPAS_PER_RUPA, 4)
            oracle_rupa = component_row.get("external_rupa")
            diff_rupa = (
                round(local_rupa - float(oracle_rupa), 4)
                if isinstance(local_rupa, (int, float)) and isinstance(oracle_rupa, (int, float))
                else None
            )
            component_rows[component] = {
                "oracle_rupa": oracle_rupa,
                "local_rupa": local_rupa,
                "diff_rupa": diff_rupa,
                "abs_diff_rupa": round(abs(diff_rupa), 4) if diff_rupa is not None else None,
                "tolerance_rupa": component_row.get("tolerance_rupa"),
                "within_tolerance": (
                    abs(diff_rupa) <= float(component_row.get("tolerance_rupa"))
                    if diff_rupa is not None and isinstance(component_row.get("tolerance_rupa"), (int, float))
                    else component_row.get("within_tolerance")
                ),
            }

        comparison[planet] = {
            "oracle_total_rupa": oracle_total,
            "local_total_rupa": local_total,
            "diff_total_rupa": diff_total,
            "abs_diff_total_rupa": abs_diff_total,
            "total_tolerance_rupa": row.get("total_tolerance_rupa"),
            "total_within_tolerance": row.get("total_within_tolerance"),
            "components": component_rows,
        }

    return {
        "comparison": comparison,
        "summary": {
            "planet_count": len(comparison),
            "planets_within_total_tolerance": within_total_tolerance,
            "max_abs_total_delta_rupa": round(max_abs_total_delta, 4),
        },
    }


def compare_case(oracle_file: str, case_id: str) -> dict[str, Any]:
    oracle = _load_oracle(oracle_file)
    case = _find_case(oracle, case_id)

    if not isinstance(case.get("target", {}).get("shadbala_components"), dict):
        raise ValueError(f"Case {case_id} is missing target.shadbala_components")

    raw = oracle_boundary_audit._template_shadbala_comparison(case)
    if raw.get("status") != "compared":
        raise RuntimeError(f"Unable to compare case {case_id}: {raw.get('status')}")

    normalized = _normalize_planet_rows(raw.get("planets", {}))
    return {
        "scope": "shadbala_absolute_oracle_comparison",
        "schema_version": 1,
        "case_id": case.get("id") or case.get("case_id"),
        "status": case.get("status"),
        "source": case.get("source"),
        "birth": case.get("birth", {}),
        "settings": case.get("settings", {}),
        "comparison": normalized["comparison"],
        "summary": normalized["summary"],
        "global_scaling_check": raw.get("global_scaling_check", {}),
        "component_tolerances": raw.get("component_tolerances", {}),
        "total_tolerance_rupa": raw.get("total_tolerance_rupa"),
        "boundary": (
            "This entrypoint compares local absolute Rupas against external component-level oracle rows. "
            "It is diagnostic evidence, not permission to apply a global scaling factor."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare a Shadbala oracle packet against local engine output")
    parser.add_argument("--oracle-file", default="references/oracle/dasha_shadbala_oracle_cases.json")
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args()

    report = compare_case(args.oracle_file, args.case_id)
    if args.format == "markdown":
        lines = [
            "# Shadbala Absolute Oracle Comparison",
            "",
            f"- case_id: `{report['case_id']}`",
            f"- status: `{report['status']}`",
            f"- ayanamsa: `{report['settings'].get('ayanamsa')}`",
            f"- planet_count: `{report['summary']['planet_count']}`",
            f"- max_abs_total_delta_rupa: `{report['summary']['max_abs_total_delta_rupa']}`",
            "",
            "## Per-Planet Totals",
            "",
            "| Planet | Oracle | Local | Diff | Within Tolerance |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
        for planet, row in report["comparison"].items():
            lines.append(
                f"| {planet} | {row['oracle_total_rupa']} | {row['local_total_rupa']} | "
                f"{row['diff_total_rupa']} | {row['total_within_tolerance']} |"
            )
        print("\n".join(lines))
        return

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
