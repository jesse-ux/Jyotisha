#!/usr/bin/env python3
"""Normalize Shadbala component rows to the same Virupa/Rupa unit.

This is an arbitration aid only. It aligns local-observation, jyotishganit,
Xalen, and VP Jain numeric fields into one 42-row matrix; it does not select
an absolute formula truth.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
JYOTISHGANIT = ROOT / "references/oracle/jyotishganit_shadbala_surface_probe_steve_jobs_2026_07_19.json"
XALEN = ROOT / "references/oracle/xalen_shadbala_av_component_delta_report_2026_07_19.json"
VP_JAIN = ROOT / "references/oracle/vp_jain_shadbala_component_benchmark_2026_07_17.json"

PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
COMPONENTS = {
    "sthana": "Sthanabala",
    "dig": "Digbala",
    "kala": "Kaalabala",
    "chesta": "Cheshtabala",
    "naisargika": "Naisargikabala",
    "drik": "Drikbala",
}


def stable_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def as_float(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) else None


def to_rupa(virupa: float | None) -> float | None:
    return None if virupa is None else round(virupa / 60.0, 6)


def jyotishganit_value(raw: dict[str, Any], planet: str, component: str) -> float | None:
    value = raw.get("raw", {}).get("shadbala", {}).get(planet, {}).get(component)
    if isinstance(value, dict):
        value = value.get("Total")
    return as_float(value)


def xalen_rows(raw: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    indexed: dict[tuple[str, str], dict[str, Any]] = {}
    for group in raw.get("component_groups", []):
        component = group.get("component")
        if component not in COMPONENTS:
            continue
        for row in group.get("rows", []):
            field = str(row.get("field") or row.get("planet") or "")
            planet = field.split(".", 1)[0]
            indexed[(planet, component)] = row
    return indexed


def vp_jain_rows(raw: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(row.get("planet"), row.get("component")): row for row in raw.get("rows", [])}


def classify(values: dict[str, float | None], statuses: dict[str, str | None]) -> str:
    numeric_values = [v for v in values.values() if isinstance(v, (int, float))]
    if len(numeric_values) < 2:
        return "insufficient_numeric_sources"
    if max(numeric_values) - min(numeric_values) <= 1.0:
        return "within_1_virupa_observation"
    if any(status == "method_variant" for status in statuses.values() if status):
        return "method_variant"
    return "formula_or_unit_mismatch"


def build() -> dict[str, Any]:
    jyotishganit = json.loads(JYOTISHGANIT.read_text(encoding="utf-8"))
    xalen = xalen_rows(json.loads(XALEN.read_text(encoding="utf-8")))
    vp_jain = vp_jain_rows(json.loads(VP_JAIN.read_text(encoding="utf-8")))

    rows: list[dict[str, Any]] = []
    for planet in PLANETS:
        for short_name, canonical_name in COMPONENTS.items():
            jyo_virupa = jyotishganit_value(jyotishganit, planet, canonical_name)
            xalen_row = xalen.get((planet, short_name), {})
            vp_jain_row = vp_jain.get((planet, short_name), {})

            values = {
                "jyotishganit_virupa": jyo_virupa,
                "xalen_virupa": as_float(xalen_row.get("xalen_value")),
                "local_from_xalen_report_virupa": as_float(xalen_row.get("local_value")),
                "vp_jain_published_virupa": as_float(vp_jain_row.get("published_value")),
                "vp_jain_local_virupa": as_float(vp_jain_row.get("local_value")),
            }
            statuses = {
                "xalen_status": xalen_row.get("status"),
                "vp_jain_status": vp_jain_row.get("status"),
            }

            rows.append(
                {
                    "planet": planet,
                    "component": short_name,
                    "canonical_component": canonical_name,
                    **values,
                    "jyotishganit_rupa": to_rupa(values["jyotishganit_virupa"]),
                    "xalen_rupa": to_rupa(values["xalen_virupa"]),
                    "local_from_xalen_report_rupa": to_rupa(values["local_from_xalen_report_virupa"]),
                    "vp_jain_published_rupa": to_rupa(values["vp_jain_published_virupa"]),
                    "vp_jain_local_rupa": to_rupa(values["vp_jain_local_virupa"]),
                    **statuses,
                    "normalization_unit": "Virupa",
                    "classification": classify(values, statuses),
                    "claim_boundary": (
                        "Same-unit observation row only; formula truth still requires "
                        "component source variant selection and public numeric worked examples."
                    ),
                }
            )

    summary = {
        "row_count": len(rows),
        "within_1_virupa_observation_count": sum(1 for row in rows if row["classification"] == "within_1_virupa_observation"),
        "method_variant_count": sum(1 for row in rows if row["classification"] == "method_variant"),
        "formula_or_unit_mismatch_count": sum(1 for row in rows if row["classification"] == "formula_or_unit_mismatch"),
        "insufficient_numeric_sources_count": sum(1 for row in rows if row["classification"] == "insufficient_numeric_sources"),
    }
    return {
        "scope": "shadbala_same_unit_normalizer",
        "created_at": "2026-07-19",
        "status": "same_unit_matrix_ready",
        "claim_status": "partial",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "sources": {
            "jyotishganit": str(JYOTISHGANIT.relative_to(ROOT)),
            "xalen": str(XALEN.relative_to(ROOT)),
            "vp_jain": str(VP_JAIN.relative_to(ROOT)),
        },
        "summary": summary,
        "matrix_hash": hashlib.sha256(stable_json(rows).encode("utf-8")).hexdigest(),
        "rows": rows,
        "boundary": (
            "All 42 rows are normalized to Virupa/Rupa fields where available. "
            "Classifications are arbitration queues, not absolute parity closure."
        ),
    }


def main() -> int:
    print(json.dumps(build(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
