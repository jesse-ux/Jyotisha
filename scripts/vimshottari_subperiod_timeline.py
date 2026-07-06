#!/usr/bin/env python3
"""Expand Vimshottari MD/AD into PD or PrAD timeline from engine AD boundaries."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DASHA_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_YEARS = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7, "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}


def _parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d")


def _fmt(value: datetime) -> str:
    return value.strftime("%Y-%m-%d")


def _ordered_lords(start_lord: str) -> list[str]:
    index = DASHA_ORDER.index(start_lord)
    return DASHA_ORDER[index:] + DASHA_ORDER[:index]


def _split_period(start: str, end: str, start_lord: str) -> list[dict[str, Any]]:
    start_dt = _parse_date(start)
    end_dt = _parse_date(end)
    total_seconds = (end_dt - start_dt).total_seconds()
    cursor = start_dt
    periods: list[dict[str, Any]] = []
    for lord in _ordered_lords(start_lord):
        seconds = total_seconds * DASHA_YEARS[lord] / 120
        next_cursor = cursor + timedelta(seconds=seconds)
        periods.append({"lord": lord, "start": _fmt(cursor), "end": _fmt(next_cursor)})
        cursor = next_cursor
    periods[-1]["end"] = end
    return periods


def _run_dasha(args: argparse.Namespace) -> dict[str, Any]:
    command = [
        sys.executable,
        "scripts/jyotish_engine.py",
        "dasha",
        "--year",
        str(args.year),
        "--month",
        str(args.month),
        "--day",
        str(args.day),
        "--hour",
        str(args.hour),
        "--minute",
        str(args.minute),
        "--second",
        str(args.second),
        "--lat",
        str(args.lat),
        "--lon",
        str(args.lon),
        "--tz",
        str(args.tz),
        "--years",
        str(args.years),
    ]
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=120, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.stderr or completed.stdout)
    return json.loads(completed.stdout)


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    dasha = _run_dasha(args)
    md_reports = []
    for md in dasha["timeline"]:
        ad_reports = []
        for ad in md.get("antardasha_timeline", []):
            pd = _split_period(ad["start"], ad["end"], ad["lord"])
            item: dict[str, Any] = {"lord": ad["lord"], "start": ad["start"], "end": ad["end"], "pratyantar": pd}
            if args.depth == "prad":
                for period in item["pratyantar"]:
                    period["sookshma"] = _split_period(period["start"], period["end"], period["lord"])
            ad_reports.append(item)
        md_reports.append({"lord": md["lord"], "start": md["start"], "end": md["end"], "antardasha": ad_reports})
    return {
        "scope": "vimshottari_subperiod_timeline",
        "method": "standard proportional subdivision from jyotish_engine dasha AD boundaries",
        "depth": args.depth,
        "timeline": md_reports,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--month", type=int, required=True)
    parser.add_argument("--day", type=int, required=True)
    parser.add_argument("--hour", type=int, required=True)
    parser.add_argument("--minute", type=int, required=True)
    parser.add_argument("--second", type=int, default=0)
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("--tz", type=float, default=0)
    parser.add_argument("--years", type=int, default=45)
    parser.add_argument("--depth", choices=["pd", "prad"], default="pd")
    args = parser.parse_args()
    print(json.dumps(build_report(args), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
