#!/usr/bin/env python3
"""Compare candidate Dig Bala models against external oracle rows."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import jyotish_engine as engine  # type: ignore
import oracle_boundary_audit  # type: ignore
from shadbala import DIG_BALA_HOUSE, calc_dig_bala  # type: ignore


MODEL_NAMES = [
    "current_linear_house_model",
    "house_midpoint_angular_model",
    "bhava_madhya_angular_model",
]


def _load_oracle(path: str) -> dict[str, Any]:
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = ROOT / resolved
    return oracle_boundary_audit._load_oracle(str(resolved))


def _resolve_path(path: str) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else ROOT / candidate


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _iter_external_verified_template_cases(oracle: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for case in oracle.get("template_cases", []):
        if case.get("status") == "external_verified" and isinstance(case.get("target", {}).get("shadbala_components"), dict):
            out.append(case)
    return out


def _namespace_from_template(case: dict[str, Any]) -> Any:
    birth = case["birth"]
    settings = case.get("settings", {})
    return type(
        "Args",
        (),
        {
            "year": birth["year"],
            "month": birth["month"],
            "day": birth["day"],
            "hour": birth["hour"],
            "minute": birth.get("minute", 0),
            "second": birth.get("second", 0),
            "lat": birth["lat"],
            "lon": birth["lon"],
            "tz": birth["tz"],
            "ayanamsa": settings.get("ayanamsa", "lahiri"),
            "node_mode": settings.get("node_mode", "mean"),
        },
    )()


def _planet_lon(chart: dict[str, Any], planet: str) -> float:
    return float(chart["planets"][planet]["degree_raw"])


def _asc_lon(chart: dict[str, Any]) -> float:
    return float(chart["ascendant"]["degree_raw"])


def _whole_sign_house_midpoint(asc_lon: float, house: int) -> float:
    base = (asc_lon + (house - 1) * 30) % 360
    return (base + 15) % 360


def _angular_distance(a: float, b: float) -> float:
    diff = abs(a - b) % 360
    return min(diff, 360 - diff)


def _dig_from_strong_point(planet_lon: float, strong_point_lon: float) -> float:
    shorter_arc = _angular_distance(planet_lon, strong_point_lon)
    return max(0.0, (180.0 - shorter_arc) / 3.0)


def _best_house_midpoint_lon(asc_lon: float, planet: str) -> float:
    best_house = DIG_BALA_HOUSE.get(planet, 1)
    return _whole_sign_house_midpoint(asc_lon, best_house)


def _best_bhava_madhya_lon(chart: dict[str, Any], planet: str) -> float:
    best_house = DIG_BALA_HOUSE.get(planet, 1)
    house_row = chart["houses"].get(f"house_{best_house}", {})
    return float(house_row.get("cusp_degree", 0.0))


def build_report(oracle_file: str) -> dict[str, Any]:
    oracle = _load_oracle(oracle_file)
    cases = _iter_external_verified_template_cases(oracle)
    resolved_oracle = _resolve_path(oracle_file)
    rows: list[dict[str, Any]] = []
    model_diffs: dict[str, list[float]] = {name: [] for name in MODEL_NAMES}

    for case in cases:
        chart = engine.cmd_chart(_namespace_from_template(case))
        asc_lon = _asc_lon(chart)
        target_components = case["target"]["shadbala_components"]
        for planet, external_row in target_components.items():
            if planet not in chart["planets"] or not isinstance(external_row, dict):
                continue
            external_dig = external_row.get("dig")
            if not isinstance(external_dig, (int, float)):
                continue
            planet_lon = _planet_lon(chart, planet)
            house = int(chart["planets"][planet]["house"])
            current_linear = calc_dig_bala(planet, house) / 60.0
            house_midpoint = _dig_from_strong_point(planet_lon, _best_house_midpoint_lon(asc_lon, planet)) / 60.0
            bhava_madhya = _dig_from_strong_point(planet_lon, _best_bhava_madhya_lon(chart, planet)) / 60.0
            candidates = {
                "current_linear_house_model": current_linear,
                "house_midpoint_angular_model": house_midpoint,
                "bhava_madhya_angular_model": bhava_madhya,
            }
            diffs = {name: round(abs(value - float(external_dig)), 4) for name, value in candidates.items()}
            for name, diff in diffs.items():
                model_diffs[name].append(diff)
            rows.append(
                {
                    "case_id": case.get("id") or case.get("case_id"),
                    "planet": planet,
                    "external_dig_rupa": float(external_dig),
                    "house": house,
                    "planet_lon": round(planet_lon, 4),
                    "asc_lon": round(asc_lon, 4),
                    "current_linear_house_model": round(current_linear, 4),
                    "house_midpoint_angular_model": round(house_midpoint, 4),
                    "bhava_madhya_angular_model": round(bhava_madhya, 4),
                    "abs_diffs": diffs,
                }
            )

    avg_diffs = {
        name: round(sum(values) / len(values), 4) if values else math.inf
        for name, values in model_diffs.items()
    }
    best_model = min(avg_diffs, key=avg_diffs.get) if rows else None

    return {
        "scope": "shadbala_dig_source_of_truth_audit",
        "schema_version": 1,
        "candidate_models": MODEL_NAMES,
        "inputs": {
            "oracle_file": str(resolved_oracle.relative_to(ROOT)),
            "oracle_file_sha256": _sha256(resolved_oracle),
            "external_case_count": len(cases),
            "external_case_sources": [
                {
                    "case_id": case.get("id") or case.get("case_id"),
                    "source_artifact": case.get("evidence_packet", {}).get("metadata", {}).get("source_artifact", ""),
                    "source_artifact_sha256": _sha256(source_path)
                    if (source_artifact := case.get("evidence_packet", {}).get("metadata", {}).get("source_artifact"))
                    and (source_path := _resolve_path(source_artifact)).exists()
                    else None,
                }
                for case in cases
            ],
        },
        "summary": {
            "case_count": len(cases),
            "row_count": len(rows),
            "best_model_by_avg_abs_diff": best_model,
            "avg_abs_diff_by_model": avg_diffs,
        },
        "rows": rows,
        "boundary": (
            "This audit compares three local Dig Bala candidate models against external oracle rows. "
            "It is diagnostic only and does not modify production scoring."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--oracle-file",
        default="references/oracle/dasha_shadbala_oracle_cases.json",
    )
    parser.add_argument("--output", help="Optional JSON snapshot path.")
    args = parser.parse_args()
    report = build_report(args.oracle_file)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
