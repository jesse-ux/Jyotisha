#!/usr/bin/env python3
"""Audit Vimshottari Dasha boundary drift against an external reference date.

This script is diagnostic. It does not tune or override the production Dasha
engine; it quantifies how much of a boundary difference can be explained by
birth-clock precision and year-length constants.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import datetime, timedelta
from typing import Any


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import jyotish_engine as engine  # noqa: E402


YEAR_LENGTHS = [365.0, 365.2422, 365.25, 365.25636, 360.0]
NAKSHATRA_SPAN = 360.0 / 27.0


def _birth_time_string(hour: int, minute: int, second: int = 0) -> str:
    if second:
        return f"{hour:02d}:{minute:02d}:{second:02d}"
    return f"{hour:02d}:{minute:02d}:00"


def _birth_datetime(args: argparse.Namespace, *, second: int | None = None) -> datetime:
    sec = args.second if second is None else second
    return datetime(args.year, args.month, args.day, args.hour, args.minute, sec)


def _engine_args(args: argparse.Namespace, *, second: int | None = None) -> argparse.Namespace:
    return argparse.Namespace(
        moon_lon=None,
        nakshatra=None,
        pada=None,
        birthdate=None,
        today=None,
        year=args.year,
        month=args.month,
        day=args.day,
        hour=args.hour,
        minute=args.minute,
        second=args.second if second is None else second,
        lat=args.lat,
        lon=args.lon,
        tz=args.tz,
        node_mode=args.node_mode,
    )


def _chart(args: argparse.Namespace, *, second: int | None = None) -> dict[str, Any]:
    chart, _asc_idx, _jd, _ayanamsa = engine._compute_chart_from_args(_engine_args(args, second=second))
    if chart is None:
        raise RuntimeError("Swiss Ephemeris is required for dasha reference audit")
    return chart


def _moon_context(args: argparse.Namespace, *, second: int | None = None) -> dict[str, Any]:
    chart = _chart(args, second=second)
    moon = chart.get("planets", {}).get("Moon", {})
    moon_lon = float(moon["degree_raw"])
    nak_index = int(moon_lon / NAKSHATRA_SPAN)
    progress = (moon_lon % NAKSHATRA_SPAN) / NAKSHATRA_SPAN
    nak_name, start_lord, start_years = engine.NAKSHATRA_LIST[nak_index % 27]
    return {
        "chart": chart,
        "moon_lon": moon_lon,
        "nakshatra_index": nak_index,
        "nakshatra": nak_name,
        "start_lord": start_lord,
        "start_years": start_years,
        "progress": progress,
        "elapsed_years": progress * start_years,
        "balance_years": start_years - progress * start_years,
    }


def _boundary_from_context(
    birth_dt: datetime,
    context: dict[str, Any],
    year_length: float,
) -> datetime:
    elapsed_years = float(context["elapsed_years"])
    return birth_dt - timedelta(days=elapsed_years * year_length)


def _boundary_snapshot(args: argparse.Namespace, *, second: int, year_length: float = 365.25) -> dict[str, Any]:
    ctx = _moon_context(args, second=second)
    birth_dt = _birth_datetime(args, second=second)
    start_dt = _boundary_from_context(birth_dt, ctx, year_length)
    return {
        "birth_time": _birth_time_string(args.hour, args.minute, second),
        "year_length": year_length,
        "moon_lon": round(ctx["moon_lon"], 8),
        "nakshatra": ctx["nakshatra"],
        "start_lord": ctx["start_lord"],
        "progress": round(ctx["progress"], 10),
        "elapsed_years": round(ctx["elapsed_years"], 8),
        "balance_years": round(ctx["balance_years"], 8),
        "start_datetime": start_dt.isoformat(timespec="seconds"),
    }


def _required_moon_delta_for_days(
    days_delta: float,
    start_years: float,
    year_length: float,
) -> float:
    """Return approximate Moon longitude delta in degrees for a boundary shift."""
    elapsed_year_delta = abs(days_delta) / year_length
    progress_delta = elapsed_year_delta / start_years if start_years else 0.0
    return progress_delta * NAKSHATRA_SPAN


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    production = engine.cmd_dasha(_engine_args(args))
    if "error" in production:
        raise RuntimeError(production["error"])
    first = production["timeline"][0]
    context = _moon_context(args)
    birth_dt = _birth_datetime(args)
    start_dt = datetime.fromisoformat(first["start_datetime"])
    target_dt = datetime.strptime(args.target_start_date, "%Y-%m-%d")
    date_delta_days = (start_dt.date() - target_dt.date()).days
    exact_delta_days = (start_dt - target_dt).total_seconds() / 86400.0
    required_moon_delta_deg = _required_moon_delta_for_days(
        exact_delta_days,
        float(context["start_years"]),
        365.25,
    )

    with_seconds = _boundary_snapshot(args, second=args.second)
    minute_only = _boundary_snapshot(args, second=0)
    with_seconds_dt = datetime.fromisoformat(with_seconds["start_datetime"])
    minute_only_dt = datetime.fromisoformat(minute_only["start_datetime"])
    clock_translation_seconds = args.second
    moon_recalculation_seconds = int((with_seconds_dt - minute_only_dt).total_seconds()) - clock_translation_seconds

    year_sensitivity = []
    for year_length in YEAR_LENGTHS:
        start = _boundary_from_context(birth_dt, context, year_length)
        year_sensitivity.append({
            "year_length": year_length,
            "start_datetime": start.isoformat(timespec="seconds"),
            "delta_days_vs_target_date": (start.date() - target_dt.date()).days,
        })

    min_delta = min(abs(row["delta_days_vs_target_date"]) for row in year_sensitivity)
    if min_delta > 0:
        finding = (
            "当前参考差异无法由秒级输入或年长常数单独解释；"
            "下一步应对比外部 oracle 的 Moon sidereal longitude、ayanamsa 与 Vimshottari 起算口径。"
        )
    else:
        finding = "当前参考差异可能由年长常数解释；需增加外部 oracle 样本确认。"

    return {
        "scope": "vimshottari_dasha_reference_boundary_audit",
        "case": {
            "date": f"{args.year:04d}-{args.month:02d}-{args.day:02d}",
            "birth_time": _birth_time_string(args.hour, args.minute, args.second),
            "lat": args.lat,
            "lon": args.lon,
            "tz": args.tz,
            "node_mode": args.node_mode,
        },
        "engine": {
            "moon_lon": round(context["moon_lon"], 8),
            "nakshatra": context["nakshatra"],
            "start_lord": context["start_lord"],
            "progress": round(context["progress"], 10),
            "elapsed_years": round(context["elapsed_years"], 8),
            "balance_years": round(context["balance_years"], 8),
            "start_datetime": first["start_datetime"],
            "end_datetime": first["end_datetime"],
            "start_date": first["start"],
            "end_date": first["end"],
        },
        "target_reference": {
            "source": args.target_source,
            "start_date": args.target_start_date,
            "date_delta_days": date_delta_days,
            "exact_delta_days": round(exact_delta_days, 6),
            "required_moon_delta_degrees": round(required_moon_delta_deg, 8),
            "required_moon_delta_arcmin_range": {
                "min": round(required_moon_delta_deg * 60 * 0.95, 6),
                "max": round(required_moon_delta_deg * 60 * 1.05, 6),
            },
        },
        "clock_precision_sensitivity": {
            "with_seconds": with_seconds,
            "minute_only": minute_only,
            "seconds_effect": {
                "start_delta_seconds": int((with_seconds_dt - minute_only_dt).total_seconds()),
                "clock_translation_seconds": clock_translation_seconds,
                "moon_recalculation_seconds": moon_recalculation_seconds,
                "moon_delta_degrees": round(with_seconds["moon_lon"] - minute_only["moon_lon"], 8),
                "note": (
                    "Changing birth seconds both translates the birth clock and recomputes Moon longitude; "
                    "near long Dasha lords this can shift the historical start boundary by more than seconds."
                ),
            },
        },
        "year_length_sensitivity": year_sensitivity,
        "finding": finding,
        "boundary": (
            "This is a calculation-boundary audit, not an event-prediction accuracy claim. "
            "Do not tune production Dasha constants to one PDF without a larger oracle set."
        ),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit Vimshottari Dasha reference drift")
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--month", type=int, required=True)
    parser.add_argument("--day", type=int, required=True)
    parser.add_argument("--hour", type=int, required=True)
    parser.add_argument("--minute", type=int, required=True)
    parser.add_argument("--second", type=int, default=0)
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("--tz", type=float, required=True)
    parser.add_argument("--node-mode", choices=["mean", "true"], default="mean")
    parser.add_argument("--target-start-date", required=True)
    parser.add_argument("--target-source", default="external_reference")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.second < 0 or args.second > 59:
        raise SystemExit("--second must be between 0 and 59")
    report = build_report(args)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
