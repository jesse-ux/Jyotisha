"""Jaimini Special Lagnas — Hora Lagna, Ghatika Lagna, Varnada Lagna.

Based on the Ghati system (60 Ghatis = 1 day, 1 Ghati = 24 minutes).
All calculations use LOCAL sunrise time as reference point.

Key time sensitivities (Jaimini Guide #1):
  - HL: ~1 hour per change (阴阳真禄)
  - GL: 24 minutes per change (五行真禄)
  - VL: ~1 hour per change (宫元, follows HL)

References:
  - Jaimini Sutramritam, Chapter I
  - dashaflow constants (sign lords, zodiac)
  - WeChat article: 阇弥尼指南(1)
"""

from ..engine.houses import calc_sunrise
from ..engine.time_utils import ZODIAC, ZODIAC_FULL

# Sign lords
SIGN_LORDS = {
    0: 'Ma', 1: 'Ve', 2: 'Me', 3: 'Mo', 4: 'Su',
    5: 'Me', 6: 'Ve', 7: 'Ma', 8: 'Ju', 9: 'Sa',
    10: 'Sa', 11: 'Ju'
}


def _elapsed_ghatis(sunrise_utc_hours, birth_utc_hours):
    """Calculate Ghatis elapsed from sunrise to birth.

    1 day = 60 Ghatis, 1 Ghati = 24 minutes.
    Birth can be after sunset (next day's sunrise not crossed).

    Returns:
        float: Ghatis elapsed (0-60 typically)
        bool: whether birth is before sunrise (night birth)
    """
    # Difference in hours
    diff_hours = birth_utc_hours - sunrise_utc_hours
    if diff_hours < 0:
        diff_hours += 24

    # Convert to Ghatis: 1 Ghati = 24 minutes = 0.4 hours
    ghatis = diff_hours / 0.4
    return ghatis, diff_hours < 0


def calc_hora_lagna(sunrise_utc_hours, birth_utc_hours):
    """Calculate Hora Lagna (阴阳真禄) — changes ~1 hour.

    Parivrittidwaya (Double Rotation) method:
    1. Calculate Ghatis elapsed from sunrise to birth
    2. For odd Hora Lagna signs: from Aries, forward 1 sign per Ghati
    3. For even Hora Lagna signs: from Scorpio, backward 1 sign per Ghati
    4. The sign is determined by whether the Ghati count is odd/even

    Actually, the standard method:
    - HL sign = floor(elapsed_ghatis) % 12 + 1 (in sign indices)

    Returns:
        dict with sign_idx, sign, longitude (sign start degree)
    """
    ghatis, night = _elapsed_ghatis(sunrise_utc_hours, birth_utc_hours)
    ghatis_rounded = int(ghatis)  # floor to whole Ghatis

    # Determine HL sign based on whether the Ghati count is odd/even
    # If odd number of Ghatis: use forward from Aries
    # If even: use reverse from Scorpio
    if ghatis_rounded % 2 == 1:
        # Odd: forward from Aries (sign 0)
        hl_sign = ghatis_rounded % 12
    else:
        # Even: reverse from Scorpio (sign 7)
        # Backward = subtract and mod
        hl_sign = (7 - ghatis_rounded) % 12

    # Sub-portion within the sign (Savayava method)
    # Each Ghati = 30 degrees in the HL system
    # Remaining fractional Ghatis determine sub-sign position
    frac = ghatis - ghatis_rounded
    hl_degree = frac * 30.0  # degree within the HL sign

    return {
        'name': 'HL',
        'full_name': 'Hora Lagna (阴阳真禄)',
        'sign_idx': hl_sign,
        'sign': ZODIAC[hl_sign],
        'sign_full': ZODIAC_FULL[hl_sign],
        'lord': SIGN_LORDS[hl_sign],
        'degree_in_sign': hl_degree,
        'longitude': hl_sign * 30.0 + hl_degree,
        'ghatis_elapsed': ghatis,
        'night_birth': night,
    }


def calc_ghatika_lagna(sunrise_utc_hours, birth_utc_hours):
    """Calculate Ghatika Lagna (五行真禄) — changes every 24 minutes (1 Ghati).

    Formula: GL = floor(elapsed_ghatis) % 12 + 1 (as sign index 0-11)

    Returns:
        dict with sign_idx, sign, longitude
    """
    ghatis, night = _elapsed_ghatis(sunrise_utc_hours, birth_utc_hours)
    ghatis_rounded = int(ghatis)

    gl_sign = ghatis_rounded % 12

    # Fractional Ghati gives degree within sign
    frac = ghatis - ghatis_rounded
    gl_degree = frac * 30.0

    return {
        'name': 'GL',
        'full_name': 'Ghatika Lagna (五行真禄)',
        'sign_idx': gl_sign,
        'sign': ZODIAC[gl_sign],
        'sign_full': ZODIAC_FULL[gl_sign],
        'lord': SIGN_LORDS[gl_sign],
        'degree_in_sign': gl_degree,
        'longitude': gl_sign * 30.0 + gl_degree,
        'ghatis_elapsed': ghatis,
    }


def calc_varnada_lagna(asc_sign_idx, hl_sign_idx=None,
                       sunrise_utc_hours=None, birth_utc_hours=None):
    """Calculate Varnada Lagna (宫元).

    Two methods exist:
    1. From Ascendant: VL = (Asc sign * k) % 12 where k depends on tradition
    2. From HL: VL = (HL sign * 3) % 12, then applied

    The most common Jaimini formula: VL_sign = (asc_sign_no * 3) % 12
    where asc_sign_no is 1-12.

    Some traditions multiply by 3, 5, or other factors depending on
    whether ascendant is odd/even.

    Returns:
        dict with sign_idx, sign
    """
    # Method 1: from Ascendant × 3 (standard Jaimini)
    vl_sign = (asc_sign_idx * 3) % 12

    result = {
        'name': 'VL',
        'full_name': 'Varnada Lagna (宫元)',
        'sign_idx': vl_sign,
        'sign': ZODIAC[vl_sign],
        'sign_full': ZODIAC_FULL[vl_sign],
        'lord': SIGN_LORDS[vl_sign],
        'method': 'Asc × 3',
    }

    # Method 2: from HL (if provided)
    if hl_sign_idx is not None:
        vl_from_hl = (hl_sign_idx * 3) % 12
        result['vl_from_hl'] = {
            'sign_idx': vl_from_hl,
            'sign': ZODIAC[vl_from_hl],
            'lord': SIGN_LORDS[vl_from_hl],
        }

    return result


def calc_all_special_lagnas(year, month, day, hour, minute, second,
                            lat, lon, asc_sign_idx, tz_offset=0.0):
    """Calculate all Jaimini special lagnas.

    Args:
        year, month, day: Local date
        hour, minute, second: Local time
        lat, lon: Location
        asc_sign_idx: Ascendant sign index (0-11)
        tz_offset: Timezone offset from UTC in hours

    Returns:
        dict with HL, GL, VL
    """
    # Convert local time to UTC hours
    from ..engine.time_utils import local_to_utc
    utc_dt = local_to_utc(year, month, day, hour, minute, second, tz_offset)

    utc_hours = (utc_dt.hour + utc_dt.minute / 60.0
                 + (utc_dt.second + utc_dt.microsecond / 1_000_000) / 3600.0)

    # Calculate sunrise
    sunrise_utc = calc_sunrise(
        utc_dt.year, utc_dt.month, utc_dt.day, lat, lon
    )

    hl = calc_hora_lagna(sunrise_utc, utc_hours)
    gl = calc_ghatika_lagna(sunrise_utc, utc_hours)
    vl = calc_varnada_lagna(asc_sign_idx, hl['sign_idx'])

    return {
        'HL': hl,
        'GL': gl,
        'VL': vl,
        'sunrise_utc_hours': sunrise_utc,
        'birth_utc_hours': utc_hours,
    }


def lagna_report(special_lagnas):
    """Generate a formatted text report of special lagnas."""
    lines = []
    lines.append("=" * 60)
    lines.append("SPECIAL LAGNAS (Jaimini System — Tropical)")
    lines.append("=" * 60)

    sl = special_lagnas
    lines.append(f"Sunrise (UTC hours): {sl['sunrise_utc_hours']:.4f}h")
    lines.append(f"Birth (UTC hours):   {sl['birth_utc_hours']:.4f}h")
    lines.append("")

    for key in ['HL', 'GL', 'VL']:
        if key in sl:
            info = sl[key]
            deg_str = f"{info['degree_in_sign']:.4f}°" if 'degree_in_sign' in info else ''
            lines.append(
                f"  {info['name']:<4} {info['full_name']:<30}"
                f"→ {info['sign']:<6} {deg_str:<12}"
                f"(lord: {info['lord']})"
            )

    lines.append("=" * 60)
    return "\n".join(lines)
