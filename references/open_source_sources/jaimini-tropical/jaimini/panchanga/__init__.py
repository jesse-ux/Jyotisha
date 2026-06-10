"""Panchanga — 五支时间历法 (Five Limbs of Vedic Timekeeping).

Provides pure-arithmetic calculation of Tithi, Nakshatra, Nitya Yoga, Karana,
and Vara from Sun and Moon longitudes. Callers supply pre-computed longitudes
from the ephemeris layer.
"""

from .panchanga import (
    # Constants
    NAKSHATRAS,
    TITHI_NAMES,
    YOGA_NAMES,
    KARANA_REPEATING,
    KARANA_FIXED,
    VARA_NAMES,
    VIMSHOTTARI_LORDS,
    PLANET_FULL_NAMES,
    # Calculation functions
    calc_tithi,
    calc_nakshatra,
    calc_yoga,
    calc_karana,
    calc_vara,
    calc_panchanga,
    format_panchanga,
)

__all__ = [
    "NAKSHATRAS", "TITHI_NAMES", "YOGA_NAMES",
    "KARANA_REPEATING", "KARANA_FIXED", "VARA_NAMES",
    "VIMSHOTTARI_LORDS", "PLANET_FULL_NAMES",
    "calc_tithi", "calc_nakshatra", "calc_yoga",
    "calc_karana", "calc_vara", "calc_panchanga",
    "format_panchanga",
]
