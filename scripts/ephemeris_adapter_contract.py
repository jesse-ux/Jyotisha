#!/usr/bin/env python3
"""Ephemeris adapter contract and parity baseline runner.

The current production backend is swisseph_python. This module defines the data
contract a future candidate_backend must satisfy, then emits SwissEph baseline
rows for stable parity cases.
"""

from __future__ import annotations

import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from jyotish_engine import HAS_SWE, compute_chart_data  # noqa: E402


BODY_KEYS = ["Sun", "Moon", "Ascendant", "Rahu", "Ketu"]


@dataclass(frozen=True)
class EphemerisAdapterContract:
    """Required input/output shape for any candidate_backend."""

    backend: str
    year: int
    month: int
    day: int
    hour: int
    minute: int
    lat: float
    lon: float
    tz: float
    ayanamsa_policy: str = "lahiri"
    node_policy: str = "mean"
    body_list: tuple[str, ...] = tuple(BODY_KEYS)


PARITY_CASES: list[dict[str, Any]] = [
    {
        "id": "beijing_first_use_demo",
        "label": "First-use demo chart",
        "year": 1990,
        "month": 1,
        "day": 1,
        "hour": 12,
        "minute": 0,
        "lat": 39.9042,
        "lon": 116.4074,
        "tz": 8.0,
    },
    {
        "id": "delhi_lagna_boundary",
        "label": "Delhi ascendant and node parity",
        "year": 1984,
        "month": 10,
        "day": 31,
        "hour": 6,
        "minute": 30,
        "lat": 28.6139,
        "lon": 77.2090,
        "tz": 5.5,
    },
    {
        "id": "new_york_moon_boundary",
        "label": "Western timezone Moon/nakshatra boundary guard",
        "year": 2001,
        "month": 9,
        "day": 11,
        "hour": 8,
        "minute": 46,
        "lat": 40.7128,
        "lon": -74.0060,
        "tz": -4.0,
    },
]


acceptance_thresholds = {
    "sun_moon_asc_nodes": {
        "Sun": {"longitude_delta_arcsec": 1.0},
        "Moon": {"longitude_delta_arcsec": 1.0},
        "Ascendant": {"longitude_delta_arcsec": 5.0},
        "Rahu": {"longitude_delta_arcsec": 2.0},
        "Ketu": {"longitude_delta_arcsec": 2.0},
    },
    "metadata": [
        "candidate_backend must report ayanamsa_value",
        "candidate_backend must report retrograde where body speed is available",
        "candidate_backend must include backend/version/source metadata",
    ],
}


def _round_float(value: Any, digits: int = 6) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numeric):
        return None
    return round(numeric, digits)


def _body_row(name: str, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "body": name,
        "sidereal_longitude": _round_float(data.get("degree_raw", data.get("lon", data.get("degree")))),
        "sign": data.get("sign"),
        "degree_in_sign": _round_float(data.get("degree_in_sign_raw", data.get("degree_in_sign"))),
        "speed": _round_float(data.get("speed")),
        "retrograde": bool(data.get("retrograde")) if data.get("retrograde") is not None else None,
        "nakshatra": data.get("nakshatra"),
        "nakshatra_pada": data.get("nakshatra_pada"),
    }


def run_swisseph_python(case: dict[str, Any]) -> dict[str, Any]:
    if not HAS_SWE:
        return {
            "backend": "swisseph_python",
            "available": False,
            "error": "swisseph module is not installed",
        }

    chart, _asc_idx, jd, ayanamsa = compute_chart_data(
        case["year"],
        case["month"],
        case["day"],
        case["hour"],
        case["minute"],
        case["lat"],
        case["lon"],
        case["tz"],
        "mean",
    )
    if not chart:
        return {
            "backend": "swisseph_python",
            "available": False,
            "error": "compute_chart_data returned no chart",
        }

    ascendant = chart.get("ascendant", {})
    bodies = {"Ascendant": _body_row("Ascendant", ascendant)}
    for body in ["Sun", "Moon", "Rahu", "Ketu"]:
        bodies[body] = _body_row(body, chart.get("planets", {}).get(body, {}))

    return {
        "backend": "swisseph_python",
        "available": True,
        "julian_day": _round_float(jd),
        "ayanamsa_value": _round_float(ayanamsa),
        "node_policy": "mean",
        "body_list": BODY_KEYS,
        "bodies": bodies,
    }


def run_candidate_backend(case: dict[str, Any], backend: str) -> dict[str, Any]:
    if backend == "swisseph_python":
        return run_swisseph_python(case)
    return {
        "backend": backend,
        "available": False,
        "status": "candidate_backend_not_configured",
        "reason": "Add an adapter implementation before parity comparison.",
    }


def build_parity_matrix(candidate_backend: str = "swisseph_python") -> dict[str, Any]:
    rows = []
    for case in PARITY_CASES:
        contract_input = {
            key: case[key]
            for key in ["year", "month", "day", "hour", "minute", "lat", "lon", "tz"]
        }
        contract = EphemerisAdapterContract(backend=candidate_backend, **contract_input)
        baseline = run_swisseph_python(case)
        candidate = run_candidate_backend(case, candidate_backend)
        rows.append(
            {
                "case": case["id"],
                "label": case["label"],
                "contract": asdict(contract),
                "baseline": baseline,
                "candidate_backend": candidate,
                "longitude_delta_arcsec": {
                    body: 0.0 if baseline.get("available") and candidate_backend == "swisseph_python" else None
                    for body in BODY_KEYS
                },
            }
        )
    return {
        "valid": all(row["baseline"].get("available") for row in rows),
        "contract_name": "EphemerisAdapterContract",
        "baseline_backend": "swisseph_python",
        "candidate_backend": candidate_backend,
        "sun_moon_asc_nodes": BODY_KEYS,
        "acceptance_thresholds": acceptance_thresholds,
        "PARITY_CASES": [case["id"] for case in PARITY_CASES],
        "rows": rows,
    }


def main() -> int:
    candidate = sys.argv[1] if len(sys.argv) > 1 else "swisseph_python"
    result = build_parity_matrix(candidate)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
