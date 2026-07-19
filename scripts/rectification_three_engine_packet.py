"""Build a privacy-safe, request-level three-engine rectification parity packet."""
from __future__ import annotations

import hashlib
import importlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from domain_calculation_service import compute_chart

ROOT = Path(__file__).resolve().parents[1]
JYOTISHGANIT_ROOT = ROOT / "references" / "open_source_sources" / "jyotishganit"
PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")


def case_hash(case: dict[str, Any]) -> str:
    """Stable identity for evidence correlation; never exposes birth data."""
    payload = json.dumps(case, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _local_d1(case: dict[str, Any]) -> dict[str, str]:
    chart = compute_chart({**case, "ayanamsa": case.get("ayanamsa", "lahiri"), "node_mode": case.get("node_mode", "true")})
    return {planet: str(chart["planets"][planet]["sign"]) for planet in PLANETS}


def _pyjhora_d1(case: dict[str, Any]) -> dict[str, str]:
    utils = importlib.import_module("jhora.utils")
    charts = importlib.import_module("jhora.horoscope.chart.charts")
    drik = importlib.import_module("jhora.panchanga.drik")
    jd = utils.julian_day_number((case["year"], case["month"], case["day"]), (case["hour"], case["minute"], case.get("second", 0)))
    drik.set_ayanamsa_mode("LAHIRI", jd=jd)
    place = drik.Place("request-level", case["lat"], case["lon"], case["tz"])
    index_to_planet = {0: "Sun", 1: "Moon", 2: "Mars", 3: "Mercury", 4: "Jupiter", 5: "Venus", 6: "Saturn"}
    return {index_to_planet[body]: SIGNS[int(position[0])] for body, position in charts.rasi_chart(jd, place) if body in index_to_planet}


def _jyotishganit_d1(case: dict[str, Any]) -> dict[str, str]:
    sys.path.insert(0, str(JYOTISHGANIT_ROOT))
    try:
        from jyotishganit import calculate_birth_chart, get_birth_chart_json
        chart = calculate_birth_chart(datetime(case["year"], case["month"], case["day"], case["hour"], case["minute"], case.get("second", 0)), case["lat"], case["lon"], case["tz"], location_name="request-level", name="request-level")
        raw = get_birth_chart_json(chart)
        return {str(item["celestialBody"]): str(item["sign"]) for house in raw["d1Chart"]["houses"] for item in house.get("occupants", []) if item.get("celestialBody") in PLANETS}
    finally:
        if str(JYOTISHGANIT_ROOT) in sys.path:
            sys.path.remove(str(JYOTISHGANIT_ROOT))


def build_packet(case: dict[str, Any]) -> dict[str, Any]:
    """Compare local/PyJHora/jyotishganit D1 without persisting private input."""
    required = {"year", "month", "day", "hour", "minute", "lat", "lon", "tz"}
    if not required <= set(case):
        raise ValueError("case is missing required birth fields")
    outputs: dict[str, dict[str, str]] = {"local": _local_d1(case)}
    engine_status: dict[str, str] = {"local": "ok"}
    for name, runner in (("pyjhora", _pyjhora_d1), ("jyotishganit", _jyotishganit_d1)):
        try:
            outputs[name] = runner(case)
            engine_status[name] = "ok"
        except Exception as exc:
            outputs[name] = {}
            engine_status[name] = f"blocked:{exc.__class__.__name__}"
    rows = [{"planet": planet, "values": {name: data.get(planet) for name, data in outputs.items()}, "status": "match" if len({data.get(planet) for data in outputs.values()}) == 1 else "mismatch"} for planet in PLANETS]
    return {
        "scope": "request_level_three_engine_d1_parity",
        "case_hash": case_hash(case),
        "engine_status": engine_status,
        "match_count": sum(row["status"] == "match" for row in rows),
        "mismatch_count": sum(row["status"] == "mismatch" for row in rows),
        "rows": rows,
        "vedastro": {"status": "requires_gateway_raw_archive"},
        "can_confirm": False,
        "boundary": "D1 parity alone never confirms a rectified minute; VedAstro raw and domain-level parity remain required.",
    }
