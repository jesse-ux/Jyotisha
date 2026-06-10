"""
Jyotish Vedic Astrology — Comprehensive calculation engine

A Python package for Vedic (Jyotish) astrology calculations:
- D1-D60 divisional charts (Varga)
- Vimshottari Dasha (planetary periods)
- Shadbala (six-fold planetary strength)
- Ashtakavarga (eight-fold bindus)
- Yoga detection (planetary combinations)
- Nakshatra analysis
- Transit calculations
- Full-reading synthesis

License: MIT
"""

import sys
import os

# Add scripts dir to path so all engine modules are importable
_pkg_dir = os.path.dirname(os.path.abspath(__file__))
_repo_root = os.path.dirname(_pkg_dir)
_scripts_dir = os.path.join(_repo_root, "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

__version__ = "6.1.10"
__all__ = [
    "calculate_chart",
    "calculate_dasha",
    "calculate_shadbala",
    "calculate_ashtakavarga",
    "calculate_varga",
    "calculate_yogas",
    "full_reading",
]

# Lazy imports — only load when called
def _import_engine():
    """Import jyotish_engine module (lazy to avoid heavy init)."""
    import jyotish_engine
    return jyotish_engine


def calculate_chart(year, month, day, hour, minute, lat, lon, tz, node_mode="mean"):
    """Calculate D1 Rashi chart."""
    import json
    import subprocess
    engine = os.path.join(_scripts_dir, "jyotish_engine.py")
    cmd = [
        sys.executable, engine, "chart",
        "--year", str(year), "--month", str(month), "--day", str(day),
        "--hour", str(hour), "--minute", str(minute),
        "--lat", str(lat), "--lon", str(lon), "--tz", str(tz),
        "--node-mode", node_mode,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return json.loads(result.stdout) if result.returncode == 0 else {"error": result.stderr}


def calculate_dasha(year, month, day, hour, minute, lat, lon, tz, years=10, node_mode="mean"):
    """Calculate Vimshottari Dasha timeline."""
    import json
    import subprocess
    engine = os.path.join(_scripts_dir, "jyotish_engine.py")
    cmd = [
        sys.executable, engine, "dasha",
        "--year", str(year), "--month", str(month), "--day", str(day),
        "--hour", str(hour), "--minute", str(minute),
        "--lat", str(lat), "--lon", str(lon), "--tz", str(tz),
        "--years", str(years), "--node-mode", node_mode,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return json.loads(result.stdout) if result.returncode == 0 else {"error": result.stderr}


def calculate_shadbala(year, month, day, hour, minute, lat, lon, tz, node_mode="mean"):
    """Calculate Shadbala (six-fold strength)."""
    import json
    import subprocess
    engine = os.path.join(_scripts_dir, "jyotish_engine.py")
    cmd = [
        sys.executable, engine, "shadbala",
        "--year", str(year), "--month", str(month), "--day", str(day),
        "--hour", str(hour), "--minute", str(minute),
        "--lat", str(lat), "--lon", str(lon), "--tz", str(tz),
        "--node-mode", node_mode,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return json.loads(result.stdout) if result.returncode == 0 else {"error": result.stderr}


def calculate_ashtakavarga(year, month, day, hour, minute, lat, lon, tz, node_mode="mean"):
    """Calculate Ashtakavarga matrix."""
    import json
    import subprocess
    engine = os.path.join(_scripts_dir, "jyotish_engine.py")
    cmd = [
        sys.executable, engine, "ashtakavarga",
        "--year", str(year), "--month", str(month), "--day", str(day),
        "--hour", str(hour), "--minute", str(minute),
        "--lat", str(lat), "--lon", str(lon), "--tz", str(tz),
        "--node-mode", node_mode,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return json.loads(result.stdout) if result.returncode == 0 else {"error": result.stderr}


def calculate_varga(year, month, day, hour, minute, lat, lon, tz, varga="D9", node_mode="mean"):
    """Calculate a specific Varga (D9, D10, etc.)."""
    import json
    import subprocess
    engine = os.path.join(_scripts_dir, "jyotish_engine.py")
    cmd = [
        sys.executable, engine, "varga",
        "--year", str(year), "--month", str(month), "--day", str(day),
        "--hour", str(hour), "--minute", str(minute),
        "--lat", str(lat), "--lon", str(lon), "--tz", str(tz),
        "--varga", varga, "--node-mode", node_mode,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return json.loads(result.stdout) if result.returncode == 0 else {"error": result.stderr}


def calculate_yogas(year, month, day, hour, minute, lat, lon, tz, node_mode="mean"):
    """Detect Yogas in the birth chart."""
    import json
    import subprocess
    engine = os.path.join(_scripts_dir, "jyotish_engine.py")
    cmd = [
        sys.executable, engine, "yoga",
        "--year", str(year), "--month", str(month), "--day", str(day),
        "--hour", str(hour), "--minute", str(minute),
        "--lat", str(lat), "--lon", str(lon), "--tz", str(tz),
        "--node-mode", node_mode,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return json.loads(result.stdout) if result.returncode == 0 else {"error": result.stderr}


def full_reading(year, month, day, hour, minute, lat, lon, tz, age, transit_date, node_mode="mean"):
    """Run the complete full-reading pipeline."""
    import json
    import subprocess
    engine = os.path.join(_scripts_dir, "jyotish_engine.py")
    cmd = [
        sys.executable, engine, "full-reading",
        "--year", str(year), "--month", str(month), "--day", str(day),
        "--hour", str(hour), "--minute", str(minute),
        "--lat", str(lat), "--lon", str(lon), "--tz", str(tz),
        "--age", str(age), "--transit-date", transit_date,
        "--node-mode", node_mode,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    return json.loads(result.stdout) if result.returncode == 0 else {"error": result.stderr}
