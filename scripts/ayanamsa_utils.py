#!/usr/bin/env python3
"""Shared Swiss Ephemeris ayanamsa helpers.

Swiss Ephemeris stores sidereal mode globally inside the process. Any helper
that calls calc_ut(..., FLG_SIDEREAL) must set the intended mode explicitly.
"""

from __future__ import annotations

from typing import Any

try:
    import swisseph as swe
except ImportError:  # pragma: no cover
    swe = None


AYANAMSA_MODES = {
    'lahiri': getattr(swe, 'SIDM_LAHIRI', 1) if swe else 1,
    'raman': getattr(swe, 'SIDM_RAMAN', 3) if swe else 3,
    'kp': getattr(swe, 'SIDM_KRISHNAMURTI', 5) if swe else 5,
    'krishnamurti': getattr(swe, 'SIDM_KRISHNAMURTI', 5) if swe else 5,
    'fagan_bradley': getattr(swe, 'SIDM_FAGAN_BRADLEY', 0) if swe else 0,
    'djwhal_khul': getattr(swe, 'SIDM_DJWHAL_KHUL', 6) if swe else 6,
    'sassanian': getattr(swe, 'SIDM_SASSANIAN', 16) if swe else 16,
    'true_citra': getattr(swe, 'SIDM_TRUE_CITRA', 27) if swe else 27,
}

AYANAMSA_DISPLAY_NAMES = {
    'lahiri': 'Lahiri',
    'raman': 'Raman',
    'kp': 'Krishnamurti/KP',
    'krishnamurti': 'Krishnamurti/KP',
    'fagan_bradley': 'Fagan-Bradley',
    'djwhal_khul': 'Djwhal Khul',
    'sassanian': 'Sassanian',
    'true_citra': 'True Citra',
}

ACTIVE_AYANAMSA_NAME = 'lahiri'


def normalize_ayanamsa_name(name: Any = None) -> str:
    key = str(name or 'lahiri').strip().lower().replace('-', '_')
    if key in ('krishnamurti_paddhati', 'krishnamurti/kp'):
        key = 'kp'
    return key if key in AYANAMSA_MODES else 'lahiri'


def ayanamsa_display_name(name: Any = None) -> str:
    key = normalize_ayanamsa_name(name)
    return AYANAMSA_DISPLAY_NAMES.get(key, key.title())


def current_ayanamsa_name(args: Any = None) -> str:
    name = getattr(args, 'ayanamsa', None) if args is not None else None
    return normalize_ayanamsa_name(name or ACTIVE_AYANAMSA_NAME)


def apply_ayanamsa(name: Any = 'lahiri', swe_module: Any = None) -> bool:
    """Set Swiss Ephemeris sidereal mode explicitly."""
    global ACTIVE_AYANAMSA_NAME
    module = swe_module or swe
    if module is None:
        return False
    key = normalize_ayanamsa_name(name)
    try:
        module.set_sid_mode(AYANAMSA_MODES[key])
    except Exception:
        return False
    ACTIVE_AYANAMSA_NAME = key
    return True


def sidereal_flags(swe_module: Any, ayanamsa_name: Any = 'lahiri') -> int:
    apply_ayanamsa(ayanamsa_name, swe_module)
    return getattr(swe_module, 'FLG_SWIEPH', 2) | getattr(swe_module, 'FLG_SIDEREAL', 65536)
