#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ashtottari_dasha.py — Ashtottari Dasha System (108-Year Cycle)

Reference: Brihat Parashara Hora Shastra (BPHS), Chapter 19

Ashtottari Dasha is a conditional dasha system with a total cycle of 108 years.
It is applicable only when the Moon is in specific Nakshatras:

    - Krishna Paksha (waning Moon): Rohini, Ardra, Pushya, Ashlesha, Magha, Revati
    - Shukla Paksha (waxing Moon): Ashwini, Mrigashira, Punarvasu, Chitra, Shravana, Dhanishta

The 8 planetary lords and their year allotments:
    1. Sun        — 6 years
    2. Moon       — 15 years
    3. Mars       — 8 years
    4. Mercury    — 17 years
    5. Saturn     — 10 years
    6. Jupiter    — 19 years
    7. Rahu       — 12 years
    8. Venus      — 21 years

Total: 6 + 15 + 8 + 17 + 10 + 19 + 12 + 21 = 108 years.

The dasha sequence always runs: Sun → Moon → Mars → Mercury → Saturn → Jupiter → Rahu → Venus.
The starting lord is determined by the Moon's Nakshatra at birth.
"""

from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Nakshatra indices (0-based): Ashwini=0, Bharani=1, ..., Revati=26
NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha",
    "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha",
    "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
    "Uttara Bhadrapada", "Revati"
]

# Applicable Nakshatras for Ashtottari Dasha
SHUKLA_PAKSHA_NAKSHATRAS = {0, 4, 6, 13, 20, 22}   # Ashwini, Mrigashira, Punarvasu, Chitra, Shravana, Dhanishta
KRISHNA_PAKSHA_NAKSHATRAS = {3, 5, 7, 8, 9, 26}   # Rohini, Ardra, Pushya, Ashlesha, Magha, Revati

# Ashtottari planetary sequence and year allotments (BPHS Ch.19)
DASHA_SEQUENCE = [
    {"planet": "Sun", "years": 6},
    {"planet": "Moon", "years": 15},
    {"planet": "Mars", "years": 8},
    {"planet": "Mercury", "years": 17},
    {"planet": "Saturn", "years": 10},
    {"planet": "Jupiter", "years": 19},
    {"planet": "Rahu", "years": 12},
    {"planet": "Venus", "years": 21},
]

TOTAL_CYCLE = 108  # years

# Mapping from starting Nakshatra index to first dasha lord index in DASHA_SEQUENCE
# Per BPHS Ch.19:
#   - Rohini (3), Ardra (5), Pushya (7), Ashlesha (8), Magha (9), Revati (26)
#     → start from Sun (0)
#   - Ashwini (0), Mrigashira (4), Punarvasu (6)
#     → start from Mars (2)
#   - Chitra (13), Shravana (20), Dhanishta (22)
#     → start from Jupiter (5)
STARTING_LORD_MAP = {
    3: 0,   # Rohini -> Sun
    5: 0,   # Ardra -> Sun
    7: 0,   # Pushya -> Sun
    8: 0,   # Ashlesha -> Sun
    9: 0,   # Magha -> Sun
    26: 0,  # Revati -> Sun
    0: 2,   # Ashwini -> Mars
    4: 2,   # Mrigashira -> Mars
    6: 2,   # Punarvasu -> Mars
    13: 5,  # Chitra -> Jupiter
    20: 5,  # Shravana -> Jupiter
    22: 5,  # Dhanishta -> Jupiter
}

# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------

def is_ashtottari_applicable(moon_nakshatra_index: int, is_shukla_paksha: bool) -> bool:
    """
    Check whether Ashtottari Dasha is applicable for the given birth conditions.

    Args:
        moon_nakshatra_index: 0-based index of Moon's Nakshatra (0 = Ashwini).
        is_shukla_paksha: True if birth is in Shukla Paksha (waxing Moon), else False.

    Returns:
        bool: True if Ashtottari Dasha applies.
    """
    if is_shukla_paksha:
        return moon_nakshatra_index in SHUKLA_PAKSHA_NAKSHATRAS
    else:
        return moon_nakshatra_index in KRISHNA_PAKSHA_NAKSHATRAS


def _build_major_periods(start_lord_idx: int, birth_date: datetime) -> list:
    """
    Build the full list of major periods (Mahadashas) given the starting lord.

    Returns a list of dicts with keys: planet, years, start_date, end_date.
    """
    periods = []
    seq_len = len(DASHA_SEQUENCE)
    current_date = birth_date

    for i in range(seq_len):
        idx = (start_lord_idx + i) % seq_len
        lord = DASHA_SEQUENCE[idx]
        end_date = current_date + timedelta(days=lord["years"] * 365.25)
        periods.append({
            "planet": lord["planet"],
            "years": lord["years"],
            "start_date": current_date.isoformat(),
            "end_date": end_date.isoformat(),
        })
        current_date = end_date

    return periods


def calculate_ashtottari_dasha(birth_info: dict) -> dict:
    """
    Calculate Ashtottari Dasha for a native.

    Args:
        birth_info: dict containing:
            - "moon_nakshatra_index": int (0-26)
            - "is_shukla_paksha": bool
            - "birth_datetime": datetime object or ISO-format string

    Returns:
        dict with keys:
            - "applicable": bool — whether this dasha system applies
            - "major": list of major period dicts (planet, years, start/end dates)
            - "current": dict — the currently running major period
            - "total_cycle": int — 108
            - "starting_planet": str — first dasha lord
    """
    moon_idx = birth_info.get("moon_nakshatra_index")
    is_shukla = birth_info.get("is_shukla_paksha", True)
    birth_dt = birth_info.get("birth_datetime")

    if isinstance(birth_dt, str):
        birth_dt = datetime.fromisoformat(birth_dt)
    if birth_dt is None:
        birth_dt = datetime.now()

    applicable = is_ashtottari_applicable(moon_idx, is_shukla)

    if not applicable:
        return {
            "applicable": False,
            "major": [],
            "current": None,
            "total_cycle": TOTAL_CYCLE,
            "starting_planet": None,
            "reason": f"Moon Nakshatra '{NAKSHATRAS[moon_idx]}' does not qualify for Ashtottari Dasha under {'Shukla' if is_shukla else 'Krishna'} Paksha.",
        }

    start_lord_idx = STARTING_LORD_MAP.get(moon_idx, 0)
    starting_planet = DASHA_SEQUENCE[start_lord_idx]["planet"]

    major_periods = _build_major_periods(start_lord_idx, birth_dt)

    # Determine current period
    now = datetime.now()
    current_period = None
    for p in major_periods:
        p_start = datetime.fromisoformat(p["start_date"])
        p_end = datetime.fromisoformat(p["end_date"])
        if p_start <= now < p_end:
            current_period = p.copy()
            current_period["elapsed_years"] = (now - p_start).days / 365.25
            current_period["remaining_years"] = (p_end - now).days / 365.25
            break

    return {
        "applicable": True,
        "major": major_periods,
        "current": current_period,
        "total_cycle": TOTAL_CYCLE,
        "starting_planet": starting_planet,
    }


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Example 1: Applicable case — Moon in Rohini, Krishna Paksha
    test_birth_1 = {
        "moon_nakshatra_index": 3,   # Rohini
        "is_shukla_paksha": False,    # Krishna Paksha
        "birth_datetime": datetime(1990, 6, 15, 10, 30),
    }
    result_1 = calculate_ashtottari_dasha(test_birth_1)
    print("=" * 60)
    print("Test 1: Moon in Rohini, Krishna Paksha")
    print("=" * 60)
    print(f"Applicable: {result_1['applicable']}")
    print(f"Starting Planet: {result_1['starting_planet']}")
    print(f"Total Cycle: {result_1['total_cycle']} years")
    print("Major Periods:")
    for p in result_1["major"]:
        print(f"  {p['planet']:10s} | {p['years']:2d} years | {p['start_date'][:10]} → {p['end_date'][:10]}")
    print(f"Current Period: {result_1['current']}")
    print()

    # Example 2: Applicable case — Moon in Ashwini, Shukla Paksha
    test_birth_2 = {
        "moon_nakshatra_index": 0,   # Ashwini
        "is_shukla_paksha": True,     # Shukla Paksha
        "birth_datetime": datetime(1985, 3, 20, 8, 0),
    }
    result_2 = calculate_ashtottari_dasha(test_birth_2)
    print("=" * 60)
    print("Test 2: Moon in Ashwini, Shukla Paksha")
    print("=" * 60)
    print(f"Applicable: {result_2['applicable']}")
    print(f"Starting Planet: {result_2['starting_planet']}")
    print(f"Total Cycle: {result_2['total_cycle']} years")
    for p in result_2["major"]:
        print(f"  {p['planet']:10s} | {p['years']:2d} years | {p['start_date'][:10]} → {p['end_date'][:10]}")
    print(f"Current Period: {result_2['current']}")
    print()

    # Example 3: Non-applicable case — Moon in Bharani, Shukla Paksha
    test_birth_3 = {
        "moon_nakshatra_index": 1,   # Bharani
        "is_shukla_paksha": True,
        "birth_datetime": datetime(2000, 1, 1, 0, 0),
    }
    result_3 = calculate_ashtottari_dasha(test_birth_3)
    print("=" * 60)
    print("Test 3: Moon in Bharani, Shukla Paksha (Non-applicable)")
    print("=" * 60)
    print(f"Applicable: {result_3['applicable']}")
    print(f"Reason: {result_3['reason']}")
