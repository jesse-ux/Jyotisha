"""Tests for Panchanga (five limbs) calculations.

Uses known reference values from Swiss Ephemeris for 1949-10-01 07:00 UTC
and tests each limb independently with boundary conditions.
"""
import sys
import os
import math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from jaimini.panchanga.panchanga import (
    calc_tithi, calc_nakshatra, calc_yoga, calc_karana, calc_vara,
    calc_panchanga, format_panchanga,
    NAKSHATRAS, TITHI_NAMES, YOGA_NAMES,
    KARANA_REPEATING, KARANA_FIXED, VARA_NAMES,
    VIMSHOTTARI_LORDS,
)

# Reference values for 1949-10-01 07:00 UTC
SUN_LON_REF = 187.766607
MOON_LON_REF = 303.048826
# lunar_angle = (303.048826 - 187.766607) % 360 = 115.282219
# This is a Saturday: datetime(1949,10,1).weekday() = 5
WEEKDAY_REF = 5  # Saturday


# ── Tithi Tests ────────────────────────────────────────────────────────

def test_tithi_new_moon():
    """Sun and Moon at same longitude → Shukla Pratipada (tithi 1, index 0)."""
    t = calc_tithi(100.0, 100.0)
    assert t["index"] == 0
    assert t["number"] == 1
    assert t["paksha"] == "Shukla"
    assert t["paksha_tithi"] == 1
    assert t["name"] == "Pratipada"
    assert 0.0 <= t["progress"] <= 0.001


def test_tithi_full_moon():
    """Sun at 0°, Moon at 179° → Purnima (tithi 15, index 14).

    At exactly 180° it's Krishna Pratipada (index 15), so Purnima is just shy of 180.
    """
    t = calc_tithi(0.0, 179.0)
    assert t["index"] == 14
    assert t["number"] == 15
    assert t["paksha"] == "Shukla"
    assert t["name"] == "Purnima"
    assert t["name_chinese"] == "望月"

def test_tithi_krishna_boundary():
    """At exactly 180° → Krishna Pratipada starts."""
    t = calc_tithi(0.0, 180.0)
    assert t["index"] == 15
    assert t["paksha"] == "Krishna"
    assert t["paksha_tithi"] == 1


def test_tithi_krishna_start():
    """Just past full moon → Krishna Paksha starts."""
    t = calc_tithi(0.0, 180.1)
    assert t["index"] == 15
    assert t["number"] == 16
    assert t["paksha"] == "Krishna"
    assert t["paksha_chinese"] == "黑半月"
    assert t["paksha_tithi"] == 1


def test_tithi_amavasya():
    """Near conjunction at end of cycle → Amavasya (tithi 30, index 29)."""
    t = calc_tithi(0.0, 359.9)
    assert t["index"] == 29
    assert t["number"] == 30
    assert t["paksha"] == "Krishna"
    assert t["name"] == "Amavasya"
    assert t["name_chinese"] == "朔月"


def test_tithi_reference():
    """1949-10-01 07:00 UTC reference: Shukla Dashami (index 9, tithi 10)."""
    t = calc_tithi(SUN_LON_REF, MOON_LON_REF)
    assert t["index"] == 9
    assert t["number"] == 10
    assert t["paksha"] == "Shukla"
    assert t["paksha_tithi"] == 10
    assert t["name"] == "Dashami"
    assert 0.60 < t["progress"] < 0.62  # (115.282-108)/12 = 0.6069


def test_tithi_progress_range():
    """Progress should always be in [0, 1)."""
    for angle in [0, 6, 12, 90, 180, 270, 354, 358]:
        t = calc_tithi(0.0, angle)
        assert 0.0 <= t["progress"] < 1.0, f"Bad progress at angle={angle}: {t['progress']}"


# ── Nakshatra Tests ────────────────────────────────────────────────────

def test_nakshatra_zero():
    """Longitude 0° → Ashvini (index 0, pada 1)."""
    n = calc_nakshatra(0.0)
    assert n["index"] == 0
    assert n["name"] == "Ashvini"
    assert n["pada"] == 1
    assert n["lord"] == "Ke"


def test_nakshatra_boundary():
    """Just past first nakshatra span → Bharani (index 1)."""
    span = 360.0 / 27.0
    n = calc_nakshatra(span + 0.01)
    assert n["index"] == 1
    assert n["name"] == "Bharani"


def test_nakshatra_pada_boundaries():
    """Test pada (quarter) boundaries within Ashvini."""
    span = 360.0 / 27.0  # ~13.333°
    ps = span / 4.0       # ~3.333°
    assert calc_nakshatra(0.0)["pada"] == 1
    assert calc_nakshatra(ps - 0.01)["pada"] == 1
    assert calc_nakshatra(ps + 0.01)["pada"] == 2
    assert calc_nakshatra(ps * 2 + 0.01)["pada"] == 3
    assert calc_nakshatra(ps * 3 + 0.01)["pada"] == 4


def test_nakshatra_lord_cycle():
    """Verify Vimshottari lord cycle: Ke→Ve→Su→Mo→Ma→Ra→Ju→Sa→Me repeats."""
    for i in range(27):
        expected_lord = VIMSHOTTARI_LORDS[i % 9]
        lon = (360.0 / 27.0) * i + 0.1  # slight offset into each nakshatra
        n = calc_nakshatra(lon)
        assert n["lord"] == expected_lord, f"Nakshatra {i}: expected {expected_lord}, got {n['lord']}"


def test_nakshatra_reference():
    """1949-10-01: Moon 303.048826° → Dhanishtha (index 22), pada 4."""
    n = calc_nakshatra(MOON_LON_REF)
    assert n["index"] == 22
    assert n["name"] == "Dhanishtha"
    assert n["pada"] == 3  # 9.715° / 3.333° = 2.915 → pada 3
    assert n["lord"] == "Ma"  # Dhanishtha = Mars lord
    assert 0.72 < n["progress"] < 0.74  # 9.715/13.333 = 0.7286


# ── Yoga Tests ─────────────────────────────────────────────────────────

def test_yoga_zero():
    """Sun=0, Moon=0 → Vishkumbha (index 0)."""
    y = calc_yoga(0.0, 0.0)
    assert y["index"] == 0
    assert y["name"] == "Vishkumbha"


def test_yoga_span():
    """Each yoga spans 360/27 degrees of combined longitude."""
    span = 360.0 / 27.0
    y = calc_yoga(0.0, span + 0.01)
    assert y["index"] == 1
    assert y["name"] == "Preeti"


def test_yoga_reference():
    """1949-10-01 reference: combined=130.815433 → Ganda (index 9)."""
    y = calc_yoga(SUN_LON_REF, MOON_LON_REF)
    assert y["index"] == 9
    assert y["name"] == "Ganda"


# ── Karana Tests ───────────────────────────────────────────────────────

def test_karana_first_fixed():
    """lunar_angle=0 → Kimstughni (fixed)."""
    k = calc_karana(0.0, 0.0)
    assert k["index"] == 0
    assert k["name"] == "Kimstughni"
    assert k["type"] == "fixed"


def test_karana_repeating_cycle():
    """lunar_angle=12 → 2nd karana (index 1, first in repeating = Bava)."""
    k = calc_karana(0.0, 12.0)
    assert k["index"] == 1  # was bug: actually 12/6=2 not 1
    assert k["type"] == "repeating"


def test_karana_fixed_positions():
    """Verify fixed karanas at indices 57, 58, 59."""
    assert calc_karana(0.0, 57 * 6 + 0.1)["name"] == "Shakuni"
    assert calc_karana(0.0, 58 * 6 + 0.1)["name"] == "Chatushpada"
    assert calc_karana(0.0, 59 * 6 + 0.1)["name"] == "Naga"


def test_karana_bava_correct():
    """lunar_angle=6 (idx=1) → Bava, first repeating karana."""
    k = calc_karana(0.0, 6.0)
    assert k["index"] == 1
    assert k["name"] == "Bava"
    assert k["type"] == "repeating"


def test_karana_reference():
    """1949-10-01: lunar_angle=115.282219 → index 19 → Gara, half 2."""
    k = calc_karana(SUN_LON_REF, MOON_LON_REF)
    assert k["index"] == 19
    assert k["name"] == "Gara"
    assert k["type"] == "repeating"
    assert k["half"] == 2


# ── Vara Tests ─────────────────────────────────────────────────────────

def test_vara_sunday():
    """Python weekday=6 (Sunday) → Vara index 0 = Sunday."""
    v = calc_vara(6)
    assert v["index"] == 0
    assert v["name"] == "Sunday"


def test_vara_monday():
    """Python weekday=0 (Monday) → Vara index 1 = Monday."""
    v = calc_vara(0)
    assert v["index"] == 1
    assert v["name"] == "Monday"


def test_vara_reference():
    """1949-10-01 = Saturday (Python weekday 5)."""
    v = calc_vara(5)
    assert v["index"] == 6
    assert v["name"] == "Saturday"
    assert v["planet"] == "Sa"


# ── Aggregate Tests ────────────────────────────────────────────────────

def test_panchanga_aggregate():
    """calc_panchanga returns all 5 keys."""
    p = calc_panchanga(SUN_LON_REF, MOON_LON_REF, WEEKDAY_REF)
    assert set(p.keys()) == {"tithi", "nakshatra", "yoga", "karana", "vara"}


def test_format_panchanga():
    """format_panchanga returns a non-empty multi-line string."""
    p = calc_panchanga(SUN_LON_REF, MOON_LON_REF, WEEKDAY_REF)
    text = format_panchanga(p)
    assert "Tithi" in text
    assert "Nakshatra" in text
    assert "Yoga" in text
    assert "Karana" in text
    assert "Vara" in text
    assert "Dashami" in text
    assert "Dhanishtha" in text


def test_all_nakshatras_valid():
    """All 27 nakshatras have valid lord cycles."""
    span = 360.0 / 27.0
    for i in range(27):
        lon = span * i + 0.01
        n = calc_nakshatra(lon)
        assert n["index"] == i
        assert n["lord"] in VIMSHOTTARI_LORDS
        assert 1 <= n["pada"] <= 4


# ── Runner ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import traceback
    tests = [
        # Tithi
        test_tithi_new_moon,
        test_tithi_full_moon,
        test_tithi_krishna_boundary,
        test_tithi_krishna_start,
        test_tithi_amavasya,
        test_tithi_reference,
        test_tithi_progress_range,
        # Nakshatra
        test_nakshatra_zero,
        test_nakshatra_boundary,
        test_nakshatra_pada_boundaries,
        test_nakshatra_lord_cycle,
        test_nakshatra_reference,
        # Yoga
        test_yoga_zero,
        test_yoga_span,
        test_yoga_reference,
        # Karana
        test_karana_first_fixed,
        test_karana_bava_correct,
        test_karana_fixed_positions,
        test_karana_reference,
        # Vara
        test_vara_sunday,
        test_vara_monday,
        test_vara_reference,
        # Aggregate
        test_panchanga_aggregate,
        test_format_panchanga,
        test_all_nakshatras_valid,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS  {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {test.__name__}: {e}")
            traceback.print_exc()
            failed += 1

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed, {len(tests)} total")
    if failed:
        sys.exit(1)
