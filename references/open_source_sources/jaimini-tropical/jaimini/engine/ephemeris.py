"""High-precision planetary ephemeris using NASA JPL DE421 via Skyfield.

Provides tropical zodiac planetary positions with sub-arcsecond accuracy.
No ayanamsa applied - pure tropical (Sayana) positions.
"""

from skyfield.api import load, load_file
import os
import sys
import numpy as np
from .time_utils import zodiac_position, ZODIAC

# Planet constants
PLANETS = ['Su', 'Mo', 'Ma', 'Me', 'Ju', 'Ve', 'Sa', 'Ur', 'Ne', 'Pl']
SUN, MOON, MERCURY, VENUS, MARS, JUPITER, SATURN = range(7)
URANUS, NEPTUNE, PLUTO = range(7, 10)

# Skyfield timescale and ephemeris (lazy loaded)
_ts = None
_eph = None
_earth = None


def _get_ts():
    global _ts
    if _ts is None:
        _ts = load.timescale()
    return _ts


def _get_eph():
    """Load ephemeris data. Downloads DE421 on first use (~17MB)."""
    global _eph
    if _eph is None:
        # Search paths in order:
        # 1. Bundled with PyInstaller (sys._MEIPASS)
        # 2. Local project data directory
        # 3. Same directory as the executable
        # 4. Skyfield auto-download from NASA
        search_paths = []

        # PyInstaller bundle path
        if getattr(sys, 'frozen', False):
            bundle_path = os.path.join(sys._MEIPASS, 'jaimini', 'data', 'de421.bsp')
            search_paths.append(bundle_path)
            exe_dir = os.path.join(os.path.dirname(sys.executable), 'de421.bsp')
            search_paths.append(exe_dir)

        # Local development path
        local_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'de421.bsp')
        search_paths.append(os.path.normpath(local_path))

        found = False
        for path in search_paths:
            if os.path.exists(path):
                _eph = load_file(path)
                found = True
                break

        if not found:
            _eph = load('de421.bsp')

        global _earth
        _earth = _eph['earth']
    return _eph


def _planet_obj(name):
    """Get Skyfield planet object by short name."""
    eph = _get_eph()
    mapping = {
        'Su': eph['sun'],
        'Mo': eph['moon'],
        'Me': eph['mercury'],
        'Ve': eph['venus'],
        'Ma': eph['mars'],
        'Ju': eph['jupiter barycenter'],
        'Sa': eph['saturn barycenter'],
        'Ur': eph['uranus barycenter'],
        'Ne': eph['neptune barycenter'],
        'Pl': eph['pluto barycenter'],
    }
    return mapping[name]


def julian_day(year, month, day, hour=12.0, minute=0.0, second=0.0):
    """Calculate Julian Day from UTC date/time.

    Returns (jd_utc, tt_offset) where tt_offset is the difference
    between Terrestrial Time and UTC in seconds.
    """
    ts = _get_ts()
    dt_str = f"{year:04d}-{month:02d}-{day:02d}T{int(hour):02d}:{int(minute):02d}:{int(second):02d}"
    t = ts.utc(year, month, day, int(hour), int(minute), int(second))
    # Convert to Julian Day
    jd = t.tt  # Terrestrial Time Julian date (more accurate for astronomy)
    return jd


def get_planet_position(planet_name, year, month, day, hour=12.0, minute=0.0, second=0.0):
    """Get tropical longitude of a planet at given UTC time.

    Args:
        planet_name: Short name like 'Su', 'Mo', 'Me', etc.
        year, month, day: UTC date
        hour, minute, second: UTC time

    Returns:
        dict with keys: lon, lat, speed, zodiac, sign_idx, sign_deg, sign_str
    """
    ts = _get_ts()
    eph = _get_eph()
    earth = eph['earth']

    # Time object
    t = ts.utc(year, month, day, int(hour), int(minute), int(second))

    # Moon and Sun use earth observer, others use astrometric
    if planet_name == 'Mo':
        astro = earth.at(t).observe(eph['moon'])
    elif planet_name == 'Su':
        astro = earth.at(t).observe(eph['sun'])
    elif planet_name == 'Ra':
        # Rahu = Mean North Node
        astro = earth.at(t).observe(eph['moon'])
        # The node is calculated differently - we compute via the lunar orbit
        # Approximate mean node position
        return _mean_node_position(year, month, day, hour, minute, second, north=True)
    elif planet_name == 'Ke':
        return _mean_node_position(year, month, day, hour, minute, second, north=False)
    else:
        planet_obj = _planet_obj(planet_name)
        astro = earth.at(t).observe(planet_obj)

    # Apparent ecliptic position
    apparent = astro.apparent()
    lat, lon, distance = apparent.ecliptic_latlon('date')

    lon_deg = lon.degrees % 360
    lat_deg = lat.degrees

    # Calculate approximate daily speed (position 12 hours later)
    t2 = ts.utc(year, month, day, int(hour) + 12, int(minute), int(second))
    if planet_name == 'Mo':
        astro2 = earth.at(t2).observe(eph['moon'])
    elif planet_name == 'Su':
        astro2 = earth.at(t2).observe(eph['sun'])
    else:
        astro2 = earth.at(t2).observe(planet_obj)

    apparent2 = astro2.apparent()
    _, lon2, _ = apparent2.ecliptic_latlon('date')
    lon2_deg = lon2.degrees % 360

    # Daily speed
    diff = lon2_deg - lon_deg
    if diff > 180:
        diff -= 360
    elif diff < -180:
        diff += 360
    speed = diff * 2  # degrees per day (12h * 2)

    sign_idx, sign_deg, sign_str = zodiac_position(lon_deg)

    return {
        'lon': lon_deg,
        'lat': lat_deg,
        'speed': abs(speed),
        'retrograde': bool(speed < 0),
        'sign_idx': sign_idx,
        'sign': ZODIAC[sign_idx],
        'sign_deg': sign_deg,
        'sign_str': sign_str
    }


def _mean_node_position(year, month, day, hour=12.0, minute=0.0, second=0.0, north=True):
    """Calculate approximate mean lunar node position.

    Uses simplified formula accurate to ~0.1 degree.
    For high-precision, download the full JPL ephemeris.
    """
    # Mean node regression: ~19.35 degrees per year
    # Node position at J2000.0: ~125.0445 degrees (North Node)
    jd = julian_day(year, month, day, hour, minute, second)
    j2000 = 2451545.0
    days_since_j2000 = jd - j2000

    # Mean node regression rate: 19.341378 deg/year = 0.052954 deg/day
    # True regression rate is slightly variable but this gives ~0.1 deg accuracy
    node_mean = 125.0445 - 0.052954 * days_since_j2000
    node_mean = node_mean % 360

    lon_deg = node_mean if north else (node_mean + 180) % 360

    sign_idx, sign_deg, sign_str = zodiac_position(lon_deg)

    return {
        'lon': lon_deg,
        'lat': 0.0,
        'speed': 0.053,
        'retrograde': True,  # Nodes always retrograde
        'sign_idx': sign_idx,
        'sign': ZODIAC[sign_idx],
        'sign_deg': sign_deg,
        'sign_str': sign_str
    }


def get_all_planets(year, month, day, hour=12.0, minute=0.0, second=0.0):
    """Get tropical positions of all 9 planets + Rahu/Ketu at given UTC time.

    Returns:
        dict mapping planet short name to position dict
    """
    planets = {}
    for p in PLANETS:
        planets[p] = get_planet_position(p, year, month, day, hour, minute, second)
    planets['Ra'] = _mean_node_position(year, month, day, hour, minute, second, north=True)
    planets['Ke'] = _mean_node_position(year, month, day, hour, minute, second, north=False)
    return planets


def get_rahu_ketu(year, month, day, hour=12.0, minute=0.0, second=0.0):
    """Get Rahu (True North Node) and Ketu (True South Node) positions."""
    rahu = _mean_node_position(year, month, day, hour, minute, second, north=True)
    ketu = _mean_node_position(year, month, day, hour, minute, second, north=False)
    return rahu, ketu
