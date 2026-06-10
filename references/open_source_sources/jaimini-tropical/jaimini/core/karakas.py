"""Jaimini Chara Karaka (Variable Significators) calculation.

Determines the 7 or 8 Chara Karakas based on planetary degrees within signs.
Uses Tropical (Sayana) longitudes.

Key principle: The planet with the highest degree within its sign becomes the
Atmakaraka (AK), the next highest becomes Amatyakaraka (AmK), and so on.

Reference: Jaimini Sutramritam, Chapter I, Pada I
"""

from ..engine.time_utils import ZODIAC

# Karaka names and their order (highest degree = AK first, then descending)
KARAKA_NAMES_7 = [
    'AK',   # Atmakaraka (Self / soul)
    'AmK',  # Amatyakaraka (Mind / advisor)
    'BK',   # Bhratrikaraka (Siblings / courage)
    'MK',   # Matrikaraka (Mother / nurturing)
    'PK',   # Pitrikaraka (Father / fortune)
    'GK',   # Gnatikaraka (Relatives / obstacles)
    'DK',   # Darakaraka (Spouse / partnerships)
]

KARAKA_NAMES_8 = [
    'AK', 'AmK', 'BK', 'MK', 'PK', 'GK', 'DK', 'NK'
    # NK = Naikaraka (Rahu's karaka role when included)
]

# Full names
KARAKA_FULL_NAMES = {
    'AK': 'Atmakaraka',
    'AmK': 'Amatyakaraka',
    'BK': 'Bhratrikaraka',
    'MK': 'Matrikaraka',
    'PK': 'Pitrikaraka',
    'GK': 'Gnatikaraka',
    'DK': 'Darakaraka',
    'NK': 'Naikaraka',
}

# Fixed (Sthira) Karakas - permanent significations regardless of degree order
STHIRA_KARAKAS = {
    'Su': {'karaka': 'PK', 'role': 'Father'},
    'Mo': {'karaka': 'MK', 'role': 'Mother'},
    'Ma': {'karaka': 'BK', 'role': 'Siblings'},
    'Me': {'karaka': 'AmK', 'role': 'Career/Profession'},
    'Ju': {'karaka': 'PK', 'role': 'Knowledge/Fortune'},
    'Ve': {'karaka': 'DK', 'role': 'Spouse'},
    'Sa': {'karaka': 'GK/DK', 'role': 'Suffering/Service'},
}

# Planets that participate in Chara Karaka (Ketu is excluded!)
KARAKA_PLANETS_7 = ['Su', 'Mo', 'Ma', 'Me', 'Ju', 'Ve', 'Sa']
KARAKA_PLANETS_8 = ['Su', 'Mo', 'Ma', 'Me', 'Ju', 'Ve', 'Sa', 'Ra']


def calc_chara_karakas(planet_positions, include_rahu=False):
    """Calculate Chara Karakas from planetary positions.

    Args:
        planet_positions: dict mapping planet name ('Su', 'Mo', etc.) to dict with 'lon' key
        include_rahu: if True, use 8-karaka system including Rahu; if False, 7-planet system

    Returns:
        list of dict: Each karaka with 'planet', 'name', 'abbr', 'degree_in_sign', 'lon'
    """
    planets = KARAKA_PLANETS_8 if include_rahu else KARAKA_PLANETS_7
    karaka_names = KARAKA_NAMES_8 if include_rahu else KARAKA_NAMES_7

    # Collect planet data with degree-within-sign
    planet_data = []
    for p in planets:
        if p not in planet_positions:
            continue
        pos = planet_positions[p]
        lon = pos['lon'] if isinstance(pos, dict) else pos

        # Degree within sign (0-30)
        deg_in_sign = lon % 30
        planet_data.append({
            'planet': p,
            'lon': lon,
            'deg_in_sign': deg_in_sign,
            'sign_idx': int(lon // 30),
            'sign': ZODIAC[int(lon // 30)],
        })

    # Sort by degree within sign, descending (highest = AK)
    # Tie-break: if same degree, compare absolute longitude (360° absolute)
    planet_data.sort(key=lambda x: (-x['deg_in_sign'], -(x['lon'] % 360)))

    # Assign karaka roles
    karakas = []
    for i, pd in enumerate(planet_data):
        if i >= len(karaka_names):
            break
        ka = karaka_names[i]
        karakas.append({
            'planet': pd['planet'],
            'karaka': ka,
            'karaka_full': KARAKA_FULL_NAMES.get(ka, ka),
            'degree_in_sign': pd['deg_in_sign'],
            'sign': pd['sign'],
            'sign_idx': pd['sign_idx'],
            'lon': pd['lon'],
            'rank': i + 1,
        })

    return karakas


def get_karaka_planet(karakas, karaka_abbr):
    """Find which planet holds a specific karaka role.

    Args:
        karakas: result from calc_chara_karakas()
        karaka_abbr: 'AK', 'AmK', 'BK', etc.

    Returns:
        dict or None: The karaka-planet mapping
    """
    for k in karakas:
        if k['karaka'] == karaka_abbr:
            return k
    return None


def get_planet_karaka(karakas, planet_name):
    """Find which karaka role a specific planet holds.

    Args:
        karakas: result from calc_chara_karakas()
        planet_name: 'Su', 'Mo', etc.

    Returns:
        dict or None: The karaka-planet mapping
    """
    for k in karakas:
        if k['planet'] == planet_name:
            return k
    return None


def karakamsa(atmakaraka_lon, navamsa_lon=None):
    """Calculate the Karakamsa Lagna (AK's position in Navamsa).

    Karakamsa = the Navamsa sign where the Atmakaraka is placed.
    This is used for Karakamsa Rajayoga analysis.

    Args:
        atmakaraka_lon: Longitude of the Atmakaraka planet (tropical)
        navamsa_lon: If provided, the navamsa sign index (0-11). If None,
                     calculates from the longitude directly.

    Returns:
        int: Sign index (0-11) of Karakamsa Lagna
    """
    if navamsa_lon is not None:
        return navamsa_lon

    # Calculate Navamsa position from the AK's longitude
    # Navamsa = 1/9 of a sign = 3°20'
    deg_in_sign = atmakaraka_lon % 30
    navamsa_in_sign = int(deg_in_sign / (30.0 / 9))

    sign_idx = int(atmakaraka_lon // 30)

    # Navamsa mapping based on sign type
    if sign_idx in (0, 4, 8):  # Aries, Leo, Sagittarius
        # Movable signs: start from Aries
        karakamsa_sign = navamsa_in_sign
    elif sign_idx in (1, 5, 9):  # Taurus, Virgo, Capricorn
        # Fixed signs: start from Capricorn
        karakamsa_sign = (9 + navamsa_in_sign) % 12
    elif sign_idx in (2, 6, 10):  # Gemini, Libra, Aquarius
        # Dual signs: start from Libra
        karakamsa_sign = (6 + navamsa_in_sign) % 12
    else:  # Cancer, Scorpio, Pisces (3, 7, 11)
        # Water signs: start from Cancer
        karakamsa_sign = (3 + navamsa_in_sign) % 12

    return karakamsa_sign


def karaka_report(karakas):
    """Generate a formatted text report of karaka assignments.

    Args:
        karakas: result from calc_chara_karakas()

    Returns:
        str: Formatted report
    """
    lines = []
    lines.append("=" * 50)
    lines.append("CHARA KARAKA (Jaimini System, Tropical Zodiac)")
    lines.append("=" * 50)
    lines.append(f"{'Rank':<6}{'Karaka':<8}{'Full Name':<20}{'Planet':<10}{'Deg in Sign':<15}{'Sign'}")
    lines.append("-" * 50)

    for k in karakas:
        deg_str = f"{k['degree_in_sign']:.6f}°"
        lines.append(
            f"{k['rank']:<6}"
            f"{k['karaka']:<8}"
            f"{k['karaka_full']:<20}"
            f"{k['planet']:<10}"
            f"{deg_str:<15}"
            f"{k['sign']}"
        )

    lines.append("=" * 50)
    return "\n".join(lines)
