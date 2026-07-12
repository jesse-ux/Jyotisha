"""Swiss Ephemeris sunrise/sunset evidence for Saham day/night formula selection."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import swisseph as swe


class SahamDayNightError(ValueError):
    pass


def determine_daytime(moment: datetime, *, lat: float, lon: float, tz: float) -> dict[str, Any]:
    if not -90 <= float(lat) <= 90 or not -180 <= float(lon) <= 180:
        raise SahamDayNightError("invalid WGS84 latitude/longitude")
    local = moment.replace(tzinfo=None)
    jd = swe.julday(local.year, local.month, local.day, local.hour + local.minute / 60 + local.second / 3600 - float(tz))
    geopos = (float(lon), float(lat), 0.0)
    rise_status, rise = swe.rise_trans(jd - 1.0, swe.SUN, swe.CALC_RISE, geopos)
    set_status, sunset = swe.rise_trans(jd - 1.0, swe.SUN, swe.CALC_SET, geopos)
    if rise_status != 0 or set_status != 0:
        raise SahamDayNightError("sunrise_or_sunset_unavailable_for_location_date")
    sunrise_jd, sunset_jd = rise[0], sunset[0]
    # Normalize the next daily events around the queried instant.
    while sunrise_jd > jd:
        sunrise_jd -= 1.0
    while sunset_jd > jd:
        sunset_jd -= 1.0
    is_day = sunrise_jd <= jd < sunset_jd if sunrise_jd < sunset_jd else not (sunset_jd <= jd < sunrise_jd)
    return {
        "scope": "saham_daynight_swiss",
        "status": "computed",
        "is_daytime": is_day,
        "julian_day_ut": jd,
        "sunrise_jd_ut": sunrise_jd,
        "sunset_jd_ut": sunset_jd,
        "method": "swisseph.rise_trans",
        "boundary": "Formula-specific +30 degree exceptions must be applied by the Saham rule layer, not inferred from house placement.",
    }
