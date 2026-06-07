#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
yogini_dasha.py — Yogini Dasha System (36-Year Cycle)

The Yogini Dasha is a Nakshatra-based dasha system with a total cycle of 36 years.
It consists of 8 Yoginis (female planetary deities), each ruling a specific number
of years. The sequence is fixed and cycles continuously.

The 8 Yoginis, their year allotments, and associated planets:

    Order | Yogini    | Years | Planet
    ------|-----------|-------|--------
      1   | Maya      |   1   | Sun
      2   | Bhadrika  |   2   | Moon
      3   | Jaya      |   3   | Mars
      4   | Rati      |   4   | Mercury
      5   | Mangala   |   5   | Jupiter
      6   | Pingala   |   6   | Saturn
      7   | Dhanya    |   7   | Venus
      8   | Bhramari  |   8   | Rahu

Total: 1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 = 36 years.

Starting Yogini:
    The starting Yogini is determined by the Ascendant (Lagna) Rashi.
    Per standard texts:
        - Aries / Leo / Sagittarius / Gemini / Libra / Aquarius
          → start from Maya (1)
        - Taurus / Virgo / Capricorn / Cancer / Scorpio / Pisces
          → start from Bhadrika (2)

    Alternative (more common) rule based on Lagna degree modulo 8:
        Lagna Nakshatra Pada determines the starting Yogini.
        For simplicity, this implementation uses the Ascendant Rashi rule above.

Reference: Various classical and modern Jyotish texts on Yogini Dasha.
"""

from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# 12 Rashis (Zodiac signs)
RASHIS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# Yogini sequence: fixed order, never changes
YOGINI_SEQUENCE = [
    {"name": "Maya", "years": 1, "planet": "Sun"},
    {"name": "Bhadrika", "years": 2, "planet": "Moon"},
    {"name": "Jaya", "years": 3, "planet": "Mars"},
    {"name": "Rati", "years": 4, "planet": "Mercury"},
    {"name": "Mangala", "years": 5, "planet": "Jupiter"},
    {"name": "Pingala", "years": 6, "planet": "Saturn"},
    {"name": "Dhanya", "years": 7, "planet": "Venus"},
    {"name": "Bhramari", "years": 8, "planet": "Rahu"},
]

TOTAL_CYCLE = 36  # years

# Lagna Rashi to starting Yogini index mapping
# Odd Rashis (0,4,8,2,6,10) → start from Maya (0)
# Even Rashis (1,5,9,3,7,11) → start from Bhadrika (1)
def _get_start_yogini_index(lagna_rashi_index: int) -> int:
    """Return starting Yogini index based on Ascendant Rashi."""
    if lagna_rashi_index % 2 == 0:
        return 0   # Maya
    else:
        return 1   # Bhadrika


# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------

def _build_major_periods(start_idx: int, birth_date: datetime) -> list:
    """
    Build the full list of major Yogini periods.

    Returns a list of dicts with keys: yogini, planet, years, start_date, end_date.
    """
    periods = []
    seq_len = len(YOGINI_SEQUENCE)
    current_date = birth_date

    for i in range(seq_len):
        idx = (start_idx + i) % seq_len
        yogini = YOGINI_SEQUENCE[idx]
        end_date = current_date + timedelta(days=yogini["years"] * 365.25)
        periods.append({
            "yogini": yogini["name"],
            "planet": yogini["planet"],
            "years": yogini["years"],
            "start_date": current_date.isoformat(),
            "end_date": end_date.isoformat(),
        })
        current_date = end_date

    return periods


def calculate_yogini_dasha(birth_info: dict) -> dict:
    """
    Calculate Yogini Dasha for a native.

    Args:
        birth_info: dict containing:
            - "lagna_rashi_index": int (0 = Aries, ..., 11 = Pisces)
            - "birth_datetime": datetime object or ISO-format string (optional)

    Returns:
        dict with keys:
            - "major": list of major period dicts
            - "current": dict — the currently running major period
            - "total_cycle": int — 36
            - "starting_yogini": str — first Yogini name
            - "starting_planet": str — planet of first Yogini
    """
    lagna_idx = birth_info.get("lagna_rashi_index", 0)
    birth_dt = birth_info.get("birth_datetime")

    if isinstance(birth_dt, str):
        birth_dt = datetime.fromisoformat(birth_dt)
    if birth_dt is None:
        birth_dt = datetime.now()

    start_idx = _get_start_yogini_index(lagna_idx)
    starting_yogini = YOGINI_SEQUENCE[start_idx]["name"]
    starting_planet = YOGINI_SEQUENCE[start_idx]["planet"]

    major_periods = _build_major_periods(start_idx, birth_dt)

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
        "major": major_periods,
        "current": current_period,
        "total_cycle": TOTAL_CYCLE,
        "starting_yogini": starting_yogini,
        "starting_planet": starting_planet,
    }


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Example 1: Ascendant in Aries (odd sign) → starts from Maya
    test_birth_1 = {
        "lagna_rashi_index": 0,   # Aries
        "birth_datetime": datetime(1990, 6, 15, 10, 30),
    }
    result_1 = calculate_yogini_dasha(test_birth_1)
    print("=" * 60)
    print("Test 1: Ascendant in Aries (odd sign)")
    print("=" * 60)
    print(f"Starting Yogini : {result_1['starting_yogini']} ({result_1['starting_planet']})")
    print(f"Total Cycle     : {result_1['total_cycle']} years")
    print("Major Periods:")
    for p in result_1["major"]:
        print(f"  {p['yogini']:10s} | {p['planet']:8s} | {p['years']} years | {p['start_date'][:10]} → {p['end_date'][:10]}")
    print(f"Current Period  : {result_1['current']}")
    print()

    # Example 2: Ascendant in Taurus (even sign) → starts from Bhadrika
    test_birth_2 = {
        "lagna_rashi_index": 1,   # Taurus
        "birth_datetime": datetime(1985, 3, 20, 8, 0),
    }
    result_2 = calculate_yogini_dasha(test_birth_2)
    print("=" * 60)
    print("Test 2: Ascendant in Taurus (even sign)")
    print("=" * 60)
    print(f"Starting Yogini : {result_2['starting_yogini']} ({result_2['starting_planet']})")
    print(f"Total Cycle     : {result_2['total_cycle']} years")
    for p in result_2["major"]:
        print(f"  {p['yogini']:10s} | {p['planet']:8s} | {p['years']} years | {p['start_date'][:10]} → {p['end_date'][:10]}")
    print(f"Current Period  : {result_2['current']}")
    print()

    # Example 3: Ascendant in Scorpio (even sign)
    test_birth_3 = {
        "lagna_rashi_index": 7,   # Scorpio
        "birth_datetime": datetime(2000, 1, 1, 0, 0),
    }
    result_3 = calculate_yogini_dasha(test_birth_3)
    print("=" * 60)
    print("Test 3: Ascendant in Scorpio (even sign)")
    print("=" * 60)
    print(f"Starting Yogini : {result_3['starting_yogini']} ({result_3['starting_planet']})")
    for p in result_3["major"]:
        print(f"  {p['yogini']:10s} | {p['planet']:8s} | {p['years']} years | {p['start_date'][:10]} → {p['end_date'][:10]}")
