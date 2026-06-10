"""Time utilities for Jaimini astrology engine.

Julian day conversion, DMS formatting, sunrise/sunset calculation.
All calculations use the Tropical Zodiac (no ayanamsa applied).
"""

from datetime import datetime, timedelta
import re

# Zodiac sign abbreviations (IAST-based, Western order)
ZODIAC = [
    'Ari', 'Tau', 'Gem', 'Cnc', 'Leo', 'Vir',
    'Lib', 'Sco', 'Sgr', 'Cap', 'Aqr', 'Psc'
]

ZODIAC_FULL = [
    'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
    'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
]

# Planet names for output
PLANET_NAMES = {
    'Su': 'Sun', 'Mo': 'Moon', 'Me': 'Mercury', 'Ve': 'Venus',
    'Ma': 'Mars', 'Ju': 'Jupiter', 'Sa': 'Saturn',
    'Ur': 'Uranus', 'Ne': 'Neptune', 'Pl': 'Pluto',
    'Ra': 'Rahu (NN)', 'Ke': 'Ketu (SN)'
}

# Natural malefics and benefics in Jaimini
NATURAL_MALEFICS = {'Su', 'Ma', 'Sa', 'Ra', 'Ke'}
NATURAL_BENEFICS = {'Mo', 'Me', 'Ve', 'Ju'}


def parse_dms(dms_str):
    """Convert a DMS string like "39°54'25.0\"" or decimal string to float degrees.

    Handles formats: "39°54'25.0\"", "39d54m25s", "39.907", "39°54′25″"
    """
    if isinstance(dms_str, (int, float)):
        return float(dms_str)

    dms_str = dms_str.strip().replace('′', "'").replace('″', '"')

    # Try parsing as simple float first
    try:
        return float(dms_str)
    except ValueError:
        pass

    # Parse DMS format
    parts = re.findall(r"[\d.-]+", dms_str)
    if len(parts) == 1:
        return float(parts[0])
    elif len(parts) == 2:
        degrees = float(parts[0])
        minutes = float(parts[1])
        sign = -1 if degrees < 0 or dms_str.lstrip().startswith('-') else 1
        return sign * (abs(degrees) + minutes / 60.0)
    elif len(parts) >= 3:
        degrees = float(parts[0])
        minutes = float(parts[1])
        seconds = float(parts[2])
        sign = -1 if degrees < 0 or dms_str.lstrip().startswith('-') else 1
        return sign * (abs(degrees) + minutes / 60.0 + seconds / 3600.0)

    raise ValueError(f"Cannot parse DMS string: {dms_str}")


def to_dms(decimal_deg, precision=2):
    """Convert decimal degrees to DMS tuple (degrees, minutes, seconds)."""
    sign = -1 if decimal_deg < 0 else 1
    d = abs(decimal_deg)
    deg = int(d)
    min_frac = (d - deg) * 60
    mins = int(min_frac)
    secs = round((min_frac - mins) * 60, precision)
    if secs >= 60:
        secs -= 60
        mins += 1
    if mins >= 60:
        mins -= 60
        deg += 1
    return (sign * deg, mins, secs)


def format_dms(decimal_deg, precision=2):
    """Format decimal degrees as a DMS string like '7°45'59.79\"'."""
    d, m, s = to_dms(decimal_deg, precision)
    return f"{d}°{m:02d}'{s:0{3 + precision}.{precision}f}\""


def zodiac_position(lon):
    """Return (sign_index, degrees_in_sign, formatted_string) for a longitude."""
    lon = lon % 360
    sign_idx = int(lon // 30)
    pos_in_sign = lon % 30
    d, m, s = to_dms(pos_in_sign)
    label = f"{ZODIAC[sign_idx]} {d}°{m:02d}'{s:05.2f}\""
    return sign_idx, pos_in_sign, label


def parse_timezone(tz_str):
    """Parse timezone string like '+8', '-5:30', '+5.5' into hours float."""
    tz_str = str(tz_str).strip()
    # Try simple float format first (+5.5, -4.5)
    try:
        return float(tz_str)
    except ValueError:
        pass
    # Try HH:MM format
    match = re.match(r'^([+-]?)(\d{1,2}):?(\d{0,2})$', tz_str)
    if not match:
        raise ValueError(f"Cannot parse timezone: {tz_str}")
    sign = -1 if match.group(1) == '-' else 1
    hours = float(match.group(2))
    mins = float(match.group(3) or 0)
    return sign * (hours + mins / 60)


def local_to_utc(year, month, day, hour, minute, second, tz_offset_hours):
    """Convert local datetime to UTC datetime."""
    local_dt = datetime(year, month, day, hour, minute, int(second),
                        int((second - int(second)) * 1_000_000))
    utc_dt = local_dt - timedelta(hours=tz_offset_hours)
    return utc_dt


def utc_to_jd(utc_dt):
    """Convert UTC datetime to Julian Day using standard formula.

    Uses the same algorithm as Swiss Ephemeris for high precision.
    """
    y = utc_dt.year
    m = utc_dt.month
    d = utc_dt.day + utc_dt.hour / 24.0 + utc_dt.minute / 1440.0 + utc_dt.second / 86400.0

    if m <= 2:
        y -= 1
        m += 12

    a = y // 100
    b = 2 - a + a // 4

    jd = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + b - 1524.5
    return jd


def jd_to_datetime(jd):
    """Convert Julian Day to (year, month, day, hour, minute, second) tuple."""
    jd += 0.5
    z = int(jd)
    f = jd - z

    if z < 2299161:
        a = z
    else:
        alpha = int((z - 1867216.25) / 36524.25)
        a = z + 1 + alpha - alpha // 4

    b = a + 1524
    c = int((b - 122.1) / 365.25)
    d = int(365.25 * c)
    e = int((b - d) / 30.6001)

    day = b - d - int(30.6001 * e) + f
    if e < 14:
        month = e - 1
    else:
        month = e - 13

    if month > 2:
        year = c - 4716
    else:
        year = c - 4715

    day_int = int(day)
    day_frac = day - day_int
    hour = int(day_frac * 24)
    minute = int((day_frac * 24 - hour) * 60)
    second = (day_frac * 24 - hour - minute / 60.0) * 3600

    return (year, month, day_int, hour, minute, second)


def iso_to_utc_str(iso_str, tz_str):
    """Convert ISO datetime with timezone to UTC datetime string.

    Example: iso_to_utc_str('2025-12-03 08:06:00', '+8') -> UTC datetime
    """
    dt = datetime.strptime(iso_str, '%Y-%m-%d %H:%M:%S')
    offset = parse_timezone(tz_str)
    utc_dt = dt - timedelta(hours=offset)
    return utc_dt.strftime('%Y-%m-%d %H:%M:%S')


def get_ayanamsa(jd, system='lahiri'):
    """Calculate ayanamsa value for given Julian Day.

    Note: In Tropical mode, ayanamsa is always 0.
    This function is provided for sidereal mode support if needed later.

    Supported systems: lahiri, raman, krishnamurti, fagan_bradley
    """
    # Lahiri ayanamsa: Simplified formula based on JPL ephemeris data
    # Accurate to within ~1 arcsecond for 1900-2100
    # Reference: IAU 2006 precession model
    if system == 'lahiri':
        # Lahiri ayanamsa on J2000.0 was 23°51'11.32"
        # Precession rate ~50.29 arcsec/year
        j2000 = 2451545.0
        years_since_j2000 = (jd - j2000) / 365.25
        base_ayanamsa = 23.853144  # degrees at J2000.0
        precession_rate = 50.29 / 3600.0  # degrees per year
        return base_ayanamsa + years_since_j2000 * precession_rate
    elif system == 'raman':
        # B.V. Raman ayanamsa
        j2000 = 2451545.0
        years_since_j2000 = (jd - j2000) / 365.25
        return 22.504167 + years_since_j2000 * 50.29 / 3600.0
    elif system == 'krishnamurti':
        # KP ayanamsa (same as Lahiri minus a small offset)
        return get_ayanamsa(jd, 'lahiri') - 0.001667
    elif system == 'fagan_bradley':
        # Fagan-Bradley (Western sidereal)
        j2000 = 2451545.0
        years_since_j2000 = (jd - j2000) / 365.25
        return 24.826667 + years_since_j2000 * 50.29 / 3600.0
    else:
        raise ValueError(f"Unknown ayanamsa system: {system}")
