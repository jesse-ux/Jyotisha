#!/usr/bin/env python3
"""Canonical calculation service shared by CLI, REST, and MCP adapters."""

from __future__ import annotations

import hashlib
import json
import math
import threading
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import swisseph as swe
from ayanamsa_utils import apply_ayanamsa, normalize_ayanamsa_name
from dasha_analyzer import build_dasha_timeline, lon_to_nakshatra
from jyotish_engine import SIGNS, compute_chart_data
from sade_sati import calc_sade_sati_complete

CONTRACT_VERSION = "1.0.0"
_SWISSEPH_LOCK = threading.RLock()
_PLANET_IDS = {"Saturn": swe.SATURN}


class CalculationError(ValueError):
    pass


class TimezoneInferenceError(CalculationError):
    pass


def _canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _lookup_timezone_name(lat: float, lon: float) -> str | None:
    try:
        from timezonefinder import TimezoneFinder
    except ImportError as exc:
        raise TimezoneInferenceError("timezone inference dependency unavailable") from exc
    return TimezoneFinder().timezone_at(lng=lon, lat=lat)


def infer_timezone_offset(*, lat: float, lon: float, local_datetime: datetime) -> float:
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise TimezoneInferenceError("timezone inference received invalid coordinates")
    tz_name = _lookup_timezone_name(lat, lon)
    if not tz_name:
        raise TimezoneInferenceError("timezone inference returned no IANA zone")
    try:
        offset = local_datetime.replace(tzinfo=ZoneInfo(tz_name)).utcoffset()
    except Exception as exc:
        raise TimezoneInferenceError("timezone inference failed for IANA zone") from exc
    if offset is None:
        raise TimezoneInferenceError("timezone inference returned no UTC offset")
    return offset.total_seconds() / 3600.0


def _normalized_request(payload: dict[str, Any]) -> dict[str, Any]:
    requested_node = str(payload.get("node_mode", payload.get("nodeMode", "mean"))).lower()
    if requested_node not in {"mean", "true"}:
        raise CalculationError("node_mode must be mean or true")
    ayanamsa = normalize_ayanamsa_name(payload.get("ayanamsa", "lahiri"))
    local_dt = datetime(
        int(payload["year"]),
        int(payload["month"]),
        int(payload["day"]),
        int(float(payload.get("hour", 0))),
        int(float(payload.get("minute", 0))),
        int(float(payload.get("second", 0))),
    )
    lat = float(payload["lat"])
    lon = float(payload["lon"])
    tz_requested = payload.get("tz")
    timezone_source = "explicit_offset"
    if tz_requested in {None, ""}:
        tz = infer_timezone_offset(lat=lat, lon=lon, local_datetime=local_dt)
        timezone_source = "iana_inferred"
    else:
        tz = float(tz_requested)
    if not math.isfinite(tz) or not -14 <= tz <= 14:
        raise CalculationError("tz must be a finite offset between -14 and 14")
    return {
        "year": local_dt.year,
        "month": local_dt.month,
        "day": local_dt.day,
        "hour": int(float(payload.get("hour", 0))),
        "minute": int(float(payload.get("minute", 0))),
        "second": int(float(payload.get("second", 0))),
        "lat": lat,
        "lon": lon,
        "tz": tz,
        "timezone_source": timezone_source,
        "ayanamsa": ayanamsa,
        "node_mode": requested_node,
    }


def _contract(requested: dict[str, Any], effective: dict[str, Any], *, algorithm: str) -> dict[str, Any]:
    return {
        "contract_version": CONTRACT_VERSION,
        "algorithm": algorithm,
        "requested": requested,
        "effective": effective,
    }


def compute_chart(payload: dict[str, Any]) -> dict[str, Any]:
    request = _normalized_request(payload)
    with _SWISSEPH_LOCK:
        chart, _asc_idx, _jd, _ayanamsa = compute_chart_data(
            request["year"],
            request["month"],
            request["day"],
            request["hour"],
            request["minute"],
            request["lat"],
            request["lon"],
            request["tz"],
            node_mode=request["node_mode"],
            second=request["second"],
            ayanamsa_name=request["ayanamsa"],
        )
    if not isinstance(chart, dict):
        raise CalculationError("canonical chart calculation failed")

    for planet in chart.get("planets", {}).values():
        if not isinstance(planet, dict) or "error" in planet:
            continue
        planet.setdefault("lon", planet.get("degree_raw", planet.get("degree")))
        if planet.get("sign") in SIGNS:
            planet.setdefault("sign_idx", SIGNS.index(planet["sign"]))

    birth = chart.get("birth_info", {})
    effective = {
        "ayanamsa": birth.get("ayanamsa_name", request["ayanamsa"]),
        "node_mode": birth.get("node_mode", request["node_mode"]),
        "timezone_offset": request["tz"],
        "timezone_source": request["timezone_source"],
        "ephemeris_source": "swisseph_calc_ut",
        "ephemeris_flags_verified": False,
    }
    requested = {
        "ayanamsa": payload.get("ayanamsa", "lahiri"),
        "node_mode": payload.get("node_mode", payload.get("nodeMode", "mean")),
        "timezone_offset": payload.get("tz"),
    }
    contract = _contract(requested, effective, algorithm="sidereal_natal_chart")
    hash_payload = {
        "contract": contract,
        "birth": birth,
        "ascendant": chart.get("ascendant"),
        "planets": chart.get("planets"),
    }
    chart["calculation_contract"] = contract
    chart["result_hash"] = _canonical_hash(hash_payload)
    return chart


def compute_vimshottari_timeline(
    *, birth_dt: datetime, moon_lon: float, current_date: datetime | None = None
) -> dict[str, Any]:
    nak_info, progress, pada = lon_to_nakshatra(float(moon_lon) % 360)
    timeline, elapsed, remaining, start_lord = build_dasha_timeline(
        birth_dt.strftime("%Y-%m-%d"), nak_info, progress
    )
    periods = [
        {
            "lord": period["lord"],
            "years": period["years"],
            "start": period["start"].strftime("%Y-%m-%d"),
            "end": period["end"].strftime("%Y-%m-%d"),
        }
        for period in timeline
    ]
    contract = _contract(
        {"moon_longitude": float(moon_lon) % 360},
        {"year_basis_days": 365.25, "nakshatra": nak_info[0], "pada": pada},
        algorithm="vimshottari_birth_balance",
    )
    result = {
        "periods": periods,
        "birth_balance": {
            "lord": start_lord,
            "elapsed_years": elapsed,
            "remaining_years": remaining,
        },
        "calculation_contract": contract,
    }
    result["result_hash"] = _canonical_hash(result)
    return result
def compute_transit_longitude(
    *, planet: str, reference_date: str, tz: float, ayanamsa: str = "lahiri"
) -> dict[str, Any]:
    if planet not in _PLANET_IDS:
        raise CalculationError(f"unsupported transit planet: {planet}")
    try:
        local_dt = datetime.strptime(reference_date[:10], "%Y-%m-%d").replace(hour=12)
    except (TypeError, ValueError) as exc:
        raise CalculationError("reference_date must be YYYY-MM-DD") from exc
    ayanamsa_name = normalize_ayanamsa_name(ayanamsa)
    with _SWISSEPH_LOCK:
        apply_ayanamsa(ayanamsa_name, swe)
        jd = swe.julday(
            local_dt.year,
            local_dt.month,
            local_dt.day,
            12.0 - float(tz),
        )
        ayanamsa_value = swe.get_ayanamsa(jd)
        position, flags = swe.calc_ut(jd, _PLANET_IDS[planet])
    longitude = (position[0] - ayanamsa_value) % 360
    return {
        "planet": planet,
        "longitude": longitude,
        "reference_date": reference_date[:10],
        "ayanamsa": ayanamsa_name,
        "timezone_offset": float(tz),
        "swisseph_return_flags": int(flags),
        "data_layer": "true_transit_positions",
    }


def compute_sade_sati(
    *,
    moon_degree: float,
    asc_degree: float,
    reference_date: str,
    tz: float,
    ayanamsa: str = "lahiri",
) -> dict[str, Any]:
    transit = compute_transit_longitude(
        planet="Saturn",
        reference_date=reference_date,
        tz=tz,
        ayanamsa=ayanamsa,
    )
    result = calc_sade_sati_complete(
        float(moon_degree) % 360,
        float(asc_degree) % 360,
        transit["longitude"],
        datetime.strptime(reference_date[:10], "%Y-%m-%d"),
    )
    result["transit_saturn_lon"] = transit["longitude"]
    result["provenance"] = transit
    result["calculation_contract"] = _contract(
        {"reference_date": reference_date[:10], "ayanamsa": ayanamsa, "tz": tz},
        transit,
        algorithm="sade_sati_true_saturn_transit",
    )
    result["result_hash"] = _canonical_hash(result)
    return result
