"""House calculation for tropical zodiac.

Supports Whole Sign (default for Jaimini) and Placidus house systems.
Whole Sign: each house = entire zodiac sign, 1st house = sign containing Ascendant.
"""

import math
from .time_utils import ZODIAC, zodiac_position
from .ephemeris import julian_day

# House system codes
WHOLE_SIGN = 'W'
PLACIDUS = 'P'
EQUAL = 'E'

# Supported house systems
HOUSE_SYSTEMS = {
    'W': 'Whole Sign',
    'P': 'Placidus',
    'E': 'Equal House',
}


def calc_ascendant(year, month, day, hour, minute, second, lat, lon):
    """Calculate the tropical ascendant (Lagna) degree.

    Uses standard astronomical formula for oblique ascension.

    Returns:
        float: Ascendant degree (0-360) in tropical zodiac
    """
    jd = julian_day(year, month, day, hour, minute, second)

    # Calculate sidereal time
    ramc = _calculate_ramc(jd, lon)

    # Calculate obliquity of the ecliptic
    eps = _obliquity(jd)

    # Calculate ascendant using standard formula
    asc_rad = math.atan2(
        -math.sin(math.radians(ramc)) * math.cos(eps) -
        math.tan(math.radians(lat)) * math.sin(eps),
        math.cos(math.radians(ramc))
    )

    asc_deg = math.degrees(asc_rad) % 360

    return asc_deg


def calc_midheaven(year, month, day, hour, minute, second, lon):
    """Calculate the MC (Medium Coeli / 10th house cusp)."""
    jd = julian_day(year, month, day, hour, minute, second)
    ramc = _calculate_ramc(jd, lon)

    mc_rad = math.atan2(
        math.sin(math.radians(ramc)),
        math.cos(math.radians(ramc)) * math.cos(math.radians(_obliquity(jd)))
    )
    mc_deg = math.degrees(mc_rad) % 360
    return mc_deg


def calc_houses(year, month, day, hour, minute, second, lat, lon, system='W'):
    """Calculate all 12 house cusps.

    Args:
        year, month, day: UTC date
        hour, minute, second: UTC time
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees (East positive)
        system: 'W' = Whole Sign, 'P' = Placidus, 'E' = Equal House

    Returns:
        list of dicts: Each with 'cusp', 'sign', 'sign_idx', 'sign_deg', 'sign_str'
    """
    asc = calc_ascendant(year, month, day, hour, minute, second, lat, lon)

    if system == 'W':
        return _whole_sign_houses(asc)
    elif system == 'P':
        return _placidus_houses(year, month, day, hour, minute, second, lat, lon, asc)
    elif system == 'E':
        return _equal_houses(asc)
    else:
        raise ValueError(f"Unknown house system: {system}")


def _whole_sign_houses(asc):
    """Whole Sign houses: each house = one entire sign.

    1st house = the sign containing the Ascendant.
    House cusps are the 0° of each sign.
    """
    asc_sign = int(asc // 30)
    houses = []

    for h in range(12):
        sign_idx = (asc_sign + h) % 12
        cusp_deg = sign_idx * 30.0
        _, sign_deg, sign_str = zodiac_position(cusp_deg)
        houses.append({
            'house': h + 1,
            'cusp': cusp_deg,
            'sign_idx': sign_idx,
            'sign': ZODIAC[sign_idx],
            'sign_deg': 0.0,
            'sign_str': f"{ZODIAC[sign_idx]} 0°00'00.00\"",
            'type': 'Whole Sign',
        })

    return houses


def _equal_houses(asc):
    """Equal House system: each house cusp = asc + (house-1)*30."""
    houses = []
    for h in range(12):
        cusp_deg = (asc + h * 30) % 360
        sign_idx, sign_deg, sign_str = zodiac_position(cusp_deg)
        houses.append({
            'house': h + 1,
            'cusp': cusp_deg,
            'sign_idx': sign_idx,
            'sign': ZODIAC[sign_idx],
            'sign_deg': sign_deg,
            'sign_str': sign_str,
            'type': 'Equal',
        })
    return houses


def _placidus_houses(year, month, day, hour, minute, second, lat, lon, asc):
    """Placidus house system using semi-arc division.

    This is a simplified implementation using the standard oblique ascension method.
    """
    jd = julian_day(year, month, day, hour, minute, second)
    ramc = _calculate_ramc(jd, lon)
    eps = _obliquity(jd)

    houses = [None] * 12

    # 1st house = ASC
    houses[0] = {
        'house': 1, 'cusp': asc,
        'sign_idx': int(asc // 30), 'sign': ZODIAC[int(asc // 30)],
        'sign_deg': asc % 30,
        'sign_str': zodiac_position(asc)[2], 'type': 'Placidus'
    }

    # 10th house = MC
    mc = calc_midheaven(year, month, day, hour, minute, second, lon)
    houses[9] = {
        'house': 10, 'cusp': mc,
        'sign_idx': int(mc // 30), 'sign': ZODIAC[int(mc // 30)],
        'sign_deg': mc % 30,
        'sign_str': zodiac_position(mc)[2], 'type': 'Placidus'
    }

    # Intermediate houses using semi-arc
    pole = math.radians(lat)
    tan_pole = math.tan(pole)

    # For each intermediate cusp
    for house_num, offset in [(2, 30), (3, 60), (11, -30), (12, -60), (4, 120), (5, 150), (6, 180), (7, 210), (8, 240), (9, 300)]:
        ra = ramc + offset
        # Oblique ascension calculation
        x = math.sin(math.radians(ra)) * math.cos(eps) + tan_pole * math.sin(eps)
        y = math.cos(math.radians(ra))
        cusp_rad = math.atan2(x, y)
        cusp_deg = math.degrees(cusp_rad) % 360

        idx = house_num - 1
        if idx == 9:
            continue  # MC already set
        sign_idx, sign_deg, sign_str = zodiac_position(cusp_deg)
        houses[idx] = {
            'house': house_num, 'cusp': cusp_deg,
            'sign_idx': sign_idx, 'sign': ZODIAC[sign_idx],
            'sign_deg': sign_deg, 'sign_str': sign_str, 'type': 'Placidus'
        }

    return houses


def _calculate_ramc(jd, lon):
    """Calculate Right Ascension of Medium Coeli.

    Returns RAMC in degrees.
    """
    # Days since J2000.0
    d = jd - 2451545.0

    # GMST at 0h UTC
    gmst = 280.46061837 + 360.98564736629 * d
    gmst = gmst % 360

    # LMST = GMST + longitude
    lmst = gmst + lon

    # RAMC = LMST (in degrees, where 15° = 1 hour)
    ramc = (lmst * 15) % 360

    return ramc


def _obliquity(jd):
    """Calculate mean obliquity of the ecliptic.

    Uses IAU 2000 formula.
    """
    d = jd - 2451545.0  # Days since J2000.0
    T = d / 36525.0  # Julian centuries

    # Mean obliquity in arcseconds
    eps0 = 84381.448 - 46.84024 * T - 0.00059 * T**2 + 0.001813 * T**3

    # Convert to degrees
    return eps0 / 3600.0


def calc_sunrise(year, month, day, lat, lon):
    """Calculate sunrise time (UTC hours) for given date and location.

    Uses standard astronomical formula accurate to ~1 minute.
    Sunrise = moment when Sun's center is at the horizon (zenith 90.833° for atm. refraction).

    Returns:
        float: UTC hour of sunrise (e.g., 6.5 = 6:30 AM UTC)
    """
    import math
    jd = julian_day(year, month, day, 12, 0, 0)

    # Solar mean anomaly
    M = (357.5291 + 0.98560028 * (jd - 2451545.0)) % 360

    # Equation of center
    C = (1.9148 * math.sin(math.radians(M))
         + 0.0200 * math.sin(math.radians(2 * M))
         + 0.0003 * math.sin(math.radians(3 * M)))

    # Ecliptic longitude of Sun
    sun_lon = (M + C + 180.10248 + 0.000048 * (jd - 2451545.0) * 360) % 360

    # Obliquity
    eps = _obliquity(jd)

    # Declination of Sun
    dec = math.degrees(math.asin(
        math.sin(math.radians(sun_lon)) * math.sin(math.radians(eps))
    ))

    # Hour angle at sunrise (zenith = 90°50' for atmospheric refraction)
    lat_rad = math.radians(lat)
    dec_rad = math.radians(dec)
    cos_ha = (math.cos(math.radians(90.833))
              - math.sin(lat_rad) * math.sin(dec_rad)) / (math.cos(lat_rad) * math.cos(dec_rad))
    cos_ha = max(-1.0, min(1.0, cos_ha))
    ha = math.degrees(math.acos(cos_ha))

    # Solar noon (UTC hours)
    # Equation of time (approximate)
    B = math.radians(360.0 * (jd - 2451545.0 - 0.5) / 365.25)
    eq_time = 229.18 * (0.000075 + 0.001868 * math.cos(B)
                         - 0.032077 * math.sin(B)
                         - 0.014615 * math.cos(2 * B)
                         - 0.040849 * math.sin(2 * B))

    # Solar transit (noon) in UTC hours
    # 720 minutes = 12:00, adjusted by equation of time and longitude
    solar_noon = (720.0 - 4.0 * lon - eq_time) / 60.0

    # Sunrise = noon - hour angle
    sunrise_utc = solar_noon - ha / 15.0

    return sunrise_utc % 24.0  # Normalize to 0-24h


def calc_sunset(year, month, day, lat, lon):
    """Calculate sunset time (UTC hours)."""
    import math
    jd = julian_day(year, month, day, 12, 0, 0)
    M = (357.5291 + 0.98560028 * (jd - 2451545.0)) % 360
    C = (1.9148 * math.sin(math.radians(M))
         + 0.0200 * math.sin(math.radians(2 * M))
         + 0.0003 * math.sin(math.radians(3 * M)))
    sun_lon = (M + C + 180.10248 + 0.000048 * (jd - 2451545.0) * 360) % 360
    eps = _obliquity(jd)
    dec = math.degrees(math.asin(
        math.sin(math.radians(sun_lon)) * math.sin(math.radians(eps))
    ))
    lat_rad = math.radians(lat)
    dec_rad = math.radians(dec)
    cos_ha = (math.cos(math.radians(90.833))
              - math.sin(lat_rad) * math.sin(dec_rad)) / (math.cos(lat_rad) * math.cos(dec_rad))
    cos_ha = max(-1.0, min(1.0, cos_ha))
    ha = math.degrees(math.acos(cos_ha))
    B = math.radians(360.0 * (jd - 2451545.0 - 0.5) / 365.25)
    eq_time = 229.18 * (0.000075 + 0.001868 * math.cos(B)
                         - 0.032077 * math.sin(B)
                         - 0.014615 * math.cos(2 * B)
                         - 0.040849 * math.sin(2 * B))
    solar_noon = (720.0 - 4.0 * lon - eq_time) / 60.0
    sunset_utc = solar_noon + ha / 15.0
    return sunset_utc % 24.0


def get_house_for_longitude(lon, houses):
    """Find which house a given longitude falls in.

    In Whole Sign, this is straightforward: the sign determines the house.
    For other systems, finds the house range that contains the longitude.

    Returns:
        int: House number (1-12)
    """
    for h in houses:
        current_cusp = h['cusp']
        next_cusp = houses[(h['house']) % 12]['cusp']

        if next_cusp > current_cusp:
            if current_cusp <= lon < next_cusp:
                return h['house']
        else:
            # Wraps around 360°
            if lon >= current_cusp or lon < next_cusp:
                return h['house']

    return 1  # Fallback
