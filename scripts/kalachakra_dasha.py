#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kalachakra_dasha.py — Kalachakra Dasha System (Variable Cycle)

The Kalachakra Dasha is one of the most intricate Nakshatra-based dasha systems.
It is based on the Moon's Nakshatra and its Pada (quarter) at birth.

Key Concepts:
    - 27 Nakshatras × 4 Padas = 108 Padas.
    - Each Pada maps to a specific Rashi (Zodiac sign).
    - Two directional modes:
        * Savya (clockwise / forward)
        * Apasavya (anti-clockwise / backward)
    - 9 lords (Navatara-like) govern the periods in a fixed sequence.

Nakshatra Grouping (per standard texts):
    Savya (forward) Nakshatras:
        Ashwini, Bharani, Krittika, Ashlesha, Magha, Moola,
        Purva Ashadha, Uttara Ashadha, Shravana, Dhanishta, Shatabhisha

    Apasavya (backward) Nakshatras:
        Rohini, Mrigashira, Ardra, Punarvasu, Pushya, Chitra,
        Swati, Vishakha, Anuradha, Jyeshtha, Purva Bhadrapada,
        Uttara Bhadrapada, Revati

    (Note: Some authorities include Abhijit; this implementation uses the 27-Nakshatra scheme.)

9-Lord Sequence:
    The 9 dasha lords correspond to the Navagraha sequence used in Kalachakra:
    1. Ketu   2. Venus  3. Sun    4. Moon   5. Mars   6. Mercury  7. Jupiter  8. Saturn  9. Rahu

    Their year allotments (one common traditional set):
        Ketu: 7, Venus: 20, Sun: 6, Moon: 10, Mars: 7,
        Mercury: 18, Jupiter: 16, Saturn: 19, Rahu: 17
    Total: 7+20+6+10+7+18+16+19+17 = 120 years

    However, Kalachakra is more commonly implemented with Rashi-based years.
    This module uses a simplified Rashi-year model (see _RASHI_YEARS below).

Rashi Dasha Sequence and Years (simplified standard model):

    Savya mode (forward through zodiac):
        Capricorn  7 → Aquarius  8 → Pisces    9 → Aries     10 →
        Taurus     11 → Gemini    12 → Cancer    13 → Leo       14 →
        Virgo      15 → Libra     16 → Scorpio   17 → Sagittarius 18
        Total = 150 years

    Apasavya mode (backward through zodiac):
        Cancer     13 → Gemini    12 → Taurus    11 → Aries     10 →
        Pisces      9 → Aquarius   8 → Capricorn  7 → Sagittarius 18 →
        Scorpio    17 → Libra     16 → Virgo     15 → Leo       14
        Total = 150 years

    Each of the 9 lords rules one consecutive Rashi in the sequence.
    The starting point is determined by Moon's Nakshatra Pada.

Reference: Brihat Parashara Hora Shastra and various classical commentaries on Kalachakra.
"""

from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha",
    "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha",
    "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
    "Uttara Bhadrapada", "Revati"
]

RASHIS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# 9 Kalachakra lords in order
KALA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Mercury", "Jupiter", "Saturn", "Rahu"
]

# Savya Rashi sequence (starting from Capricorn, forward)
SAVYA_RASHI_SEQ = [9, 10, 11, 0, 1, 2, 3, 4, 5, 6, 7, 8]
# Apasavya Rashi sequence (starting from Cancer, backward)
APASAVYA_RASHI_SEQ = [3, 2, 1, 0, 11, 10, 9, 8, 7, 6, 5, 4]

# Rashi year allotments (index 0-11)
# Savya: Cap 7, Aqua 8, Pis 9, Ari 10, Tau 11, Gem 12, Can 13, Leo 14, Vir 15, Lib 16, Sco 17, Sag 18
# Apasavya: Can 13, Gem 12, Tau 11, Ari 10, Pis 9, Aqua 8, Cap 7, Sag 18, Sco 17, Lib 16, Vir 15, Leo 14
_RASHI_YEARS_SAVYA = {
    9: 7, 10: 8, 11: 9, 0: 10, 1: 11, 2: 12,
    3: 13, 4: 14, 5: 15, 6: 16, 7: 17, 8: 18
}
_RASHI_YEARS_APASAVYA = {
    3: 13, 2: 12, 1: 11, 0: 10, 11: 9, 10: 8,
    9: 7, 8: 18, 7: 17, 6: 16, 5: 15, 4: 14
}

# Nakshatra → mode mapping (Savya = True, Apasavya = False)
# Per standard grouping
SAVYA_NAKSHATRAS = {0, 1, 2, 8, 9, 18, 19, 20, 21, 22, 23}
APASAVYA_NAKSHATRAS = {3, 4, 5, 6, 7, 13, 14, 15, 16, 17, 24, 25, 26}

# Pada → starting Rashi offset within the sequence (simplified model)
# For Savya: Pada 1 → Cap(0), Pada 2 → Aqu(1), Pada 3 → Pis(2), Pada 4 → Ari(3)
# For Apasavya: Pada 1 → Can(0), Pada 2 → Gem(1), Pada 3 → Tau(2), Pada 4 → Ari(3)
# The actual classical mapping is more nuanced; this is a practical approximation.
PADA_OFFSET_MAP = {1: 0, 2: 1, 3: 2, 4: 3}


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def _get_mode(nakshatra_index: int) -> str:
    """Return 'savya' or 'apasavya' based on Nakshatra."""
    if nakshatra_index in SAVYA_NAKSHATRAS:
        return "savya"
    elif nakshatra_index in APASAVYA_NAKSHATRAS:
        return "apasavya"
    else:
        # Default fallback (should not happen with valid 0-26 input)
        return "savya"


def _build_major_periods(mode: str, start_offset: int, birth_date: datetime) -> list:
    """
    Build major periods for Kalachakra Dasha.

    Args:
        mode: 'savya' or 'apasavya'.
        start_offset: offset into the 12-sign Rashi sequence.
        birth_date: datetime of birth.

    Returns:
        list of period dicts.
    """
    if mode == "savya":
        rashi_seq = SAVYA_RASHI_SEQ
        years_map = _RASHI_YEARS_SAVYA
    else:
        rashi_seq = APASAVYA_RASHI_SEQ
        years_map = _RASHI_YEARS_APASAVYA

    periods = []
    current_date = birth_date
    seq_len = len(rashi_seq)

    for i in range(seq_len):
        seq_idx = (start_offset + i) % seq_len
        rashi_idx = rashi_seq[seq_idx]
        lord_idx = i % 9  # 9 lords cycle through 12 rashis
        lord = KALA_LORDS[lord_idx]
        years = years_map[rashi_idx]
        end_date = current_date + timedelta(days=years * 365.25)

        periods.append({
            "lord": lord,
            "rashi": RASHIS[rashi_idx],
            "rashi_index": rashi_idx,
            "years": years,
            "start_date": current_date.isoformat(),
            "end_date": end_date.isoformat(),
        })
        current_date = end_date

    return periods


# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------

def calculate_kalachakra_dasha(birth_info: dict) -> dict:
    """
    Calculate Kalachakra Dasha for a native.

    Args:
        birth_info: dict containing:
            - "moon_nakshatra_index": int (0-26)
            - "moon_pada": int (1-4)
            - "birth_datetime": datetime object or ISO-format string (optional)

    Returns:
        dict with keys:
            - "mode": str — 'savya' or 'apasavya'
            - "major": list of major period dicts
            - "current": dict — the currently running major period
            - "total_cycle": int — sum of years in one full cycle
            - "starting_lord": str
            - "starting_rashi": str
    """
    nakshatra_idx = birth_info.get("moon_nakshatra_index", 0)
    pada = birth_info.get("moon_pada", 1)
    birth_dt = birth_info.get("birth_datetime")

    if isinstance(birth_dt, str):
        birth_dt = datetime.fromisoformat(birth_dt)
    if birth_dt is None:
        birth_dt = datetime.now()

    # Clamp pada to 1-4
    if not 1 <= pada <= 4:
        pada = ((pada - 1) % 4) + 1

    mode = _get_mode(nakshatra_idx)
    start_offset = PADA_OFFSET_MAP.get(pada, 0)

    major_periods = _build_major_periods(mode, start_offset, birth_dt)
    total_cycle = sum(p["years"] for p in major_periods)

    starting_lord = major_periods[0]["lord"] if major_periods else None
    starting_rashi = major_periods[0]["rashi"] if major_periods else None

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
        "mode": mode,
        "major": major_periods,
        "current": current_period,
        "total_cycle": total_cycle,
        "starting_lord": starting_lord,
        "starting_rashi": starting_rashi,
    }


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Example 1: Savya mode — Moon in Ashwini (Savya), Pada 1
    test_birth_1 = {
        "moon_nakshatra_index": 0,   # Ashwini (Savya)
        "moon_pada": 1,
        "birth_datetime": datetime(1990, 6, 15, 10, 30),
    }
    result_1 = calculate_kalachakra_dasha(test_birth_1)
    print("=" * 70)
    print("Test 1: Moon in Ashwini (Savya), Pada 1")
    print("=" * 70)
    print(f"Mode            : {result_1['mode']}")
    print(f"Starting Lord   : {result_1['starting_lord']}")
    print(f"Starting Rashi  : {result_1['starting_rashi']}")
    print(f"Total Cycle     : {result_1['total_cycle']} years")
    print("Major Periods:")
    for p in result_1["major"]:
        print(f"  {p['lord']:8s} | {p['rashi']:12s} | {p['years']:2d} years | {p['start_date'][:10]} → {p['end_date'][:10]}")
    print(f"Current Period  : {result_1['current']}")
    print()

    # Example 2: Apasavya mode — Moon in Rohini (Apasavya), Pada 2
    test_birth_2 = {
        "moon_nakshatra_index": 3,   # Rohini (Apasavya)
        "moon_pada": 2,
        "birth_datetime": datetime(1985, 3, 20, 8, 0),
    }
    result_2 = calculate_kalachakra_dasha(test_birth_2)
    print("=" * 70)
    print("Test 2: Moon in Rohini (Apasavya), Pada 2")
    print("=" * 70)
    print(f"Mode            : {result_2['mode']}")
    print(f"Starting Lord   : {result_2['starting_lord']}")
    print(f"Starting Rashi  : {result_2['starting_rashi']}")
    print(f"Total Cycle     : {result_2['total_cycle']} years")
    for p in result_2["major"]:
        print(f"  {p['lord']:8s} | {p['rashi']:12s} | {p['years']:2d} years | {p['start_date'][:10]} → {p['end_date'][:10]}")
    print(f"Current Period  : {result_2['current']}")
    print()

    # Example 3: Savya mode — Moon in Shravana (Savya), Pada 4
    test_birth_3 = {
        "moon_nakshatra_index": 21,  # Shravana (Savya)
        "moon_pada": 4,
        "birth_datetime": datetime(2000, 1, 1, 0, 0),
    }
    result_3 = calculate_kalachakra_dasha(test_birth_3)
    print("=" * 70)
    print("Test 3: Moon in Shravana (Savya), Pada 4")
    print("=" * 70)
    print(f"Mode            : {result_3['mode']}")
    print(f"Starting Lord   : {result_3['starting_lord']}")
    print(f"Starting Rashi  : {result_3['starting_rashi']}")
    print(f"Total Cycle     : {result_3['total_cycle']} years")
    for p in result_3["major"]:
        print(f"  {p['lord']:8s} | {p['rashi']:12s} | {p['years']:2d} years | {p['start_date'][:10]} → {p['end_date'][:10]}")
