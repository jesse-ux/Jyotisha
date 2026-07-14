#!/usr/bin/env python3
"""Auditable tropical transit and solar-return evidence calculations."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import swisseph as swe

try:
    from western_chart_engine import _ASPECTS, _PLANETS, _birth_zone, _longitude, _orb_for, _point, build_tropical_natal_chart
except ImportError:  # pragma: no cover - package import path
    from scripts.western_chart_engine import _ASPECTS, _PLANETS, _birth_zone, _longitude, _orb_for, _point, build_tropical_natal_chart


def _target_jd(target_date: str, timezone: str | float | int) -> tuple[float, datetime]:
    zone, _ = _birth_zone(timezone)
    local = datetime.fromisoformat(target_date).replace(tzinfo=zone)
    utc = local.astimezone(ZoneInfo("UTC"))
    jd = swe.julday(utc.year, utc.month, utc.day, utc.hour + utc.minute / 60 + utc.second / 3600)
    return jd, local


def _cross_aspects(transits: dict[str, dict[str, Any]], natal: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for transit_name, transit in transits.items():
        for natal_name, point in natal.items():
            separation = abs(transit["longitude"] - point["longitude"])
            separation = min(separation, 360.0 - separation)
            allowed_orb = _orb_for(transit_name, natal_name)
            for aspect, exact in _ASPECTS.items():
                orb = abs(separation - exact)
                if orb <= allowed_orb:
                    matches.append({
                        "transit_planet": transit_name,
                        "natal_point": natal_name,
                        "aspect": aspect,
                        "exact_degrees": exact,
                        "separation": round(separation, 6),
                        "orb": round(orb, 6),
                        "allowed_orb": allowed_orb,
                    })
    return sorted(matches, key=lambda row: (row["orb"], row["transit_planet"], row["natal_point"]))


def calculate_transit_to_natal(*, target_date: str, **birth: Any) -> dict[str, Any]:
    """Calculate major tropical transits to natal planets and ASC/MC on a local date."""
    natal_chart = build_tropical_natal_chart(**birth)
    jd, local = _target_jd(target_date, birth["timezone"])
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    planets: dict[str, dict[str, Any]] = {}
    for name, planet_id in _PLANETS.items():
        values, _ = swe.calc_ut(jd, planet_id, flags)
        planets[name] = _point(values[0], speed=values[3])
    natal_points = {
        **natal_chart["natal"]["planets"],
        "ascendant": natal_chart["natal"]["angles"]["ascendant"],
        "mc": natal_chart["natal"]["angles"]["mc"],
    }
    return {
        "technique": "transits",
        "status": "used",
        "target_date": target_date,
        "target_local_time": local.isoformat(),
        "zodiac": "tropical",
        "transit_planets": planets,
        "aspects": _cross_aspects(planets, natal_points),
        "orb_policy": "major aspects 0/60/90/120/180; min(per-point configured orb)",
        "boundary": "A dated transit snapshot only; no duration, outcome, or interpretation is inferred.",
    }


def _jd_to_local(jd_ut: float, timezone: str | float | int) -> datetime:
    zone, _ = _birth_zone(timezone)
    year, month, day, hour_float = swe.revjul(jd_ut, swe.GREG_CAL)
    utc = datetime(year, month, day, tzinfo=ZoneInfo("UTC")) + timedelta(hours=hour_float)
    return utc.astimezone(zone)


def calculate_solar_return(*, target_year: int, **birth: Any) -> dict[str, Any]:
    """Find the exact tropical solar return and calculate its local return chart."""
    natal_chart = build_tropical_natal_chart(**birth)
    natal_sun = natal_chart["natal"]["planets"]["sun"]["longitude"]
    start_jd = swe.julday(int(target_year), 1, 1, 0.0)
    return_jd = swe.solcross_ut(natal_sun, start_jd, swe.FLG_SWIEPH)
    return_local = _jd_to_local(return_jd, birth["timezone"])
    return_birth = {
        **birth,
        "year": return_local.year,
        "month": return_local.month,
        "day": return_local.day,
        "hour": return_local.hour,
        "minute": return_local.minute,
        "second": return_local.second,
    }
    return_chart = build_tropical_natal_chart(**return_birth)
    returned_sun = return_chart["natal"]["planets"]["sun"]["longitude"]
    delta = abs(_longitude(returned_sun - natal_sun))
    delta = min(delta, 360.0 - delta)
    return {
        "technique": "solar_return",
        "status": "used",
        "target_year": int(target_year),
        "return_julian_day_ut": round(return_jd, 8),
        "return_local_time": return_local.isoformat(),
        "natal_sun_longitude": natal_sun,
        "return_sun_longitude": returned_sun,
        "sun_longitude_delta": round(delta, 8),
        "return_chart": return_chart,
        "boundary": "Exact solar return time and chart only; annual topics require separate audited interpretation.",
    }


def build_timing_techniques(
    *,
    transit_date: str | None = None,
    solar_return_year: int | None = None,
    **birth: Any,
) -> dict[str, Any]:
    """Materialize only the requested, independently auditable timing layers."""
    techniques: dict[str, Any] = {}
    if transit_date:
        techniques["transits"] = calculate_transit_to_natal(target_date=transit_date, **birth)
    if solar_return_year is not None:
        techniques["solar_return"] = calculate_solar_return(target_year=int(solar_return_year), **birth)
    return techniques
