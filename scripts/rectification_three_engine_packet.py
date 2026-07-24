"""Build a privacy-safe, request-level three-engine rectification parity packet."""
from __future__ import annotations

import importlib
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from domain_calculation_service import compute_chart

try:
    from scripts.rectification_input_contract import (
        candidate_input_fingerprint,
        canonical_birth_input,
        stability_probe_contract,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from rectification_input_contract import (
        candidate_input_fingerprint,
        canonical_birth_input,
        stability_probe_contract,
    )

ROOT = Path(__file__).resolve().parents[1]
JYOTISHGANIT_ROOT = ROOT / "references" / "open_source_sources" / "jyotishganit"
JYOTISHGANIT_DATA_DIR = ROOT / ".cache" / "jyotishganit"
PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")


def canonical_case_input(case: dict[str, Any]) -> dict[str, Any]:
    """Normalize only calculation-bearing fields before hashing or engine dispatch."""
    return canonical_birth_input(case)


def case_hash(case: dict[str, Any]) -> str:
    """Stable identity for evidence correlation; never exposes birth data."""
    return candidate_input_fingerprint(case)


def _local_d1(case: dict[str, Any]) -> dict[str, str]:
    chart = compute_chart(canonical_case_input(case))
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


def _ensure_jyotishganit_data_dir() -> str:
    return os.environ.setdefault("JYOTISHGANIT_DATA_DIR", str(JYOTISHGANIT_DATA_DIR))


def _jyotishganit_d1(case: dict[str, Any]) -> dict[str, str]:
    _ensure_jyotishganit_data_dir()
    sys.path.insert(0, str(JYOTISHGANIT_ROOT))
    try:
        from jyotishganit import calculate_birth_chart, get_birth_chart_json
        chart = calculate_birth_chart(datetime(case["year"], case["month"], case["day"], case["hour"], case["minute"], case.get("second", 0)), case["lat"], case["lon"], case["tz"], location_name="request-level", name="request-level")
        raw = get_birth_chart_json(chart)
        return {str(item["celestialBody"]): str(item["sign"]) for house in raw["d1Chart"]["houses"] for item in house.get("occupants", []) if item.get("celestialBody") in PLANETS}
    finally:
        if str(JYOTISHGANIT_ROOT) in sys.path:
            sys.path.remove(str(JYOTISHGANIT_ROOT))


def _gateway_job_receipt(job: dict[str, Any]) -> dict[str, Any]:
    """Return only pollable, non-sensitive VedAstro job state for a packet."""
    archive = job.get("raw_response_archive")
    archive = archive if isinstance(archive, dict) else {}
    return {
        "scope": "vedastro_gateway_job_receipt",
        "status": str(job.get("status") or "blocked"),
        "job_id": str(job.get("job_id") or ""),
        "poll_path": str(job.get("poll_path") or ""),
        "raw_response_archive": {
            "status": str(archive.get("status") or "unknown"),
            "official_raw_response_available": bool(archive.get("official_raw_response_available")),
        },
        "boundary": "VedAstro raw response remains server-side; this receipt never returns request data or raw evidence.",
    }


def _enqueue_vedastro_gateway_job(
    case: dict[str, Any], *, question: str = "", reference_date: str = ""
) -> dict[str, Any]:
    from scripts.vedastro_gateway import enqueue_gateway_job

    job = enqueue_gateway_job(
        case,
        question=question,
        themes=["rectification"],
        reference_date=reference_date,
    )
    return _gateway_job_receipt(job)


def build_packet(
    case: dict[str, Any],
    *,
    enqueue_vedastro_gateway: bool = False,
    vedastro_question: str = "",
    vedastro_reference_date: str = "",
) -> dict[str, Any]:
    """Compare local/PyJHora/jyotishganit D1 without persisting private input."""
    case = canonical_case_input(case)
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
    vedastro = {"status": "requires_gateway_raw_archive"}
    if enqueue_vedastro_gateway:
        try:
            vedastro = _enqueue_vedastro_gateway_job(
                case,
                question=vedastro_question,
                reference_date=vedastro_reference_date,
            )
        except Exception as exc:
            vedastro = {
                "scope": "vedastro_gateway_job_receipt",
                "status": "blocked",
                "reason": f"gateway_enqueue_failed:{exc.__class__.__name__}",
                "boundary": "VedAstro raw response remains server-side; no raw evidence was returned.",
            }
    return {
        "scope": "request_level_three_engine_d1_parity",
        "case_hash": case_hash(case),
        "input_contract_hash": candidate_input_fingerprint(case),
        "stability_contract": stability_probe_contract(case),
        "engine_status": engine_status,
        "match_count": sum(row["status"] == "match" for row in rows),
        "mismatch_count": sum(row["status"] == "mismatch" for row in rows),
        "rows": rows,
        "vedastro": vedastro,
        "can_confirm": False,
        "boundary": "D1 parity alone never confirms a rectified minute; VedAstro raw and domain-level parity remain required.",
    }
