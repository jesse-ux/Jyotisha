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


def _birth_jd(**birth: Any) -> float:
    zone, _ = _birth_zone(birth["timezone"])
    local = datetime(
        int(birth["year"]), int(birth["month"]), int(birth["day"]),
        int(birth["hour"]), int(birth["minute"]), int(birth.get("second", 0)), tzinfo=zone,
    )
    utc = local.astimezone(ZoneInfo("UTC"))
    return swe.julday(utc.year, utc.month, utc.day, utc.hour + utc.minute / 60 + utc.second / 3600)


def _progressed_planets(progressed_jd: float) -> dict[str, dict[str, Any]]:
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    planets: dict[str, dict[str, Any]] = {}
    for name, planet_id in _PLANETS.items():
        values, _ = swe.calc_ut(progressed_jd, planet_id, flags)
        planets[name] = _point(values[0], speed=values[3])
    return planets


def _quotidian_progressed_angles(progressed_jd: float, birth: dict[str, Any]) -> dict[str, Any]:
    local = _jd_to_local(progressed_jd, birth["timezone"])
    progressed_birth = {
        **birth,
        "year": local.year,
        "month": local.month,
        "day": local.day,
        "hour": local.hour,
        "minute": local.minute,
        "second": local.second,
    }
    chart = build_tropical_natal_chart(**progressed_birth)
    return {
        "status": "used",
        "method": "secondary_quotidian_progressed_date_same_location",
        "progressed_local_time": local.isoformat(),
        "angles": chart["natal"]["angles"],
        "boundary": "Quotidian progressed-date angles; Naibod and solar-arc angle variants are separate methods.",
    }


def calculate_secondary_progressions(*, target_date: str, **birth: Any) -> dict[str, Any]:
    """Calculate progressed planets using one ephemeris day per tropical year."""
    natal_chart = build_tropical_natal_chart(**birth)
    target_jd, local = _target_jd(target_date, birth["timezone"])
    birth_jd = _birth_jd(**birth)
    elapsed_years = (target_jd - birth_jd) / 365.242189
    progressed_jd = birth_jd + elapsed_years
    planets = _progressed_planets(progressed_jd)
    progressed_angles = _quotidian_progressed_angles(progressed_jd, birth)
    natal_points = {
        **natal_chart["natal"]["planets"],
        "ascendant": natal_chart["natal"]["angles"]["ascendant"],
        "mc": natal_chart["natal"]["angles"]["mc"],
    }
    return {
        "technique": "secondary_progressions",
        "status": "partial",
        "method": "one_ephemeris_day_per_tropical_year",
        "target_date": target_date,
        "target_local_time": local.isoformat(),
        "elapsed_tropical_years": round(elapsed_years, 8),
        "progressed_julian_day_ut": round(progressed_jd, 8),
        "natal_sun_longitude": natal_chart["natal"]["planets"]["sun"]["longitude"],
        "progressed_planets": planets,
        "progressed_angles": progressed_angles,
        "aspects": _cross_aspects(planets, natal_points),
        "boundary": "Progressed planets plus explicitly selected quotidian angles. Lunar phases, stations, duration, and interpretation remain separate audited layers.",
    }


def calculate_solar_arc_directions(*, target_date: str, **birth: Any) -> dict[str, Any]:
    """Direct natal points by the true arc of the secondary progressed Sun."""
    natal_chart = build_tropical_natal_chart(**birth)
    progressions = calculate_secondary_progressions(target_date=target_date, **birth)
    natal_sun = natal_chart["natal"]["planets"]["sun"]["longitude"]
    progressed_sun = progressions["progressed_planets"]["sun"]["longitude"]
    arc = _longitude(progressed_sun - natal_sun)
    natal_points = {
        **natal_chart["natal"]["planets"],
        "ascendant": natal_chart["natal"]["angles"]["ascendant"],
        "mc": natal_chart["natal"]["angles"]["mc"],
    }
    directed = {name: _point(point["longitude"] + arc) for name, point in natal_points.items()}
    return {
        "technique": "solar_arc_directions",
        "status": "partial",
        "method": "secondary_progressed_sun_arc",
        "target_date": target_date,
        "natal_sun_longitude": natal_sun,
        "progressed_sun_longitude": progressed_sun,
        "solar_arc_degrees": round(arc, 8),
        "directed_points": directed,
        "aspects": _cross_aspects(directed, natal_points),
        "boundary": "True secondary-progressed-Sun arc applied to natal planets/ASC/MC. Directional converse, latitude, parans, midpoint, duration, and event interpretation are not inferred.",
    }


def calculate_converse_secondary_progressions(*, target_date: str, **birth: Any) -> dict[str, Any]:
    """Calculate converse progressed planets using one ephemeris day per tropical year backward."""
    natal_chart = build_tropical_natal_chart(**birth)
    target_jd, local = _target_jd(target_date, birth["timezone"])
    birth_jd = _birth_jd(**birth)
    elapsed_years = (target_jd - birth_jd) / 365.242189
    progressed_jd = birth_jd - elapsed_years
    planets = _progressed_planets(progressed_jd)
    natal_points = {
        **natal_chart["natal"]["planets"],
        "ascendant": natal_chart["natal"]["angles"]["ascendant"],
        "mc": natal_chart["natal"]["angles"]["mc"],
    }
    return {
        "technique": "converse_secondary_progressions",
        "status": "partial",
        "method": "one_ephemeris_day_per_tropical_year_backward",
        "target_date": target_date,
        "target_local_time": local.isoformat(),
        "elapsed_tropical_years": round(elapsed_years, 8),
        "progressed_julian_day_ut": round(progressed_jd, 8),
        "progressed_planets": planets,
        "aspects": _cross_aspects(planets, natal_points),
        "progressed_angles": {
            "status": "blocked",
            "reason": "Progressed angle method is not selected; quotidian/solar-arc/Naibod variants are not interchangeable.",
        },
        "boundary": "Converse progressed planets only; progressed angles and interpretation remain blocked until a method is selected.",
    }


def calculate_converse_solar_arc_directions(*, target_date: str, **birth: Any) -> dict[str, Any]:
    """Direct natal points backward by the converse secondary-progressed Sun arc."""
    natal_chart = build_tropical_natal_chart(**birth)
    progressions = calculate_converse_secondary_progressions(target_date=target_date, **birth)
    natal_sun = natal_chart["natal"]["planets"]["sun"]["longitude"]
    progressed_sun = progressions["progressed_planets"]["sun"]["longitude"]
    arc = _longitude(natal_sun - progressed_sun)
    natal_points = {
        **natal_chart["natal"]["planets"],
        "ascendant": natal_chart["natal"]["angles"]["ascendant"],
        "mc": natal_chart["natal"]["angles"]["mc"],
    }
    directed = {name: _point(point["longitude"] - arc) for name, point in natal_points.items()}
    return {
        "technique": "converse_solar_arc_directions",
        "status": "partial",
        "method": "converse_secondary_progressed_sun_arc",
        "target_date": target_date,
        "natal_sun_longitude": natal_sun,
        "converse_progressed_sun_longitude": progressed_sun,
        "converse_solar_arc_degrees": round(arc, 8),
        "directed_points": directed,
        "aspects": _cross_aspects(directed, natal_points),
        "boundary": "Backward solar arc applied to natal planets/ASC/MC. Interpretation and parans remain separate audited layers.",
    }


def _midpoint_longitude(first: float, second: float) -> float:
    diff = _longitude(second - first)
    if diff > 180.0:
        diff -= 360.0
    return _longitude(first + diff / 2.0)


def calculate_midpoints(*, target_date: str | None = None, orb: float = 1.5, **birth: Any) -> dict[str, Any]:
    """Calculate natal midpoint tree and optional transit conjunction/opposition hits."""
    natal_chart = build_tropical_natal_chart(**birth)
    natal_points = {
        **natal_chart["natal"]["planets"],
        "ascendant": natal_chart["natal"]["angles"]["ascendant"],
        "mc": natal_chart["natal"]["angles"]["mc"],
    }
    names = [name for name in [*_PLANETS.keys(), "ascendant", "mc"] if name in natal_points]
    midpoints: dict[str, dict[str, Any]] = {}
    for index, first_name in enumerate(names):
        for second_name in names[index + 1:]:
            key = f"{first_name}/{second_name}"
            lon = _midpoint_longitude(natal_points[first_name]["longitude"], natal_points[second_name]["longitude"])
            midpoints[key] = _point(lon)
    result: dict[str, Any] = {
        "technique": "midpoints",
        "status": "used",
        "method": "shortest_arc_direct_midpoints",
        "orb_degrees": float(orb),
        "natal_midpoints": midpoints,
        "boundary": "Midpoint geometry only; hits are conjunction/opposition contacts, not interpretations.",
    }
    if target_date:
        transit = calculate_transit_to_natal(target_date=target_date, **birth)
        hits: list[dict[str, Any]] = []
        for transit_name, transit_point in transit["transit_planets"].items():
            for midpoint_name, midpoint in midpoints.items():
                separation = abs(transit_point["longitude"] - midpoint["longitude"])
                separation = min(separation, 360.0 - separation)
                for aspect, exact in {"conjunction": 0.0, "opposition": 180.0}.items():
                    hit_orb = abs(separation - exact)
                    if hit_orb <= orb:
                        hits.append({
                            "transit_planet": transit_name,
                            "midpoint": midpoint_name,
                            "aspect": aspect,
                            "orb": round(hit_orb, 6),
                            "separation": round(separation, 6),
                        })
        result["target_date"] = target_date
        result["transit_midpoint_hits"] = sorted(hits, key=lambda row: (row["orb"], row["transit_planet"], row["midpoint"]))
    return result


def calculate_lunar_return(*, start_date: str, **birth: Any) -> dict[str, Any]:
    """Find the next exact tropical lunar return after a local start date."""
    natal_chart = build_tropical_natal_chart(**birth)
    natal_moon = natal_chart["natal"]["planets"]["moon"]["longitude"]
    start_jd, _ = _target_jd(start_date, birth["timezone"])
    return_jd = swe.mooncross_ut(natal_moon, start_jd, swe.FLG_SWIEPH)
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
    returned_moon = return_chart["natal"]["planets"]["moon"]["longitude"]
    delta = abs(_longitude(returned_moon - natal_moon))
    delta = min(delta, 360.0 - delta)
    return {
        "technique": "lunar_return",
        "status": "used",
        "method": "Swiss Ephemeris mooncross_ut tropical longitude",
        "start_date": start_date,
        "return_julian_day_ut": round(return_jd, 8),
        "return_local_time": return_local.isoformat(),
        "natal_moon_longitude": natal_moon,
        "return_moon_longitude": returned_moon,
        "moon_longitude_delta": round(delta, 8),
        "return_chart": return_chart,
        "boundary": "Exact lunar return time and chart only; monthly topics require separate audited interpretation.",
    }


def calculate_transit_duration_scan(*, start_date: str, end_date: str, max_days: int = 370, **birth: Any) -> dict[str, Any]:
    """Scan daily transit-to-natal aspect activity and group consecutive windows."""
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    if end < start:
        raise ValueError("end_date must be on or after start_date")
    days = (end.date() - start.date()).days + 1
    if days > max_days:
        raise ValueError(f"duration scan range exceeds max_days={max_days}")
    daily_hits: list[dict[str, Any]] = []
    active: dict[tuple[str, str, str], dict[str, Any]] = {}
    windows: list[dict[str, Any]] = []
    for offset in range(days):
        current = (start + timedelta(days=offset)).date().isoformat()
        transit = calculate_transit_to_natal(target_date=current, **birth)
        keys = set()
        for aspect in transit["aspects"]:
            key = (aspect["transit_planet"], aspect["natal_point"], aspect["aspect"])
            keys.add(key)
            if key not in active:
                active[key] = {"start_date": current, "min_orb": aspect["orb"]}
            else:
                active[key]["min_orb"] = min(active[key]["min_orb"], aspect["orb"])
        for key in list(active):
            if key not in keys:
                row = active.pop(key)
                windows.append({
                    "transit_planet": key[0],
                    "natal_point": key[1],
                    "aspect": key[2],
                    "start_date": row["start_date"],
                    "end_date": (start + timedelta(days=offset - 1)).date().isoformat(),
                    "min_orb": round(row["min_orb"], 6),
                })
        daily_hits.append({"date": current, "hit_count": len(transit["aspects"]), "aspects": transit["aspects"]})
    final_date = end.date().isoformat()
    for key, row in active.items():
        windows.append({
            "transit_planet": key[0],
            "natal_point": key[1],
            "aspect": key[2],
            "start_date": row["start_date"],
            "end_date": final_date,
            "min_orb": round(row["min_orb"], 6),
        })
    return {
        "technique": "transit_duration_scan",
        "status": "used",
        "method": "daily local-midnight transit snapshots grouped into consecutive aspect windows",
        "start_date": start_date,
        "end_date": end_date,
        "days_scanned": days,
        "daily_hits": daily_hits,
        "windows": sorted(windows, key=lambda row: (row["start_date"], row["min_orb"], row["transit_planet"])),
        "boundary": "Daily scan only; exact ingress/egress times require sub-daily root finding.",
    }


def calculate_parans_status(*, target_date: str | None = None, **birth: Any) -> dict[str, Any]:
    if not target_date:
        return {"technique": "parans", "status": "blocked", "reason": "target_date_required"}
    start_jd, target_local = _target_jd(target_date, birth["timezone"])
    geopos = (float(birth["longitude"]), float(birth["latitude"]), 0.0)
    modes = {
        "rise": swe.CALC_RISE,
        "upper_culmination": swe.CALC_MTRANSIT,
        "set": swe.CALC_SET,
    }
    events: list[dict[str, Any]] = []
    for planet, planet_id in _PLANETS.items():
        for angle, mode in modes.items():
            try:
                status, values = swe.rise_trans(start_jd, planet_id, mode, geopos, 0.0, 15.0, swe.FLG_SWIEPH)
            except (swe.Error, TypeError, ValueError):
                continue
            if status != 0:
                continue
            event_local = _jd_to_local(float(values[0]), birth["timezone"])
            if event_local.date() != target_local.date():
                continue
            events.append({
                "planet": planet,
                "angle": angle,
                "julian_day_ut": round(float(values[0]), 8),
                "local_time": event_local.isoformat(),
            })
    events.sort(key=lambda row: (row["julian_day_ut"], row["planet"], row["angle"]))
    pairs: list[dict[str, Any]] = []
    for index, first in enumerate(events):
        for second in events[index + 1:]:
            delta_minutes = (second["julian_day_ut"] - first["julian_day_ut"]) * 1440.0
            if delta_minutes > 4.0:
                break
            if first["planet"] == second["planet"]:
                continue
            pairs.append({
                "first": {key: first[key] for key in ("planet", "angle", "local_time")},
                "second": {key: second[key] for key in ("planet", "angle", "local_time")},
                "separation_minutes": round(delta_minutes, 4),
            })
    return {
        "technique": "parans",
        "status": "used",
        "target_date": target_date,
        "method": "Swiss Ephemeris rise_trans latitude-aware angular events",
        "event_count": len(events),
        "events": events,
        "paran_pairs_within_4_minutes": pairs,
        "boundary": "Geometric rise/culmination/set simultaneity only; no interpretation or predictive claim is inferred.",
    }


def build_timing_techniques(
    *,
    transit_date: str | None = None,
    solar_return_year: int | None = None,
    secondary_progression_date: str | None = None,
    solar_arc_date: str | None = None,
    converse_secondary_progression_date: str | None = None,
    converse_solar_arc_date: str | None = None,
    midpoint_date: str | None = None,
    lunar_return_start_date: str | None = None,
    duration_scan_start_date: str | None = None,
    duration_scan_end_date: str | None = None,
    parans_date: str | None = None,
    **birth: Any,
) -> dict[str, Any]:
    """Materialize only the requested, independently auditable timing layers."""
    techniques: dict[str, Any] = {}
    if transit_date:
        techniques["transits"] = calculate_transit_to_natal(target_date=transit_date, **birth)
    if solar_return_year is not None:
        techniques["solar_return"] = calculate_solar_return(target_year=int(solar_return_year), **birth)
    if secondary_progression_date:
        techniques["secondary_progressions"] = calculate_secondary_progressions(
            target_date=secondary_progression_date, **birth
        )
    if solar_arc_date:
        techniques["solar_arc_directions"] = calculate_solar_arc_directions(target_date=solar_arc_date, **birth)
    if converse_secondary_progression_date:
        techniques["converse_secondary_progressions"] = calculate_converse_secondary_progressions(
            target_date=converse_secondary_progression_date, **birth
        )
    if converse_solar_arc_date:
        techniques["converse_solar_arc_directions"] = calculate_converse_solar_arc_directions(
            target_date=converse_solar_arc_date, **birth
        )
    if midpoint_date:
        techniques["midpoints"] = calculate_midpoints(target_date=midpoint_date, **birth)
    if lunar_return_start_date:
        techniques["lunar_return"] = calculate_lunar_return(start_date=lunar_return_start_date, **birth)
    if duration_scan_start_date and duration_scan_end_date:
        techniques["transit_duration_scan"] = calculate_transit_duration_scan(
            start_date=duration_scan_start_date,
            end_date=duration_scan_end_date,
            **birth,
        )
    if parans_date:
        techniques["parans"] = calculate_parans_status(target_date=parans_date, **birth)
    return techniques
