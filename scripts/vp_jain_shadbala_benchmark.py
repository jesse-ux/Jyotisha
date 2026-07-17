#!/usr/bin/env python3
"""Compare the native Shadbala chain with VP Jain's published worked example."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
EXPECTED = {
    "sthana": (172.04, 77.17, 184.94, 238.16, 152.98, 198.08, 206.31),
    "dig": (6.59, 12.22, 20.99, 31.97, 31.99, 53.29, 26.67),
    "kala": (81.80, 205.85, 158.08, 210.68, 144.22, 135.89, 139.56),
    "chesta": (0.0, 0.0, 20.93, 28.76, 8.43, 28.18, 5.05),
    "naisargika": (60.0, 51.43, 17.14, 25.71, 34.29, 42.86, 8.57),
    "drik": (11.24, -0.32, -5.10, 4.29, 4.32, -2.86, 5.82),
}
LOCAL_KEYS = {
    "sthana": ("sthana_bala", "total"),
    "dig": ("dig_bala",),
    "kala": ("kala_bala", "total"),
    "chesta": ("chesta_bala",),
    "naisargika": ("naisargika_bala",),
    "drik": ("drik_bala",),
}


def _native_output() -> dict:
    command = [
        sys.executable, str(ROOT / "scripts" / "jyotish_engine.py"), "shadbala",
        "--year", "1981", "--month", "9", "--day", "13",
        "--hour", "1", "--minute", "30", "--lat", "28.65",
        "--lon", "77.2166666667", "--tz", "5.5", "--ayanamsa", "lahiri",
    ]
    return json.loads(subprocess.check_output(command, cwd=ROOT, text=True))


def _value(row: dict, path: tuple[str, ...]) -> float:
    value = row
    for key in path:
        value = value[key]
    return float(value)


def _variant(component: str, planet: str) -> str:
    if component == "sthana":
        return "moolatrikona_degree_range_vs_whole_sign"
    if planet in {"Sun", "Moon"}:
        return "luminary_chesta_policy"
    return "mean_motion_seeghrochcha_variant"


def build_report() -> dict:
    actual = _native_output()["planets"]
    rows = []
    for component, expected_values in EXPECTED.items():
        for planet, expected in zip(PLANETS, expected_values):
            local = _value(actual[planet], LOCAL_KEYS[component])
            delta = round(local - expected, 4)
            matched = abs(delta) <= 1.0
            rows.append({
                "component": component,
                "planet": planet,
                "unit": "Virupa",
                "published_value": expected,
                "local_value": local,
                "delta": delta,
                "tolerance": 1.0,
                "status": "within_tolerance" if matched else "method_variant",
                "variant": None if matched else _variant(component, planet),
            })
    matched = sum(row["status"] == "within_tolerance" for row in rows)
    return {
        "case": {
            "name": "VP Jain published Shadbala example",
            "birth": "1981-09-13T01:30:00+05:30",
            "latitude": 28.65,
            "longitude": 77.2166666667,
            "ayanamsa": "Lahiri",
        },
        "source": {
            "upstream": "PyJHora V4.8.7 pvr_tests.py::shadbala_VPJainBook_tests",
            "upstream_commit": "ca22995709bd60e371e7820a1a5efc80ce4cf821",
            "upstream_url": "https://github.com/naturalstupid/PyJHora/blob/ca22995709bd60e371e7820a1a5efc80ce4cf821/src/jhora/tests/pvr_tests.py#L6853",
            "upstream_issue": None,
            "license_boundary": "AGPL-3.0 process-isolated numeric expectations only; no implementation copied.",
            "truth_status": "candidate_published_example_replay_not_independent_arbitration",
        },
        "summary": {
            "row_count": len(rows),
            "classified_count": len(rows),
            "within_tolerance_count": matched,
            "method_variant_count": len(rows) - matched,
            "absolute_parity": False,
        },
        "rows": rows,
    }


if __name__ == "__main__":
    output = ROOT / "references" / "oracle" / "vp_jain_shadbala_component_benchmark_2026_07_17.json"
    output.write_text(json.dumps(build_report(), ensure_ascii=False, indent=2) + "\n")
    print(output)
