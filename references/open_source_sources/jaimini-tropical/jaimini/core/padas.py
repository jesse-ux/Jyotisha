"""Arudha Pada (Jaimini Padas) calculation.

Arudha = the "mounted" or "reflected" image of a house.
The Pada reveals how a house's matters manifest in the external world.

Formula:
  Pada = LordSign + (LordSign - HouseSign)
  Padāraṇī: count from house to lord, then count same distance from lord onward.

Exception: If Pada falls in the same sign as the house or the 7th from it,
move it to the 10th from the house.

References:
  - Jaimini Sutramritam, Chapter I, Pada 1
  - dashaflow jaimini.py (MIT licensed)
"""

from ..engine.time_utils import ZODIAC, ZODIAC_FULL

# Sign lords (same as dasha module)
SIGN_LORDS = {
    0: 'Ma', 1: 'Ve', 2: 'Me', 3: 'Mo', 4: 'Su',
    5: 'Me', 6: 'Ve', 7: 'Ma', 8: 'Ju', 9: 'Sa',
    10: 'Sa', 11: 'Ju'
}

# Pada names
PADA_NAMES = {
    1: 'AL',   2: 'A2',   3: 'A3',   4: 'A4',
    5: 'A5',   6: 'A6',   7: 'A7',   8: 'A8',
    9: 'A9',  10: 'A10', 11: 'A11', 12: 'UL',
}

PADA_FULL_NAMES = {
    1: 'Arudha Lagna',     2: 'Dhana Pada',
    3: 'Vikrama Pada',     4: 'Sukha Pada',
    5: 'Mantra Pada',      6: 'Roga Pada',
    7: 'Dara Pada',        8: 'Mrityu Pada',
    9: 'Dharma Pada',     10: 'Karma Pada',
    11: 'Labha Pada',      12: 'Upapada',
}


def calc_arudha_pada(house_sign_idx, planet_positions):
    """Calculate Arudha Pada for a single house (1-indexed).

    Args:
        house_sign_idx: Sign index (0-11) of the house whose Pada to calculate
        planet_positions: dict mapping planet name to {'lon': float}

    Returns:
        dict with sign_idx, sign, name, exception_triggered
    """
    lord = SIGN_LORDS[house_sign_idx]
    if lord not in planet_positions:
        return None

    lord_lon = planet_positions[lord]['lon']
    lord_sign_idx = int(lord_lon // 30)

    # Count from house sign to lord's sign (1-based, forward)
    distance = ((lord_sign_idx - house_sign_idx) % 12) + 1

    # Pada = same distance from lord's sign forward
    pada_idx = (lord_sign_idx + distance - 1) % 12

    # Exception: if pada falls in the house itself or 7th from it → move to 10th
    seventh = (house_sign_idx + 6) % 12
    exception_triggered = False

    if pada_idx == house_sign_idx or pada_idx == seventh:
        pada_idx = (house_sign_idx + 9) % 12
        exception_triggered = True

    return {
        'sign_idx': pada_idx,
        'sign': ZODIAC[pada_idx],
        'sign_full': ZODIAC_FULL[pada_idx],
        'lord': SIGN_LORDS[pada_idx],
        'exception_triggered': exception_triggered,
    }


def calc_all_padas(asc_sign_idx, planet_positions):
    """Calculate Arudha Padas for all 12 houses.

    Args:
        asc_sign_idx: Ascendant sign index (0-11)
        planet_positions: dict mapping planet name to {'lon': float}

    Returns:
        dict mapping house_num (1-12) to pada info
    """
    padas = {}
    for house_num in range(1, 13):
        house_sign_idx = (asc_sign_idx + house_num - 1) % 12
        pada = calc_arudha_pada(house_sign_idx, planet_positions)
        if pada:
            pada['house_num'] = house_num
            pada['name'] = PADA_NAMES.get(house_num, f'A{house_num}')
            pada['full_name'] = PADA_FULL_NAMES.get(house_num, '')
            padas[house_num] = pada

    return padas


def calc_upapada(asc_sign_idx, planet_positions):
    """Calculate Upapada Lagna (Arudha of 12th house).

    UL is critical for spouse analysis in Jaimini.
    The 2nd from UL indicates marriage longevity.
    """
    ul_house_sign = (asc_sign_idx + 11) % 12  # 12th house
    ul = calc_arudha_pada(ul_house_sign, planet_positions)
    if ul:
        ul['second_from_ul'] = ZODIAC[(ul['sign_idx'] + 1) % 12]
        ul['description'] = (
            f"Upapada in {ul['sign_full']} — spouse characteristics "
            f"shaped by {ul['lord']}. 2nd from UL "
            f"({ul['second_from_ul']}) indicates marriage longevity."
        )
    return ul


def calc_graha_pada(planet_name, planet_positions):
    """Calculate Graha Pada (planetary Arudha) for a specific planet.

    Graha Pada = reflection of a planet's position, used for planet-specific
    material manifestations.

    Formula: Pada = PlanetSign + (PlanetSign - PlanetLordSign)
    """
    if planet_name not in planet_positions:
        return None

    planet_lon = planet_positions[planet_name]['lon']
    planet_sign = int(planet_lon // 30)

    planet_lord = SIGN_LORDS[planet_sign]
    if planet_lord not in planet_positions:
        return None

    lord_lon = planet_positions[planet_lord]['lon']
    lord_sign = int(lord_lon // 30)

    # Count from planet sign to lord sign
    distance = ((lord_sign - planet_sign) % 12) + 1

    # Graha Pada = same distance from lord sign
    pada_idx = (lord_sign + distance - 1) % 12

    return {
        'planet': planet_name,
        'planet_sign': ZODIAC[planet_sign],
        'pada_sign_idx': pada_idx,
        'pada_sign': ZODIAC[pada_idx],
    }


def pada_report(padas):
    """Generate formatted text report of all Arudha Padas."""
    lines = []
    lines.append("=" * 60)
    lines.append("ARUDHA PADA (Jaimini System)")
    lines.append("=" * 60)
    lines.append(f"{'House':<8}{'Pada':<8}{'Sign':<12}{'Full Name':<22}{'Exception'}")
    lines.append("-" * 60)

    for h in range(1, 13):
        if h in padas:
            p = padas[h]
            exc = 'YES (→10th)' if p.get('exception_triggered') else '—'
            lines.append(
                f"House {h:<2}   {p['name']:<8}"
                f"{p['sign']:<12}"
                f"{p['full_name']:<22}"
                f"{exc}"
            )

    lines.append("=" * 60)
    return "\n".join(lines)
