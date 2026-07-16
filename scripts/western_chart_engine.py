#!/usr/bin/env python3
"""Native, auditable tropical Western natal-chart calculation.

This module deliberately uses the project's existing Swiss Ephemeris binding
instead of bundling an AGPL Western astrology library.  It is a calculation
layer only: transits, progressions, solar arcs, returns, and interpretation
remain separate evidence layers.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone as fixed_timezone
from typing import Any
from zoneinfo import ZoneInfo

import swisseph as swe

try:
    from western_evidence_packet import build_western_evidence_packet
except ImportError:  # pragma: no cover - package import path
    from scripts.western_evidence_packet import build_western_evidence_packet


_PLANETS = {
    "sun": swe.SUN,
    "moon": swe.MOON,
    "mercury": swe.MERCURY,
    "venus": swe.VENUS,
    "mars": swe.MARS,
    "jupiter": swe.JUPITER,
    "saturn": swe.SATURN,
    "uranus": swe.URANUS,
    "neptune": swe.NEPTUNE,
    "pluto": swe.PLUTO,
    "true_node": swe.TRUE_NODE,
}
_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)
_ELEMENTS = {
    "Aries": "fire", "Leo": "fire", "Sagittarius": "fire",
    "Taurus": "earth", "Virgo": "earth", "Capricorn": "earth",
    "Gemini": "air", "Libra": "air", "Aquarius": "air",
    "Cancer": "water", "Scorpio": "water", "Pisces": "water",
}
_MODES = {
    "Aries": "cardinal", "Cancer": "cardinal", "Libra": "cardinal", "Capricorn": "cardinal",
    "Taurus": "fixed", "Leo": "fixed", "Scorpio": "fixed", "Aquarius": "fixed",
    "Gemini": "mutable", "Virgo": "mutable", "Sagittarius": "mutable", "Pisces": "mutable",
}
_RULERS = {
    "Aries": "mars", "Taurus": "venus", "Gemini": "mercury", "Cancer": "moon",
    "Leo": "sun", "Virgo": "mercury", "Libra": "venus", "Scorpio": "mars",
    "Sagittarius": "jupiter", "Capricorn": "saturn", "Aquarius": "saturn", "Pisces": "jupiter",
}
_ASPECTS = {"conjunction": 0.0, "sextile": 60.0, "square": 90.0, "trine": 120.0, "opposition": 180.0}
_ORB = {"sun": 8.0, "moon": 8.0, "ascendant": 5.0, "mc": 5.0}


def _longitude(value: float) -> float:
    return float(value) % 360.0


def _point(longitude: float, *, house: int | None = None, speed: float | None = None) -> dict[str, Any]:
    longitude = _longitude(longitude)
    point = {
        "longitude": round(longitude, 6),
        "sign": _SIGNS[int(longitude // 30)],
        "degree_in_sign": round(longitude % 30, 6),
    }
    if house is not None:
        point["house"] = house
    if speed is not None:
        point["speed_longitude"] = round(float(speed), 8)
        point["retrograde"] = bool(speed < 0)
    return point


def _house_for_longitude(longitude: float, cusps: list[float]) -> int:
    """Return Placidus house by testing each cusp-to-next-cusp circular arc."""
    longitude = _longitude(longitude)
    for index, cusp in enumerate(cusps):
        start = _longitude(cusp)
        end = _longitude(cusps[(index + 1) % 12])
        span = (end - start) % 360.0
        if (longitude - start) % 360.0 < span:
            return index + 1
    raise RuntimeError("Unable to assign longitude to a house")  # pragma: no cover


def _orb_for(left: str, right: str) -> float:
    return min(_ORB.get(left, 6.0), _ORB.get(right, 6.0))


def _aspects(points: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    names = list(points)
    found: list[dict[str, Any]] = []
    for index, left in enumerate(names):
        for right in names[index + 1:]:
            separation = abs(points[left]["longitude"] - points[right]["longitude"])
            separation = min(separation, 360.0 - separation)
            allowed_orb = _orb_for(left, right)
            for aspect, exact in _ASPECTS.items():
                orb = abs(separation - exact)
                if orb <= allowed_orb:
                    found.append({
                        "left": left,
                        "right": right,
                        "aspect": aspect,
                        "exact_degrees": exact,
                        "separation": round(separation, 6),
                        "orb": round(orb, 6),
                        "allowed_orb": allowed_orb,
                    })
    return sorted(found, key=lambda row: (row["orb"], row["left"], row["right"]))


def _distribution(planets: dict[str, dict[str, Any]]) -> dict[str, dict[str, int]]:
    elements = {name: 0 for name in ("fire", "earth", "air", "water")}
    modes = {name: 0 for name in ("cardinal", "fixed", "mutable")}
    for planet in planets.values():
        elements[_ELEMENTS[planet["sign"]]] += 1
        modes[_MODES[planet["sign"]]] += 1
    return {"elements": elements, "modes": modes}


def _ruler_chains(cusps: list[float], planets: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    chains: dict[str, list[str]] = {}
    for house, cusp in enumerate(cusps, start=1):
        sign = _SIGNS[int(_longitude(cusp) // 30)]
        chain: list[str] = []
        current = _RULERS[sign]
        for _ in range(12):
            if current in chain:
                break
            chain.append(current)
            current = _RULERS[planets[current]["sign"]]
        chains[str(house)] = chain
    return chains


def _birth_zone(value: str | float | int):
    if isinstance(value, str):
        return ZoneInfo(value), value
    offset = float(value)
    return fixed_timezone(timedelta(hours=offset)), f"UTC{offset:+g}"


def build_tropical_natal_chart(
    *,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    latitude: float,
    longitude: float,
    timezone: str | float | int,
    second: int = 0,
    house_system: str = "P",
) -> dict[str, Any]:
    """Calculate a tropical natal chart from local birth data using Swiss Ephemeris."""
    if len(house_system) != 1:
        raise ValueError("house_system must be a single Swiss Ephemeris house-system letter")
    zone, timezone_label = _birth_zone(timezone)
    local = datetime(year, month, day, hour, minute, second, tzinfo=zone)
    utc = local.astimezone(ZoneInfo("UTC"))
    jd_ut = swe.julday(utc.year, utc.month, utc.day, utc.hour + utc.minute / 60 + utc.second / 3600)
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    cusps_raw, ascmc = swe.houses_ex(jd_ut, float(latitude), float(longitude), house_system.encode("ascii"), 0)
    cusps = [_longitude(cusp) for cusp in cusps_raw]
    planets: dict[str, dict[str, Any]] = {}
    for name, planet_id in _PLANETS.items():
        values, _ = swe.calc_ut(jd_ut, planet_id, flags)
        position = _point(values[0], house=_house_for_longitude(values[0], cusps), speed=values[3])
        planets[name] = position
    angles = {
        "ascendant": _point(ascmc[0]),
        "mc": _point(ascmc[1]),
        "descendant": _point(ascmc[0] + 180.0),
        "ic": _point(ascmc[1] + 180.0),
    }
    aspect_points = {**planets, "ascendant": angles["ascendant"], "mc": angles["mc"]}
    natal = {
        "ascendant": angles["ascendant"],
        "mc": angles["mc"],
        "angles": angles,
        "planets": planets,
        "houses": [{"house": index + 1, "cusp": _point(cusp)} for index, cusp in enumerate(cusps)],
        "aspects": _aspects(aspect_points),
        "distribution": _distribution(planets),
        "house_ruler_chains": _ruler_chains(cusps, planets),
    }
    return {
        "source_engine": "pyswisseph_tropical",
        "engine_version": getattr(swe, "version", "unknown"),
        "zodiac": "tropical",
        "house_system": house_system.upper(),
        "calculation_contract": {
            "birth_timezone": timezone_label,
            "local_birth_time": local.isoformat(),
            "utc_birth_time": utc.isoformat(),
            "julian_day_ut": round(jd_ut, 8),
            "latitude": float(latitude),
            "longitude": float(longitude),
            "ephemeris": "Swiss Ephemeris via pyswisseph",
        },
        "natal": natal,
        "boundary": "Natal tropical calculation only; it does not calculate transits, progressions, solar arcs, returns, or interpretation.",
    }


def build_tropical_western_evidence_packet(*, route_packet: dict[str, Any], **birth: Any) -> dict[str, Any]:
    """Wrap direct natal calculation in the existing cross-system packet contract."""
    chart = build_tropical_natal_chart(**birth)
    packet = build_western_evidence_packet(
        route_packet=route_packet,
        natal=chart["natal"],
        timing_techniques={},
        signals=[],
    )
    packet.update({
        "source_engine": chart["source_engine"],
        "calculation": {
            "status": "used",
            "source_engine": chart["source_engine"],
            "zodiac": chart["zodiac"],
            "house_system": chart["house_system"],
            "contract": chart["calculation_contract"],
        },
        "native_chart": chart,
        "boundary": chart["boundary"],
    })
    return packet


def main() -> int:
    parser = argparse.ArgumentParser(description="Calculate an auditable tropical Western natal chart.")
    for name, kind in (("year", int), ("month", int), ("day", int), ("hour", int), ("minute", int)):
        parser.add_argument(f"--{name}", required=True, type=kind)
    parser.add_argument("--lat", required=True, type=float)
    parser.add_argument("--lon", required=True, type=float)
    parser.add_argument("--timezone", required=True)
    parser.add_argument("--second", type=int, default=0)
    parser.add_argument("--house-system", default="P")
    args = parser.parse_args()
    print(json.dumps(build_tropical_natal_chart(
        year=args.year, month=args.month, day=args.day, hour=args.hour, minute=args.minute, second=args.second,
        latitude=args.lat, longitude=args.lon, timezone=args.timezone, house_system=args.house_system,
    ), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
