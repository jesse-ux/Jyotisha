from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_vimshottari_subperiod_timeline_expands_ad_to_pd() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/vimshottari_subperiod_timeline.py",
            "--year",
            "2000",
            "--month",
            "1",
            "--day",
            "1",
            "--hour",
            "12",
            "--minute",
            "0",
            "--lat",
            "0.0",
            "--lon",
            "0.0",
            "--tz",
            "0",
            "--years",
            "30",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    first_ad = report["timeline"][0]["antardasha"][0]
    assert len(first_ad["pratyantar"]) == 9
    assert first_ad["pratyantar"][0]["start"] == first_ad["start"]
    assert first_ad["pratyantar"][-1]["end"] == first_ad["end"]


def test_daily_transit_window_scan_runs_one_day_json() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/daily_transit_window_scan.py",
            "--start",
            "2027-03-01",
            "--end",
            "2027-03-01",
            "--planets",
            "Jupiter,Saturn",
            "--tz",
            "0",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["days"] == 1
    assert report["rows"][0]["date"] == "2027-03-01"
    planets = report["rows"][0]["transit"]["planets"]
    if isinstance(planets, dict):
        assert "Jupiter" in planets
    else:
        assert any(item.get("planet") == "Jupiter" for item in planets)
