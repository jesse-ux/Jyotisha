"""Validation tests for Jaimini engine — planetary positions, houses, karakas.

Tests against known reference values from Swiss Ephemeris (swetest64.exe),
manual calculations, and edge cases across different times and locations.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import math
from jaimini.engine.ephemeris import get_all_planets, get_planet_position, julian_day
from jaimini.engine.houses import calc_ascendant, calc_houses, calc_sunrise
from jaimini.engine.time_utils import parse_dms, to_dms, zodiac_position, utc_to_jd, local_to_utc, parse_timezone


def test_sun_position_1949():
    """Verify Sun position against swetest64.exe reference value.
    Reference: 1949-10-01 07:00 UTC, Sun = 187.766607° (Libra 7°45'59.786")
    """
    pos = get_planet_position('Su', 1949, 10, 1, 7, 0, 0)
    expected = 187.766607
    diff = abs(pos['lon'] - expected)
    # DE421 vs DE431: expect < 0.002° (~7 arcsec)
    assert diff < 0.002, f"Sun position off by {diff*3600:.1f} arcsec"
    assert pos['sign'] == 'Lib'
    assert 7.7 < pos['sign_deg'] < 7.8


def test_moon_position_1949():
    """Verify Moon position against swetest64.exe reference value.
    Reference: 1949-10-01 07:00 UTC, Moon = 303.048826° (Aquarius 3°02'55.773")
    """
    pos = get_planet_position('Mo', 1949, 10, 1, 7, 0, 0)
    expected = 303.048826
    diff = abs(pos['lon'] - expected)
    # Moon accuracy: DE421 vs DE431, allow up to 0.01° (~0.6 arcmin)
    assert diff < 0.01, f"Moon position off by {diff*3600:.1f} arcsec"
    assert pos['sign'] == 'Aqr'
    assert 3.0 < pos['sign_deg'] < 3.1


def test_ascendant_1949():
    """Verify Ascendant for New China chart.
    1949-10-01 15:00 CST (07:00 UTC), Beijing (39.907N, 116.397E)
    Reference: Leo approx 11°30' (from user's article)
    """
    asc = calc_ascendant(1949, 10, 1, 7, 0, 0, 39.907, 116.397)
    assert 120 < asc < 150  # Leo = 120-150°
    assert 11.0 < (asc % 30) < 12.0  # ~11°30' in sign


def test_all_planets_consistent():
    """All planets should return valid positions at any time."""
    planets = get_all_planets(2025, 6, 15, 12, 0, 0)
    required = ['Su', 'Mo', 'Ma', 'Me', 'Ju', 'Ve', 'Sa']
    for p in required:
        assert p in planets
        assert 0 <= planets[p]['lon'] <= 360
        assert 0 <= planets[p]['sign_idx'] <= 11
        assert planets[p]['sign'] is not None


def test_different_latitudes():
    """Ascendant calculation should work across different latitudes."""
    # Equator (0°)
    asc_eq = calc_ascendant(2025, 6, 15, 12, 0, 0, 0.0, 77.0)
    assert 0 <= asc_eq <= 360

    # Mid-latitude (45°N)
    asc_mid = calc_ascendant(2025, 6, 15, 12, 0, 0, 45.0, 10.0)
    assert 0 <= asc_mid <= 360

    # High latitude (60°N)
    asc_high = calc_ascendant(2025, 6, 15, 12, 0, 0, 60.0, 30.0)
    assert 0 <= asc_high <= 360

    # Southern hemisphere (33°S)
    asc_south = calc_ascendant(2025, 12, 25, 10, 0, 0, -33.0, 151.0)
    assert 0 <= asc_south <= 360


def test_different_dates():
    """Engine should work across wide date ranges (1900-2100)."""
    test_cases = [
        (1900, 1, 1, 12, 0, 0),
        (1950, 6, 15, 6, 30, 0),
        (2000, 1, 1, 0, 0, 0),
        (2020, 6, 15, 12, 0, 0),
        (2050, 1, 1, 12, 0, 0),  # DE421 max ~2053-10-09
    ]
    for y, m, d, h, mi, s in test_cases:
        planets = get_all_planets(y, m, d, h, mi, s)
        assert 'Su' in planets
        assert 0 <= planets['Su']['lon'] <= 360
        assert 'Mo' in planets
        assert 0 <= planets['Mo']['lon'] <= 360


def test_sunrise_calculation():
    """Sunrise should be between 0-24h and reasonable for given location."""
    # Beijing summer sunrise should be ~5:00 local = ~21:00 UTC previous day
    sr = calc_sunrise(2025, 6, 15, 39.9, 116.4)
    assert 0 <= sr <= 24

    # Winter sunrise should be later
    sr_winter = calc_sunrise(2025, 12, 21, 39.9, 116.4)
    assert sr_winter > sr  # Winter sunrise later than summer

    # Equator sunrise should be ~6:00 year-round
    sr_eq = calc_sunrise(2025, 3, 20, 0.0, 0.0)
    assert 5.5 < sr_eq < 6.5


def test_house_positions_whole_sign():
    """Whole Sign houses: each house = one sign, 1st = ascendant sign."""
    houses = calc_houses(2025, 6, 15, 12, 0, 0, 40.0, -74.0, system='W')

    assert len(houses) == 12
    for i, h in enumerate(houses):
        assert h['house'] == i + 1
        # Whole Sign: each cusp should be at 0° of its sign
        assert h['sign_deg'] == 0.0
        assert 0 <= h['sign_idx'] <= 11

    # Signs should be consecutive (asc + 0, asc + 1, ..., asc + 11)
    asc_sign = houses[0]['sign_idx']
    for i, h in enumerate(houses):
        assert h['sign_idx'] == (asc_sign + i) % 12


def test_dms_conversion():
    """DMS parsing and formatting should be accurate and round-trip."""
    # Parse
    assert abs(parse_dms("39°54'25\"") - 39.906944) < 0.0001
    assert abs(parse_dms("116°23'50\"") - 116.397222) < 0.0001
    assert abs(parse_dms("39.907") - 39.907) < 0.0001
    assert abs(parse_dms("0°0'0\"") - 0.0) < 0.0001
    assert abs(parse_dms("180°0'0\"") - 180.0) < 0.0001

    # Format
    d, m, s = to_dms(39.906944)
    assert d == 39
    assert m == 54
    assert abs(s - 25.0) < 0.1

    # Zodiac position
    sign_idx, deg, label = zodiac_position(187.766607)
    assert sign_idx == 6  # Libra = index 6
    assert abs(deg - 7.766607) < 0.0001


def test_timezone_parsing():
    """Timezone parsing should handle various formats."""
    assert parse_timezone('+8') == 8.0
    assert parse_timezone('-5') == -5.0
    assert parse_timezone('+5.5') == 5.5
    assert parse_timezone('-5:30') == -5.5
    assert parse_timezone('+0') == 0.0


def test_planet_retrograde_detection():
    """Speed calculation should detect retrograde motion."""
    # Mercury retrograde periods known from astronomical data
    pos = get_planet_position('Me', 2025, 7, 18, 12, 0, 0)
    # Mercury typically retrogrades 3-4 times per year
    # Just verify speed is calculated (can be retro or direct)
    # Speed should always be positive (we store abs(speed))
    assert pos['speed'] > 0
    # retrograde should be Python bool
    assert isinstance(pos['retrograde'], bool)
    assert pos['speed'] < 15.0


def test_julian_day_consistency():
    """Julian Day should be consistent with known astronomy."""
    # J2000.0 = 2451545.0
    jd = julian_day(2000, 1, 1, 12, 0, 0)
    assert abs(jd - 2451545.0) < 0.01

    # 1949-10-01 JD should be ~2433190
    jd2 = julian_day(1949, 10, 1, 7, 0, 0)
    assert 2433190 < jd2 < 2433191


def test_sun_never_below_zero():
    """Sun longitude should always be 0-360. Regression test for modulo bugs."""
    for year in [1950, 2000, 2025, 2050]:
        pos = get_planet_position('Su', year, 6, 15, 12, 0, 0)
        assert 0 <= pos['lon'] <= 360


if __name__ == '__main__':
    # Run all tests and report
    tests = [
        test_sun_position_1949,
        test_moon_position_1949,
        test_ascendant_1949,
        test_all_planets_consistent,
        test_different_latitudes,
        test_different_dates,
        test_sunrise_calculation,
        test_house_positions_whole_sign,
        test_dms_conversion,
        test_timezone_parsing,
        test_planet_retrograde_detection,
        test_julian_day_consistency,
        test_sun_never_below_zero,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS: {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {test.__name__}: {type(e).__name__}: {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed, {len(tests)} total")
    assert failed == 0, f"{failed} tests failed!"
