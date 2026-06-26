#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""First-pass Adhana / conception workflow scaffold.

This module does not claim final classical closure. It reuses existing skill
building blocks (D12, Gulika, special lagnas, Ghati-based timing sensitivity)
and exposes a structured trace for later classical rule hardening.
"""

from __future__ import annotations

from typing import Dict, Any

from jaimini import calc_special_lagnas_precise
from prashna import calc_gulika_simple
from varga import calc_all_vargas


SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
         'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']


def _norm(lon: float) -> float:
    return lon % 360.0


def _sign_name(sign_idx: int) -> str:
    return SIGNS[sign_idx % 12]


def _point_payload(lon: float, source: str, note: str = "") -> Dict[str, Any]:
    longitude = _norm(lon)
    sign_idx = int(longitude / 30) % 12
    return {
        "longitude": round(longitude, 4),
        "sign_idx": sign_idx,
        "sign": _sign_name(sign_idx),
        "degree_in_sign": round(longitude - sign_idx * 30, 4),
        "source": source,
        "note": note,
    }


def analyze_adhana_candidates(payload: Dict[str, Any]) -> Dict[str, Any]:
    asc_lon = float(payload["asc_lon"])
    sun_lon = float(payload["sun_lon"])
    moon_lon = float(payload["moon_lon"])
    gulika_lon = float(payload.get("gulika_lon", calc_gulika_simple(asc_lon, sun_lon, int(payload.get("weekday", 0)))))

    year = int(payload["year"])
    month = int(payload["month"])
    day = int(payload["day"])
    hour = int(payload["hour"])
    minute = int(payload["minute"])
    second = int(payload.get("second", 0))
    lat = float(payload["lat"])
    lon = float(payload["lon"])
    tz = float(payload["tz"])

    planet_lons = {
        "Sun": sun_lon,
        "Moon": moon_lon,
        "Rahu": float(payload.get("rahu_lon", 0.0)),
        "Ketu": float(payload.get("ketu_lon", 180.0)),
    }
    vargas = calc_all_vargas(planet_lons, asc_lon, [12])
    d12 = vargas.get("D12_Dwadashamsa", {})

    asc_sign_idx = int(asc_lon / 30) % 12
    special = calc_special_lagnas_precise(
        asc_sign_idx,
        year,
        month,
        day,
        hour,
        minute + second / 60.0,
        lat=lat,
        lon=lon,
        tz_offset=tz,
        second=second,
    )

    gl_sign_idx = special["GL"]["sign_idx"]
    hl_sign_idx = special["HL"]["sign_idx"]
    d12_moon = d12.get("Moon", {})
    d12_moon_sign_idx = d12_moon.get("sign_idx", int(moon_lon / 30) % 12)
    d12_moon_deg = d12_moon.get("degree_in_sign", moon_lon % 30)
    d12_moon_lon = d12_moon_sign_idx * 30 + d12_moon_deg

    candidate_lagna_lon = gl_sign_idx * 30 + ((gulika_lon % 24.0) / 24.0) * 30.0
    candidate_moon_lon = _norm(d12_moon_lon + ((gulika_lon - asc_lon) % 360) / 12.0)

    return {
        "system": "adhana_scaffold",
        "status": "partial_scaffold",
        "boundary": "This is not a final classical closure; it is a reusable Adhana scaffold built from validated skill components.",
        "inputs": {
            "asc_lon": asc_lon,
            "sun_lon": sun_lon,
            "moon_lon": moon_lon,
            "gulika_lon": round(gulika_lon, 6),
            "weekday": int(payload.get("weekday", 0)),
        },
        "birth_d12": d12,
        "special_lagnas": special,
        "candidate_adhana_lagna": _point_payload(
            candidate_lagna_lon,
            "special_lagnas.GL",
            note=f"GL sign {_sign_name(gl_sign_idx)} prioritized over HL {_sign_name(hl_sign_idx)} in scaffold mode.",
        ),
        "candidate_adhana_moon": _point_payload(
            candidate_moon_lon,
            "D12_moon_plus_gulika_arc",
            note="Uses D12 Moon anchor plus a normalized Gulika/Asc arc fraction as first-pass scaffold.",
        ),
        "rule_trace": [
            "Reused existing D12 calculator instead of inventing a conception-specific divisional engine.",
            "Reused precise special lagnas for Ghati-sensitive timing instead of new time math.",
            "Reused Gulika as a conception-sensitive point input because the screenshot workflow repeatedly references it.",
            "Returned candidate layers with explicit boundary text; no claim of final Adhana/Nisheka authority yet.",
        ],
    }
