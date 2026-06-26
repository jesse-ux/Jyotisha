#!/usr/bin/env python3
"""Build a combined external-oracle boundary report for Dasha and Shadbala.

The report is intentionally diagnostic. It records whether external references
are strong enough to tune production constants. Single PDF dates and incomplete
Shadbala totals are treated as boundaries, not calibration authority.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import dasha_reference_audit  # noqa: E402
import jyotish_engine as engine  # noqa: E402


SHADBALA_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
ORACLE_TEMPLATE_READY_STATUSES = {"external_verified"}
SHADBALA_COMPONENT_FIELD_MAP = {
    "sthana": "sthana_bala",
    "dig": "dig_bala",
    "kala": "kala_bala",
    "chesta": "chesta_bala",
    "naisargika": "naisargika_bala",
    "drik": "drik_bala",
}
SHADBALA_COMPONENT_TOLERANCES_RUPA = {
    "sthana": 0.1,
    "dig": 0.5,
    "kala": 0.5,
    "chesta": 1.0,
    "naisargika": 0.05,
    "drik": 1.5,
}
SHADBALA_TOTAL_TOLERANCE_RUPA = 1.0


def _resolve_path(path: str) -> str:
    if os.path.isabs(path):
        return path
    return os.path.join(ROOT_DIR, path)


def _load_oracle(path: str) -> dict[str, Any]:
    with open(_resolve_path(path), "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if data.get("schema_version") != 1:
        raise ValueError("Unsupported oracle schema_version")
    return data


def _namespace_from_birth(birth: dict[str, Any], **extra: Any) -> argparse.Namespace:
    payload = {
        "year": int(birth["year"]),
        "month": int(birth["month"]),
        "day": int(birth["day"]),
        "hour": int(birth["hour"]),
        "minute": int(birth["minute"]),
        "second": int(birth.get("second", 0) or 0),
        "lat": float(birth["lat"]),
        "lon": float(birth["lon"]),
        "tz": float(birth["tz"]),
        "node_mode": birth.get("node_mode", "mean"),
    }
    payload.update(extra)
    return argparse.Namespace(**payload)


def _audit_dasha_case(case: dict[str, Any]) -> dict[str, Any]:
    target = case.get("target", {})
    args = _namespace_from_birth(
        case["birth"],
        target_start_date=target["vimshottari_start_date"],
        target_source=target.get("source", "external_reference"),
    )
    report = dasha_reference_audit.build_report(args)
    return {
        "case_id": case["case_id"],
        "reference_kind": case.get("reference_kind"),
        "privacy": case.get("privacy"),
        "engine_moon_lon": report["engine"]["moon_lon"],
        "engine_nakshatra": report["engine"]["nakshatra"],
        "engine_start_lord": report["engine"]["start_lord"],
        "engine_start_datetime": report["engine"]["start_datetime"],
        "target_source": report["target_reference"]["source"],
        "target_start_date": report["target_reference"]["start_date"],
        "date_delta_days": report["target_reference"]["date_delta_days"],
        "exact_delta_days": report["target_reference"]["exact_delta_days"],
        "required_moon_delta_degrees": report["target_reference"]["required_moon_delta_degrees"],
        "calibration_decision": case.get("calibration_policy", "do_not_tune_single_reference"),
        "finding": report["finding"],
    }


def _component_totals(planet: dict[str, Any]) -> dict[str, float]:
    sthana = planet.get("sthana_bala", {})
    kala = planet.get("kala_bala", {})
    return {
        "sthana_bala": round(float(sthana.get("total", 0.0)), 4),
        "dig_bala": round(float(planet.get("dig_bala", 0.0)), 4),
        "kala_bala": round(float(kala.get("total", 0.0)), 4),
        "chesta_bala": round(float(planet.get("chesta_bala", 0.0)), 4),
        "naisargika_bala": round(float(planet.get("naisargika_bala", 0.0)), 4),
        "drik_bala": round(float(planet.get("drik_bala", 0.0)), 4),
    }


def _audit_shadbala_case(case: dict[str, Any]) -> dict[str, Any]:
    args = _namespace_from_birth(case["birth"])
    result = engine.cmd_shadbala(args)
    if "error" in result:
        raise RuntimeError(result["error"])

    target = case.get("target", {})
    component_targets = target.get("component_targets")
    target_authority = target.get("authority")
    if component_targets and target_authority == "external_oracle":
        component_status = "component_targets_external_oracle"
    elif component_targets:
        component_status = "component_targets_sample_only"
        target_authority = target_authority or "sample_only_not_external_oracle"
    else:
        component_status = "missing_component_targets"
        target_authority = target_authority or "missing_external_oracle"

    totals: dict[str, Any] = {}
    for name in SHADBALA_PLANETS:
        planet = result.get("planets", {}).get(name, {})
        if not planet:
            continue
        totals[name] = {
            "total_rupas": round(float(planet.get("total_rupas", 0.0)), 4),
            "total_virupas": round(float(planet.get("total_virupas", 0.0)), 4),
            "min_required": round(float(planet.get("min_required", 0.0)), 4),
            "rank": planet.get("rank"),
            "components": _component_totals(planet),
        }

    return {
        "case_id": case["case_id"],
        "reference_kind": case.get("reference_kind"),
        "privacy": case.get("privacy"),
        "engine_method": result.get("method", ""),
        "target_source": target.get("source", "external_reference"),
        "component_oracle_status": component_status,
        "target_authority": target_authority,
        "calibration_decision": case.get("calibration_policy", "component_oracle_required"),
        "engine_totals": totals,
        "finding": (
            "Shadbala external calibration requires component-level oracle rows; "
            "do not apply a global scaling factor to match one total."
        ),
    }


def _angular_delta_degrees(left: float, right: float) -> float:
    return (left - right + 180.0) % 360.0 - 180.0


def _audit_longitude_case(case: dict[str, Any]) -> dict[str, Any]:
    chart, _asc_idx, _jd, ayanamsa = engine._compute_chart_from_args(_namespace_from_birth(case["birth"]))
    if chart is None:
        raise RuntimeError("Swiss Ephemeris is required for longitude oracle audit")

    target = case.get("target", {})
    threshold_arcsec = float(target.get("threshold_arcsec", 60.0))
    comparisons: dict[str, Any] = {}
    max_abs_delta_arcsec = 0.0

    for planet_name, target_position in target.get("positions", {}).items():
        engine_position = chart.get("planets", {}).get(planet_name, {})
        if not engine_position:
            comparisons[planet_name] = {
                "status": "missing_engine_position",
                "target_sign": target_position.get("sign"),
                "target_sidereal_longitude": target_position.get("sidereal_longitude"),
            }
            continue

        engine_lon = float(engine_position.get("degree_raw", 0.0))
        target_lon = float(target_position["sidereal_longitude"])
        delta_degrees = _angular_delta_degrees(engine_lon, target_lon)
        abs_delta_arcsec = abs(delta_degrees) * 3600.0
        max_abs_delta_arcsec = max(max_abs_delta_arcsec, abs_delta_arcsec)
        comparisons[planet_name] = {
            "status": "compared",
            "engine_sign": engine_position.get("sign"),
            "target_sign": target_position.get("sign"),
            "engine_sidereal_longitude": round(engine_lon, 8),
            "target_sidereal_longitude": round(target_lon, 8),
            "delta_degrees": round(delta_degrees, 8),
            "abs_delta_arcsec": round(abs_delta_arcsec, 4),
            "within_threshold": abs_delta_arcsec <= threshold_arcsec,
        }

    return {
        "case_id": case["case_id"],
        "reference_kind": case.get("reference_kind"),
        "privacy": case.get("privacy"),
        "target_source": target.get("source", "external_reference"),
        "target_ayanamsa": target.get("ayanamsa"),
        "target_node_mode": target.get("node_mode"),
        "engine_ayanamsa": round(float(ayanamsa), 8),
        "threshold_arcsec": threshold_arcsec,
        "max_abs_delta_arcsec": round(max_abs_delta_arcsec, 4),
        "within_threshold": max_abs_delta_arcsec <= threshold_arcsec,
        "calibration_decision": case.get("calibration_policy", "external_position_reference_only"),
        "comparisons": comparisons,
        "finding": (
            "External longitude rows can explain ephemeris drift, but Dasha/Shadbala tuning still "
            "requires explicit Dasha boundary and Shadbala component targets."
        ),
    }


def _missing_target_fields(value: Any, prefix: str = "target") -> list[str]:
    missing: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            missing.extend(_missing_target_fields(child, f"{prefix}.{key}"))
    elif value is None:
        missing.append(prefix)
    return missing


def _audit_template_case(case: dict[str, Any]) -> dict[str, Any]:
    status = case.get("status", "template_only")
    target = case.get("target", {})
    missing = _missing_target_fields(target)
    return {
        "case_id": case.get("id") or case.get("case_id"),
        "status": status,
        "source": case.get("source"),
        "privacy": case.get("privacy"),
        "settings": case.get("settings", {}),
        "missing_target_fields": missing,
        "ready_for_calibration": status in ORACLE_TEMPLATE_READY_STATUSES and not missing,
        "verification_note": case.get("verification_note", ""),
    }


def _namespace_from_template(case: dict[str, Any]) -> argparse.Namespace:
    birth = dict(case.get("birth", {}))
    settings = case.get("settings", {})
    if "node_mode" not in birth and settings.get("node_mode"):
        birth["node_mode"] = settings["node_mode"]
    return _namespace_from_birth(
        birth,
        ayanamsa=settings.get("ayanamsa", "lahiri"),
        moon_lon=None,
        nakshatra=None,
        pada=None,
        birthdate=None,
        today=None,
        years=120,
        table=False,
    )


def _first_dasha_start(result: dict[str, Any]) -> str | None:
    timeline = result.get("timeline")
    if isinstance(timeline, list) and timeline:
        return timeline[0].get("start")
    return None


def _date_delta_days(engine_date: str | None, target_date: str | None) -> int | None:
    if not engine_date or not target_date:
        return None
    from datetime import date

    try:
        engine_parts = [int(part) for part in engine_date.split("-")[:3]]
        target_parts = [int(part) for part in target_date.split("-")[:3]]
        return (date(*engine_parts) - date(*target_parts)).days
    except Exception:
        return None


def _template_shadbala_comparison(case: dict[str, Any]) -> dict[str, Any]:
    target_components = case.get("target", {}).get("shadbala_components")
    if not isinstance(target_components, dict):
        return {"status": "missing_external_shadbala_components", "planets": {}}

    result = engine.cmd_shadbala(_namespace_from_template(case))
    if "error" in result:
        return {"status": "engine_error", "error": result["error"], "planets": {}}

    rows: dict[str, Any] = {}
    scale_ratios: list[float] = []
    for planet in SHADBALA_PLANETS:
        external_row = target_components.get(planet, {})
        engine_row = result.get("planets", {}).get(planet, {})
        engine_components = _component_totals(engine_row) if engine_row else {}
        external_total = external_row.get("total_rupa") if isinstance(external_row, dict) else None
        engine_total = round(float(engine_row.get("total_rupas", 0.0)), 4) if engine_row else None
        component_deltas: dict[str, Any] = {}
        if isinstance(external_row, dict):
            for external_name, engine_name in SHADBALA_COMPONENT_FIELD_MAP.items():
                engine_value = engine_components.get(engine_name)
                external_value = external_row.get(external_name)
                tolerance = SHADBALA_COMPONENT_TOLERANCES_RUPA[external_name]
                delta = (
                    round(float(engine_value) - float(external_value), 4)
                    if isinstance(engine_value, (int, float)) and isinstance(external_value, (int, float))
                    else None
                )
                component_deltas[external_name] = {
                    "engine_rupa": engine_value,
                    "external_rupa": external_value,
                    "delta_rupa": delta,
                    "abs_delta_rupa": round(abs(delta), 4) if delta is not None else None,
                    "tolerance_rupa": tolerance,
                    "within_tolerance": abs(delta) <= tolerance if delta is not None else None,
                }
        if isinstance(engine_total, (int, float)) and isinstance(external_total, (int, float)) and external_total:
            scale_ratios.append(round(float(engine_total) / float(external_total), 6))
        total_delta = (
            round(engine_total - float(external_total), 4)
            if engine_total is not None and isinstance(external_total, (int, float))
            else None
        )
        rows[planet] = {
            "engine_total_rupa": engine_total,
            "external_total_rupa": external_total,
            "total_rupa_delta": total_delta,
            "total_abs_delta_rupa": round(abs(total_delta), 4) if total_delta is not None else None,
            "total_tolerance_rupa": SHADBALA_TOTAL_TOLERANCE_RUPA,
            "total_within_tolerance": (
                abs(total_delta) <= SHADBALA_TOTAL_TOLERANCE_RUPA if total_delta is not None else None
            ),
            "engine_components": engine_components,
            "external_components": external_row,
            "component_deltas": component_deltas,
        }
    ratio_spread = round(max(scale_ratios) - min(scale_ratios), 6) if len(scale_ratios) >= 2 else None
    return {
        "status": "compared",
        "unit": "rupa",
        "component_tolerances": SHADBALA_COMPONENT_TOLERANCES_RUPA,
        "total_tolerance_rupa": SHADBALA_TOTAL_TOLERANCE_RUPA,
        "global_scaling_check": {
            "allowed": False,
            "recommendation": "reject_global_scaling",
            "engine_to_external_total_ratios": scale_ratios,
            "ratio_spread": ratio_spread,
            "finding": (
                "Do not fix Shadbala with a global multiplier; inspect component-level deltas by planet."
            ),
        },
        "planets": rows,
    }


def _audit_external_verified_template_case(case: dict[str, Any]) -> dict[str, Any]:
    target = case.get("target", {})
    dasha_result = engine.cmd_dasha(_namespace_from_template(case))
    engine_start = _first_dasha_start(dasha_result) if "error" not in dasha_result else None
    target_start = target.get("vimshottari_start_date")
    return {
        "case_id": case.get("id") or case.get("case_id"),
        "status": case.get("status"),
        "source": case.get("source"),
        "metadata": case.get("evidence_packet", {}).get("metadata", {}),
        "dasha": {
            "status": "compared" if engine_start and target_start else "missing_dasha_target",
            "engine_start_date": engine_start,
            "target_start_date": target_start,
            "date_delta_days": _date_delta_days(engine_start, target_start),
        },
        "shadbala": _template_shadbala_comparison(case),
        "calibration_decision": "do_not_tune_single_template",
        "finding": (
            "External-verified template rows are comparison evidence. Production constants require "
            "a multi-source sample matrix and must not be tuned to a single packet."
        ),
    }


def _status_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        status = row.get("status", "unknown")
        counts[status] = counts.get(status, 0) + 1
    return counts


def build_report(oracle: dict[str, Any]) -> dict[str, Any]:
    template_rows = [_audit_template_case(case) for case in oracle.get("template_cases", [])]
    template_comparisons = [
        _audit_external_verified_template_case(case)
        for case in oracle.get("template_cases", [])
        if case.get("status") in ORACLE_TEMPLATE_READY_STATUSES and not _missing_target_fields(case.get("target", {}))
    ]
    dasha_rows = [_audit_dasha_case(case) for case in oracle.get("dasha_cases", [])]
    longitude_rows = [_audit_longitude_case(case) for case in oracle.get("longitude_cases", [])]
    shadbala_rows = [_audit_shadbala_case(case) for case in oracle.get("shadbala_cases", [])]
    return {
        "scope": "external_oracle_boundary_audit",
        "schema_version": oracle.get("schema_version"),
        "summary": {
            "template_cases": len(template_rows),
            "template_status_counts": _status_counts(template_rows),
            "external_verified_template_cases": len(template_comparisons),
            "dasha_cases": len(dasha_rows),
            "longitude_cases": len(longitude_rows),
            "shadbala_cases": len(shadbala_rows),
            "production_tuning_recommended": False,
            "open_items": [
                "Promote template cases to external_verified only after filling external target rows.",
                "Add multi-source Vimshottari rows with Moon longitude, ayanamsa and start-boundary settings.",
                "Add Shadbala component targets before claiming external absolute calibration.",
            ],
        },
        "template_cases": template_rows,
        "template_comparisons": template_comparisons,
        "dasha_cases": dasha_rows,
        "longitude_cases": longitude_rows,
        "shadbala_cases": shadbala_rows,
        "boundary": (
            "This report is a repeatable audit gate. It should prevent accidental claims that "
            "Dasha/Shadbala are fully externally calibrated before the oracle matrix is complete."
        ),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit external Dasha/Shadbala oracle boundaries")
    parser.add_argument("--oracle-file", required=True, help="Path to oracle fixture JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    oracle = _load_oracle(args.oracle_file)
    print(json.dumps(build_report(oracle), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
