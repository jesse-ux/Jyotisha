"""Jaimini Argala (Intervention) and Virodhargala (Obstruction) system.

Argala is Jaimini's unique planetary influence mechanism — fully independent
of Parashara's planetary aspects. It determines whether a house's affairs
will be supported or obstructed by planets in specific positions.

Core principle:
  From a reference point R, planets in houses (2, 4, 11) from R create
  positive ARGALA. Planets in houses (12, 10, 3) create VIRODHARGALA
  (obstruction) that blocks the corresponding argala.

  - House 2 ← obstructed by → House 12
  - House 4 ← obstructed by → House 10
  - House 3 (special, with 2+ malefics) creates additional argala

Whole Sign houses. Tropical zodiac. Rasi (D-1) chart only.

Reference: Jaimini Sutramritam, Chapter I, Pada 1
"""

from ..engine.time_utils import ZODIAC, ZODIAC_FULL

# Natural malefics in Jaimini (7-planet system)
NATURAL_MALEFICS = {'Su', 'Ma', 'Sa'}
NATURAL_BENEFICS = {'Mo', 'Me', 'Ju', 'Ve'}

# Argala positions relative to reference point
# Primary: houses that create positive argala
PRIMARY_ARGALA = {2, 4, 11}

# The obstruction mapping: argala_house → obstructing_house
VIRODHARGALA_MAP = {
    2: 12,   # House 2 argala blocked by planets in house 12
    4: 10,   # House 4 argala blocked by planets in house 10
    11: 3,   # House 11 argala blocked by planets in house 3
}

# Secondary argala: weaker positive influence
SECONDARY_ARGALA = {5, 9}

# All positions that matter for argala analysis
ALL_ARGALA_POSITIONS = PRIMARY_ARGALA | SECONDARY_ARGALA | {3}
ALL_VIRODHARGALA_POSITIONS = set(VIRODHARGALA_MAP.values())


def _house_from(ref_sign_idx, offset):
    """Get the sign index that is `offset` houses from ref_sign_idx.

    Whole Sign: house N from a sign = (sign + N - 1) % 12
    """
    return (ref_sign_idx + offset - 1) % 12


def _planets_in_house(house_sign_idx, planet_positions):
    """Find all planets occupying a given sign.

    Args:
        house_sign_idx: The sign index (0-11) of the house
        planet_positions: dict of planet → {'lon': float}

    Returns:
        list of planet names in that sign
    """
    planets = []
    for name, pos in planet_positions.items():
        if name in ('Ra', 'Ke', 'Ur', 'Ne', 'Pl'):
            continue  # Only 7 classical planets for Jaimini argala
        lon = pos['lon'] if isinstance(pos, dict) else pos
        sign_idx = int(lon // 30)
        if sign_idx == house_sign_idx:
            planets.append(name)
    return planets


def calc_argala(ref_sign_idx, planet_positions):
    """Calculate complete Argala analysis for a single reference point (house/sign).

    Args:
        ref_sign_idx: Sign index (0-11) of the reference point
        planet_positions: dict of planet → {'lon': float}

    Returns:
        dict with primary, specific, secondary argala and virodhargala details
    """
    result = {
        'ref_sign': ZODIAC[ref_sign_idx],
        'primary': {},
        'specific': None,
        'secondary': {},
        'virodhargala': {},
        'argala_count': 0,
        'virodhargala_count': 0,
        'net_result': 'neutral',
    }

    # Primary Argala: houses 2, 4, 11
    for h in PRIMARY_ARGALA:
        hs = _house_from(ref_sign_idx, h)
        planets = _planets_in_house(hs, planet_positions)
        block_h = VIRODHARGALA_MAP[h]  # which house obstructs this argala
        block_hs = _house_from(ref_sign_idx, block_h)
        blockers = _planets_in_house(block_hs, planet_positions)

        result['primary'][f'H{h}'] = {
            'sign': ZODIAC[hs],
            'sign_idx': hs,
            'planets': planets,
            'blocked_by_house': block_h,
            'blocked_by_sign': ZODIAC[block_hs],
            'blockers': blockers,
            'effective': len(planets) > len(blockers),
        }

        if planets:
            result['argala_count'] += 1
        if blockers:
            result['virodhargala_count'] += 1

    # Specific Argala: house 3, only if 2+ malefics present
    h3_sign = _house_from(ref_sign_idx, 3)
    h3_planets = _planets_in_house(h3_sign, planet_positions)
    h3_malefics = [p for p in h3_planets if p in NATURAL_MALEFICS]
    if len(h3_malefics) >= 2:
        result['specific'] = {
            'house': 3,
            'sign': ZODIAC[h3_sign],
            'sign_idx': h3_sign,
            'planets': h3_planets,
            'malefics': h3_malefics,
            'effective': True,
        }
        result['argala_count'] += 1
    else:
        result['specific'] = {
            'house': 3,
            'sign': ZODIAC[h3_sign],
            'sign_idx': h3_sign,
            'planets': h3_planets,
            'malefics': h3_malefics,
            'effective': False,
        }

    # Secondary Argala: houses 5 and 9
    for h in SECONDARY_ARGALA:
        hs = _house_from(ref_sign_idx, h)
        planets = _planets_in_house(hs, planet_positions)
        result['secondary'][f'H{h}'] = {
            'sign': ZODIAC[hs],
            'sign_idx': hs,
            'planets': planets,
        }

    # Net result
    if result['argala_count'] > result['virodhargala_count']:
        result['net_result'] = 'supported'
    elif result['argala_count'] < result['virodhargala_count']:
        result['net_result'] = 'obstructed'
    else:
        result['net_result'] = 'neutral'

    return result


def calc_all_argalas(houses, planet_positions):
    """Calculate Argala for all 12 houses.

    Returns:
        dict mapping house_num (1-12) to argala result
    """
    argalas = {}
    for house_num in range(1, 13):
        house_sign = houses[house_num - 1]['sign_idx']
        argalas[house_num] = calc_argala(house_sign, planet_positions)
    return argalas


def classify_argala_rajayoga(argala_result):
    """Classify Argala Rajayoga for a reference point.

    Poornargala  (Complete):  All 3 primary argala positions occupied → strongest
    Tripadargala (Three-foot): 2 of 3 primary positions occupied → strong
    Ardhargala   (Half):      1 of 3 primary positions occupied → moderate
    Padargala    (Quarter):   0 primary positions occupied, only virodhargala → weak
    """
    primary = argala_result['primary']
    occupied = sum(
        1 for h in ['H2', 'H4', 'H11']
        if len(primary[h]['planets']) > 0
    )

    if occupied == 3:
        return {'type': 'Poornargala', 'level': 4, 'desc': 'Complete — strongest Raja Yoga'}
    elif occupied == 2:
        return {'type': 'Tripadargala', 'level': 3, 'desc': 'Three-foot — strong Raja Yoga'}
    elif occupied == 1:
        return {'type': 'Ardhargala', 'level': 2, 'desc': 'Half — moderate Raja Yoga'}
    else:
        # Check if Virodhargala has planets — if so, even weaker
        virodh_planets = sum(
            len(primary[h]['blockers']) for h in ['H2', 'H4', 'H11']
        )
        if virodh_planets > 0:
            return {'type': 'Padargala', 'level': 1, 'desc': 'Quarter — weak, obstructed'}
        return {'type': 'Padargala', 'level': 1, 'desc': 'Quarter — weak, no support'}


def calc_karakamsa_rajayoga(atmakaraka_planet, atmakaraka_lon, divisions_d9, planet_positions):
    """Check for Karakamsa Rajayoga.

    Karakamsa = the Navamsa sign where the Atmakaraka is placed.
    A Rajayoga forms when:
      - AK is in its own Navamsa sign, OR
      - Benefic planets occupy or aspect the Karakamsa, OR
      - The Karakamsa lord is well-placed

    Args:
        atmakaraka_planet: The planet that is the Atmakaraka (e.g., 'Ju')
        atmakaraka_lon: Its tropical longitude
        divisions_d9: D-9 positions from calc_all_divisions
        planet_positions: Rasi planet positions

    Returns:
        dict with yoga analysis
    """
    from .divisions import navamsa_sign

    # Get Karakamsa = AK's Navamsa sign
    ak_d9 = navamsa_sign(atmakaraka_lon)
    karakamsa_sign = ak_d9['sign_idx']

    # Planets in Karakamsa (in D-9)
    planets_in_kk = []
    for name, d9 in divisions_d9.get('D9', {}).items():
        if d9['sign_idx'] == karakamsa_sign and name not in ('Ra', 'Ke'):
            planets_in_kk.append(name)

    # Check if AK is in own sign in D-9
    ak_own_d9 = False
    for name, d9 in divisions_d9.get('D9', {}).items():
        if name == atmakaraka_planet and d9['sign_idx'] == karakamsa_sign:
            # Check if AK's own sign
            from .divisions import SIGN_LORDS
            if SIGN_LORDS.get(karakamsa_sign) == atmakaraka_planet:
                ak_own_d9 = True

    # Check for benefics in Karakamsa
    benefics_in_kk = [p for p in planets_in_kk if p in NATURAL_BENEFICS]
    malefics_in_kk = [p for p in planets_in_kk if p in NATURAL_MALEFICS]

    yoga_level = 0
    description = []

    if ak_own_d9:
        yoga_level += 2
        description.append("AK in own Navamsa sign — strong soul-direction alignment")

    if len(benefics_in_kk) >= 2:
        yoga_level += 2
        description.append(f"Multiple benefics ({', '.join(benefics_in_kk)}) in Karakamsa")
    elif len(benefics_in_kk) == 1:
        yoga_level += 1
        description.append(f"One benefic ({benefics_in_kk[0]}) in Karakamsa")

    if len(malefics_in_kk) > 0:
        yoga_level -= 1
        description.append(f"Malefics ({', '.join(malefics_in_kk)}) in Karakamsa — challenges present")

    return {
        'karakamsa_sign': ZODIAC[karakamsa_sign],
        'karakamsa_sign_idx': karakamsa_sign,
        'ak_planet': atmakaraka_planet,
        'ak_in_own_navamsa': ak_own_d9,
        'planets_in_karakamsa': planets_in_kk,
        'benefics_in_karakamsa': benefics_in_kk,
        'malefics_in_karakamsa': malefics_in_kk,
        'yoga_level': max(0, yoga_level),
        'is_rajayoga': yoga_level >= 2,
        'description': '; '.join(description) if description else 'No significant Karakamsa Yoga',
    }


def argala_report(argalas, houses=None):
    """Generate formatted text report of Argala analysis for all houses.

    Args:
        argalas: result from calc_all_argalas()
        houses: house cusps (for planet_in_house mapping)

    Returns:
        str: Formatted report
    """
    lines = []
    lines.append("=" * 70)
    lines.append("JAIMINI ARGALA ANALYSIS (Whole Sign, Tropical Rasi Chart)")
    lines.append("=" * 70)

    for house_num in range(1, 13):
        a = argalas[house_num]
        yoga = classify_argala_rajayoga(a)

        lines.append(f"\n--- House {house_num} ({a['ref_sign']}) {'-' * 40}")
        lines.append(f"  Rajayoga: {yoga['type']} — {yoga['desc']}")

        # Primary Argala
        lines.append(f"  Primary Argala:")
        for h in ['H2', 'H4', 'H11']:
            info = a['primary'][h]
            planets_str = ', '.join(info['planets']) if info['planets'] else '—'
            block_str = (f"{', '.join(info['blockers'])}"
                         if info['blockers'] else '—')
            status = '+' if info['effective'] else 'x (blocked)'
            lines.append(
                f"    {h}: {info['sign']:<6} "
                f"planets=[{planets_str:<12}] "
                f"← block H{info['blocked_by_house']}({info['blocked_by_sign']})=[{block_str:<10}] "
                f"{status}"
            )

        # Specific Argala
        if a['specific']:
            s = a['specific']
            planets_str = ', '.join(s['planets']) if s['planets'] else '—'
            status = '+ (2+ malefics)' if s.get('effective') else '-- (need 2+ malefics)'
            lines.append(f"  Specific Argala: H3 {s['sign']:<6} planets=[{planets_str:<12}] {status}")

        # Secondary Argala
        lines.append(f"  Secondary Argala:")
        for h in ['H5', 'H9']:
            info = a['secondary'][h]
            planets_str = ', '.join(info['planets']) if info['planets'] else '—'
            lines.append(f"    {h}: {info['sign']:<6} planets=[{planets_str}]")

        # Net
        net_map = {'supported': '+ SUPPORTED', 'obstructed': 'x OBSTRUCTED', 'neutral': '~ NEUTRAL'}
        lines.append(f"  Net: {net_map.get(a['net_result'], a['net_result'])} "
                     f"(argala={a['argala_count']}, virodhargala={a['virodhargala_count']})")

    lines.append("\n" + "=" * 70)
    return "\n".join(lines)
