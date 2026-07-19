#!/usr/bin/env python3
"""Build Shadbala component closure matrix from local OSS observations."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
JYO = ROOT / "references/oracle/jyotishganit_shadbala_surface_probe_steve_jobs_2026_07_19.json"
PROVENANCE = ROOT / "references/oracle/shadbala_av_component_provenance_registry_2026_07_19.json"
XALEN = ROOT / "references/oracle/xalen_shadbala_av_component_delta_report_2026_07_19.json"
VPJ = ROOT / "references/oracle/vp_jain_shadbala_component_benchmark_2026_07_17.json"
COMPONENTS = ["Sthanabala", "Digbala", "Kaalabala", "Cheshtabala", "Naisargikabala", "Drikbala"]
PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]


def stable(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def component_value(raw: dict[str, Any], planet: str, component: str) -> float | None:
    value = raw["raw"]["shadbala"].get(planet, {}).get(component)
    if isinstance(value, dict):
        value = value.get("Total")
    return value if isinstance(value, (int, float)) else None


def load_optional(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def build() -> dict[str, Any]:
    raw = json.loads(JYO.read_text(encoding="utf-8"))
    provenance = load_optional(PROVENANCE)
    xalen = load_optional(XALEN)
    vpj = load_optional(VPJ)
    rows = []
    for planet in PLANETS:
        for component in COMPONENTS:
            val = component_value(raw, planet, component)
            rows.append(
                {
                    "planet": planet,
                    "component": component,
                    "jyotishganit_value_virupa": val,
                    "jyotishganit_status": "raw_available" if val is not None else "missing",
                    "local_status": "available_needs_same_unit_extraction",
                    "xalen_status": "delta_report_available" if xalen else "missing",
                    "vp_jain_status": "benchmark_row_classified" if vpj else "missing",
                    "source_status": "formula_source_registry_available" if provenance else "source_needed",
                    "closure_status": "component_observation_ready_unit_parity_pending",
                    "claim_boundary": "Do not assert absolute Virupa parity until local/Xalen/VP Jain/PyJHora values are normalized to the same unit and formula variant.",
                }
            )
    matrix = {
        "scope": "shadbala_component_closure_matrix",
        "created_at": "2026-07-19",
        "status": "component_matrix_ready",
        "claim_status": "partial",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "sources": {
            "jyotishganit_raw": str(JYO.relative_to(ROOT)),
            "provenance_registry": str(PROVENANCE.relative_to(ROOT)),
            "xalen_delta_report": str(XALEN.relative_to(ROOT)),
            "vp_jain_benchmark": str(VPJ.relative_to(ROOT)),
        },
        "summary": {
            "row_count": len(rows),
            "visible_planet_count": len(PLANETS),
            "component_count": len(COMPONENTS),
            "jyotishganit_raw_available_count": sum(1 for r in rows if r["jyotishganit_status"] == "raw_available"),
            "absolute_parity_ready_count": 0,
        },
        "matrix_hash": hashlib.sha256(stable(rows).encode("utf-8")).hexdigest(),
        "rows": rows,
        "boundary": "42 Shadbala six-force rows have jyotishganit raw and source/provenance hooks; absolute Virupa parity remains pending until same-unit multi-engine normalization closes.",
    }
    return matrix


def main() -> int:
    print(json.dumps(build(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
