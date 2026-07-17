#!/usr/bin/env python3
"""Swiss-Ephemeris Gulika calculator using the Prasna Marga Ghatika table."""
from __future__ import annotations

from datetime import datetime
from typing import Any

import swisseph as swe

try:
    from saham_daynight import determine_daytime
except ImportError:
    from scripts.saham_daynight import determine_daytime


# Monday=0, matching datetime.weekday(). Values are the end of Saturn's share
# measured in Ghatika from the relevant sunrise/sunset (30 Ghatika per period).
GHATIKA_END = {
    0: {"day": 22, "night": 6},
    1: {"day": 18, "night": 2},
    2: {"day": 14, "night": 26},
    3: {"day": 10, "night": 22},
    4: {"day": 6, "night": 18},
    5: {"day": 2, "night": 14},
    6: {"day": 26, "night": 10},
}

# Saturn's zero-based share in eight equal day/night parts. Python weekday:
# Monday=0. This is the variant used by PyJHora's public black-box oracle.
SATURN_PART_START = {
    0: {"day": 5, "night": 1},
    1: {"day": 4, "night": 0},
    2: {"day": 3, "night": 6},
    3: {"day": 2, "night": 5},
    4: {"day": 1, "night": 4},
    5: {"day": 0, "night": 3},
    6: {"day": 6, "night": 2},
}


def _sidereal_ascendant(jd_ut: float, lat: float, lon: float) -> float:
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    cusps, ascmc = swe.houses_ex(jd_ut, lat, lon, b"P", swe.FLG_SIDEREAL)
    return float(ascmc[0]) % 360


def calculate_gulika(
    moment: datetime,
    *,
    lat: float,
    lon: float,
    tz: float,
    method: str = "saturn_part_start",
) -> dict[str, Any]:
    """Return Gulika from local moment/location using Swiss sunrise and sunset."""
    daynight = determine_daytime(moment, lat=lat, lon=lon, tz=tz)
    is_day = bool(daynight["is_daytime"])
    period = "day" if is_day else "night"
    start_jd = daynight["sunrise_jd_ut"] if is_day else daynight["sunset_jd_ut"]
    end_jd = daynight["sunset_jd_ut"] if is_day else daynight["sunrise_jd_ut"] + 1.0
    if end_jd <= start_jd:
        end_jd += 1.0
    if method == "saturn_part_start":
        part_index = SATURN_PART_START[moment.weekday()][period]
        segment_fraction = part_index / 8.0
        ghatika_end = None
    elif method == "legacy_ghatika_end":
        part_index = None
        ghatika_end = GHATIKA_END[moment.weekday()][period]
        segment_fraction = ghatika_end / 30.0
    else:
        raise ValueError("method must be saturn_part_start or legacy_ghatika_end")
    segment_jd = start_jd + (end_jd - start_jd) * segment_fraction
    longitude = _sidereal_ascendant(segment_jd, float(lat), float(lon))
    return {
        "scope": "gulika_prasna_marga",
        "status": "partial",
        "longitude": round(longitude, 6),
        "sign_idx": int(longitude / 30) % 12,
        "degree_in_sign": round(longitude % 30, 6),
        "period": period,
        "weekday": moment.weekday(),
        "method": method,
        "part_index": part_index,
        "segment_fraction": segment_fraction,
        "ghatika_end": ghatika_end,
        "segment_jd_ut": segment_jd,
        "daynight_evidence": daynight,
        "ayanamsa": "lahiri",
        "rule_source": "references/prashna-complete-guide.md#3.5",
        "boundary": "PyJHora-aligned Saturn-part-start variant. Numeric parity is evidence only and does not enable Prashna verdict layers.",
    }
