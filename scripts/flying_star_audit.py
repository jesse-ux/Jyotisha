#!/usr/bin/env python3
"""Inter-chart linkage, dispositor chain, and motion-point audit."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
SIGN_LORDS = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}


def _run_json(command: list[str], timeout: int = 90) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=timeout, check=False)
    if completed.returncode != 0:
        return {"status": "error", "stderr": (completed.stderr or completed.stdout).strip()[:500]}
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {"status": "invalid_json", "stdout_excerpt": completed.stdout[:500]}


def _birth_args(args: argparse.Namespace) -> list[str]:
    out: list[str] = []
    for key in ("year", "month", "day", "hour", "minute", "second", "lat", "lon", "tz"):
        out.extend([f"--{key}", str(getattr(args, key))])
    return out


def _house(sign: str, asc_sign: str) -> int:
    return (SIGNS.index(sign) - SIGNS.index(asc_sign)) % 12 + 1


def _inter_chart_linkage(chart: dict[str, Any], varga: dict[str, Any], planets: list[str]) -> dict[str, Any]:
    d1_asc = chart["ascendant"]["sign"]
    charts = {"D1": {"ascendant": d1_asc, **chart["planets"]}}
    charts.update(varga.get("divisional_charts", {}))
    result: dict[str, Any] = {}
    for planet in planets:
        rows = {}
        for chart_name, payload in charts.items():
            asc = payload.get("ascendant")
            if isinstance(asc, dict):
                asc = asc.get("sign")
            item = payload.get(planet) if isinstance(payload, dict) else None
            if not item or not asc:
                continue
            sign = item["sign"]
            rows[chart_name] = {
                "sign": sign,
                "house_in_chart": _house(sign, asc),
                "lord_of_sign": SIGN_LORDS.get(sign),
            }
        result[planet] = rows
    return result


def _dispositor_chain(chart: dict[str, Any], planet: str, max_depth: int) -> list[dict[str, Any]]:
    planets = chart["planets"]
    chain = []
    seen = set()
    current = planet
    for _ in range(max_depth):
        item = planets.get(current)
        if not item:
            break
        sign = item["sign"]
        lord = SIGN_LORDS[sign]
        chain.append({"planet": current, "sign": sign, "dispositor": lord, "dispositor_sign": planets.get(lord, {}).get("sign")})
        key = (current, lord)
        if key in seen or lord == current:
            break
        seen.add(key)
        current = lord
    return chain


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    birth = _birth_args(args)
    chart = _run_json([sys.executable, "scripts/jyotish_engine.py", "chart", *birth])
    varga = _run_json([sys.executable, "scripts/jyotish_engine.py", "varga", *birth, "--all"])
    sudarshana = _run_json([sys.executable, "scripts/jyotish_engine.py", "sudarshana", *birth, "--house", str(args.event_house)])
    tajika = _run_json([sys.executable, "scripts/jyotish_engine.py", "tajika", *birth, "--age", str(args.age), "--mode", "muntha"]) if args.age is not None else {"status": "blocked", "reason": "age_required"}
    planets = [p.strip() for p in args.planets.split(",") if p.strip()]
    return {
        "scope": "flying_star_audit",
        "event_house": args.event_house,
        "planets": planets,
        "inter_chart_linkage": _inter_chart_linkage(chart, varga, planets),
        "dispositor_chains": {planet: _dispositor_chain(chart, planet, args.max_depth) for planet in planets},
        "motion_points": {
            "bcp": {"status": "available_reference", "module": "scripts/bhrigu_pada_dasha.py", "note": "BCP/Bhrigu Pada exists; this audit records availability pending clean CLI integration."},
            "tajika_muntha": tajika,
            "sudarshana": sudarshana,
        },
        "boundaries": {
            "nadi_chain": "reference_only_not_full_machine_adjudicator",
            "ul_specific_chain": "pending_ul_output_adapter",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--month", type=int, required=True)
    parser.add_argument("--day", type=int, required=True)
    parser.add_argument("--hour", type=int, required=True)
    parser.add_argument("--minute", type=int, required=True)
    parser.add_argument("--second", type=int, default=0)
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("--tz", type=float, default=0)
    parser.add_argument("--age", type=int)
    parser.add_argument("--event-house", type=int, default=7)
    parser.add_argument("--planets", default="Venus,Saturn,Mars,Jupiter")
    parser.add_argument("--max-depth", type=int, default=12)
    args = parser.parse_args()
    print(json.dumps(build_report(args), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
