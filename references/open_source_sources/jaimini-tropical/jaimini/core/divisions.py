"""Jaimini Divisional Charts (Varga).

Jaimini uses a specific set of divisional charts with the core principle:
  YANG (odd signs) → FORWARD  |  YIN (even signs) → REVERSE

This is the foundation of Jaimini's 阳顺阴逆 (yang forward, yin reverse).

Primary charts:
  - D-1: Rasi (birth chart) — already calculated
  - D-3: Drekkana (3-part division, ~40 min sensitivity)
  - D-9: Navamsa (9-part division, ~13 min 20 sec sensitivity)
  - D-12: Dwadashamsha (12-part division, ~10 min sensitivity)

References:
  - Jaimini Sutramritam, Chapter I
  - WeChat article: 阇弥尼九分盘系统介绍
  - dashaflow constants
"""

from ..engine.time_utils import ZODIAC, ZODIAC_FULL

# Sign lords
SIGN_LORDS = {
    0: 'Ma', 1: 'Ve', 2: 'Me', 3: 'Mo', 4: 'Su',
    5: 'Me', 6: 'Ve', 7: 'Ma', 8: 'Ju', 9: 'Sa',
    10: 'Sa', 11: 'Ju'
}

# Sign types: movable/chara (odd zodiac index), fixed/sthira, dual/dwiswabhava
SIGN_TYPE = {
    0: 'movable', 1: 'fixed', 2: 'dual',
    3: 'movable', 4: 'fixed', 5: 'dual',
    6: 'movable', 7: 'fixed', 8: 'dual',
    9: 'movable', 10: 'fixed', 11: 'dual',
}


def navamsa_sign(lon):
    """Calculate the Navamsa (D-9) sign for a given tropical longitude.

    Jaimini Navamsa follows 阳顺阴逆:
    Each sign's 9 navamsas are mapped differently based on sign group.

    Sign groups (Jaimini method):
      - Aries, Leo, Sagittarius (Fire signs): Start from Aries, FORWARD
      - Taurus, Virgo, Capricorn (Earth signs): Start from Capricorn, FORWARD
      - Gemini, Libra, Aquarius (Air signs): Start from Libra, FORWARD
      - Cancer, Scorpio, Pisces (Water signs): Start from Cancer, REVERSE

    Each navamsa = 3°20' (30° / 9)

    Args:
        lon: Tropical longitude (0-360)

    Returns:
        dict with sign_idx, sign, navamsa_number (1-9)
    """
    lon = lon % 360
    sign_idx = int(lon // 30)
    deg_in_sign = lon % 30

    # Which navamsa (0-8, 0-indexed)
    navamsa_part = int(deg_in_sign / (30.0 / 9))

    # Jaimini Navamsa mapping per sign group
    if sign_idx in (0, 4, 8):  # Fire: Aries, Leo, Sagittarius
        start_sign = 0  # Aries
        direction = 1    # Forward
    elif sign_idx in (1, 5, 9):  # Earth: Taurus, Virgo, Capricorn
        start_sign = 9  # Capricorn
        direction = 1    # Forward
    elif sign_idx in (2, 6, 10):  # Air: Gemini, Libra, Aquarius
        start_sign = 6  # Libra
        direction = 1    # Forward
    else:  # Water: Cancer(3), Scorpio(7), Pisces(11)
        start_sign = 3  # Cancer
        direction = -1   # REVERSE (key Jaimini difference)

    navamsa_sign_idx = (start_sign + direction * navamsa_part) % 12

    return {
        'sign_idx': navamsa_sign_idx,
        'sign': ZODIAC[navamsa_sign_idx],
        'navamsa_number': navamsa_part + 1,  # 1-9
        'longitude_in_navamsa': (deg_in_sign % (30.0 / 9)) * 9,  # 0-30 within navamsa
    }


def drekkana_sign(lon):
    """Calculate the Drekkana (D-3) sign for a given tropical longitude.

    Jaimini Drekkana — Parivrittitraya (Triple Rotation) method.

    Standard D-3: Each sign divided into 3 parts of 10° each.
    The first drekkana of a sign maps differently:
      - Movable signs: 1st=itself, 2nd=+4, 3rd=+8 (forward)
      - Fixed signs: 1st=+8, 2nd=itself, 3rd=+4 (forward from +8 sign)
      - Dual signs: 1st=+4, 2nd=+8, 3rd=itself (forward from +4 sign)

    But the Jaimini-specific Parivrittitraya method:
      - Odd signs: Forward mapping
      - Even signs: Reverse mapping

    Args:
        lon: Tropical longitude (0-360)

    Returns:
        dict with sign_idx, sign, drekkana_number (1-3)
    """
    lon = lon % 360
    sign_idx = int(lon // 30)
    deg_in_sign = lon % 30

    # Which drekkana (0-2, 0-indexed, each 10°)
    drekkana_part = int(deg_in_sign / 10.0)
    sign_type = SIGN_TYPE[sign_idx]

    # Standard Parivrittitraya mapping per sign type
    if sign_type == 'movable':
        offsets = [0, 4, 8]
    elif sign_type == 'fixed':
        offsets = [8, 0, 4]
    else:  # dual
        offsets = [4, 8, 0]

    drekkana_sign_idx = (sign_idx + offsets[drekkana_part]) % 12

    return {
        'sign_idx': drekkana_sign_idx,
        'sign': ZODIAC[drekkana_sign_idx],
        'drekkana_number': drekkana_part + 1,  # 1-3
        'longitude_in_drekkana': (deg_in_sign % 10.0) * 3,  # 0-30 within drekkana
    }


def dwadashamsha_sign(lon):
    """Calculate the Dwadashamsha (D-12) for a given tropical longitude.

    D-12: Each sign divided into 12 parts of 2°30' each.
    The first part starts from the sign itself and proceeds sequentially.
    """
    lon = lon % 360
    sign_idx = int(lon // 30)
    deg_in_sign = lon % 30

    # Which dwadashamsha (0-11, each 2.5°)
    d12_part = int(deg_in_sign / 2.5)

    d12_sign_idx = (sign_idx + d12_part) % 12

    return {
        'sign_idx': d12_sign_idx,
        'sign': ZODIAC[d12_sign_idx],
        'd12_number': d12_part + 1,  # 1-12
    }


def calc_all_divisions(planet_positions, asc_lon=None):
    """Calculate Jaimini divisional positions for all planets.

    Args:
        planet_positions: dict mapping planet name to {'lon': float}
        asc_lon: Ascendant longitude (for ascendant's D-9, D-3)

    Returns:
        dict with 'D9', 'D3', 'D12' keys, each a dict of planet→position info
    """
    divisions = {'D9': {}, 'D3': {}, 'D12': {}}

    all_points = dict(planet_positions)
    if asc_lon is not None:
        all_points['Asc'] = {'lon': asc_lon}

    for name, pos in all_points.items():
        lon = pos['lon'] if isinstance(pos, dict) and 'lon' in pos else pos
        divisions['D9'][name] = navamsa_sign(lon)
        divisions['D3'][name] = drekkana_sign(lon)
        divisions['D12'][name] = dwadashamsha_sign(lon)

    return divisions


def division_report(divisions, title="D-9 NAVAMSA"):
    """Generate a formatted text report of one divisional chart.

    Args:
        divisions: dict from calc_all_divisions
        title: 'D9', 'D3', or 'D12'

    Returns:
        str: Formatted report
    """
    if title not in divisions:
        return ""

    lines = []
    lines.append("-" * 50)
    lines.append(f"JAIMINI {title} DIVISIONAL CHART")
    lines.append("-" * 50)
    lines.append(f"{'Planet':<10}{'D-Sign':<8}{'Part #':<8}{'Long in D':<15}")
    lines.append("-" * 50)

    div = divisions[title]
    planet_order = ['Asc', 'Su', 'Mo', 'Ma', 'Me', 'Ju', 'Ve', 'Sa', 'Ra', 'Ke', 'Ur', 'Ne', 'Pl']
    for p in planet_order:
        if p in div:
            d = div[p]
            if title == 'D9':
                part = d.get('navamsa_number', '')
            elif title == 'D3':
                part = d.get('drekkana_number', '')
            else:
                part = d.get('d12_number', '')

            long_in_d = d.get('longitude_in_navamsa',
                     d.get('longitude_in_drekkana', 0))
            long_str = f"{long_in_d:.4f}°"

            lines.append(
                f"{p:<10}{d['sign']:<8}{part:<8}{long_str:<15}"
            )

    lines.append("-" * 50)
    return "\n".join(lines)
