import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from benchmarks.jyotish.scripts.run_pyjhora_compare import write_report
from benchmarks.jyotish.scripts.run_pyjhora_compare import compare_one


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "benchmarks" / "jyotish" / "scripts" / "run_pyjhora_compare.py"


def test_pyjhora_compare_help_is_non_executing():
    result = subprocess.run(
        [sys.executable, str(RUNNER), "--help"], cwd=ROOT, capture_output=True, text=True, timeout=15
    )

    assert result.returncode == 0
    assert "--build-local" in result.stdout
    assert "--refresh-local" in result.stdout
    assert "--output-prefix" in result.stdout
    assert "FileNotFoundError" not in result.stderr


def test_pyjhora_report_uses_supplied_utc_generation_timestamp():
    report = write_report(
        [],
        [],
        generated_at=datetime(2026, 7, 15, 4, 30, tzinfo=timezone.utc),
    )

    assert "生成时间：2026-07-15T04:30:00+00:00" in report
    assert "生成时间：2026-06-03" not in report


def test_pyjhora_comparison_includes_d2_d4_bav_sav_and_shadbala_rows():
    bodies = ["Ascendant", "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    chart = {body: {"sign": "Aries", "degree_in_sign": 1.0} for body in bodies}
    planet = {body: {"sign": "Aries", "degree_in_sign": 1.0, "nakshatra": "Ashwini", "nakshatra_pada": 1} for body in bodies[1:]}
    local = {
        "ascendant": chart["Ascendant"], "planets": planet,
        "varga": {"D2": chart, "D4": chart, "D9": chart, "D10": chart},
        "dasha": {},
        "ashtakavarga": {"bav": {name: [1] * 12 for name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Lagna"]}, "sav": [7] * 12},
        "shadbala": {name: 100.0 for name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]},
    }
    pyjhora = {
        "ascendant": chart["Ascendant"], "planets": planet,
        "varga": {"D2": chart, "D4": chart, "D9": chart, "D10": chart},
        "dasha": {},
        "ashtakavarga": local["ashtakavarga"], "shadbala": local["shadbala"],
    }

    sections = {row["section"] for row in compare_one("fixture", local, pyjhora)}

    assert {"D2", "D4", "Ashtakavarga_BAV", "Ashtakavarga_SAV", "Shadbala"} <= sections
