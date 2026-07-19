#!/usr/bin/env python3
"""Normalize local/jyotishganit/Xalen/VP Jain Shadbala component rows.

All component values are represented as Virupa plus derived Rupa=Virupa/60
when numeric. The output classifies row-level deltas without declaring
absolute truth.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
JYO = ROOT / "references/oracle/jyotishganit_shadbala_surface_probe_steve_jobs_2026_07_19.json"
XALEN = ROOT / "references/oracle/xalen_shadbala_av_component_delta_report_2026_07_19.json"
VPJ = ROOT / "references/oracle/vp_jain_shadbala_component_benchmark_2026_07_17.json"
PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
COMPONENTS = {
    "sthana": "Sthanabala",
    "dig": "Digbala",
    "kala": "Kaalabala",
    "chesta": "Cheshtabala",
    "naisargika": "Naisargikabala",
    "drik": "Drikbala",
}


def stable(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def rupa(v: float | None) -> float | None:
    return None if v is None else round(v / 60.0, 6)


def get_jyo_value(jyo: dict[str, Any], planet: str, canonical: str) -> float | None:
    val = jyo["raw"]["shadbala"].get(planet, {}).get(canonical)
    if isinstance(val, dict):
        val = val.get("Total")
    return val if isinstance(val, (int, float)) else None


def xalen_index(xalen: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for group in xalen.get("component_groups", []):
        component = group.get("component")
        if component not in COMPONENTS:
            continue
        for row in group.get("rows", []):
            planet = row.get("field") or row.get("planet")
            out[(planet, component)] = row
    return out


def vpj_index(vpj: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (row.get("planet"), row.get("component")): row
        for row in vpj.get("rows", [])
    }


def classify(values: dict[str, float | None], statuses: dict[str, str | None]) -> str:
    nums = {k: v for k, v in values.items() if isinstance(v, (int, float))}
    if len(nums) < 2:
        return "insufficient_numeric_sources"
    span = max(nums.values()) - min(nums.values())
    if span <= 1.0:
        return "within_1_virupa_observation"
    if any(status == "method_variant" for status in statuses.values() if status):
        return "method_variant"
    return "formula_or_unit_mismatch"


def build() -> dict[str, Any]:
    jyo = json.loads(JYO.read_text(encoding="utf-8"))
    xalen = xalen_index(json.loads(XALEN.read_text(encoding="utf-8")))
    vpj = vpj_index(json.loads(VPJ.read_text(encoding="utf-8")))
    rows = []
    for planet in PLANETS:
        for short, canonical in COMPONENTS.items():
            jyo_v = get_jyo_value(jyo, planet, canonical)
            xrow = xalen.get((planet, short), {})
            vrow = vpj.get((planet, short), {})
            values = {
                "jyotishganit_virupa": jyo_v,
                "xalen_virupa": xrow.get("xalen_value"),
                "local_from_xalen_report_virupa": xrow.get("local_value"),
                "vp_jain_published_virupa": vrow.get("published_value"),
                "vp_jain_local_virupa": vrow.get("local_value"),
            }
            statuses = {
                "xalen_status": xrow.get("status"),
                "vp_jain_status": vrow.get("status"),
            }
            rows.append(
                {
                    "planet": planet,
                    "component": short,
                    "canonical_component": canonical,
                    **values,
                    "jyotishganit_rupa": rupa(jyo_v),
                    "xalen_rupa": rupa(xrow.get("xalen_value")),
                    "vp_jain_published_rupa": rupa(vrow.get("published_value")),
                    **statuses,
                    "normalization_unit": "Virupa",
                    "classification": classify(values, statuses),
                    "claim_boundary": "Same-unit row only; formula truth still requires source variant selection and public worked example.",
                }
            )
    summary = {
        "row_count": len(rows),
        "within_1_virupa_observation_count": sum(1 for r in rows if r["classification"] == "within_1_virupa_observation"),
        "method_variant_count": sum(1 for r in rows if r["classification"] == "method_variant"),
        "formula_or_unit_mismatch_count": sum(1 for r in rows if r["classification"] == "formula_or_unit_mismatch"),
        "insufficient_numeric_sources_count": sum(1 for r in rows if r["classification"] == "insufficient_numeric_sources"),
    }
    return {
        "scope": "shadbala_same_unit_normalizer",
        "created_at": "2026-07-19",
        "status": "same_unit_matrix_ready",
        "claim_status": "partial",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "sources": {
            "jyotishganit": str(JYO.relative_to(ROOT)),
            "xalen": str(XALEN.relative_to(ROOT)),
            "vp_jain": str(VPJ.relative_to(ROOT)),
        },
        "summary": summary,
        "matrix_hash": hashlib.sha256(stable(rows).encode("utf-8")).hexdigest(),
        "rows": rows,
        "boundary": "All 42 rows are normalized to Virupa/Rupa fields where available. Classifications are arbitration queues, not absolute parity closure.",
    }


def main() -> int:
    print(json.dumps(build(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
