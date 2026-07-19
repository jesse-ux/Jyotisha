#!/usr/bin/env python3
"""Run VedicAstro KP house cusp star/sub/sub-sub raw probe.

Requires an isolated PYTHONPATH containing VedicAstro's required sidereal
flatlib fork. Output is observation-only until public numeric KP worked
examples are replayed.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "references/open_source_sources/VedicAstro"


def stable(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def build(args: argparse.Namespace) -> dict[str, Any]:
    sys.path.insert(0, str(SRC))
    from vedicastro.VedicAstro import VedicHoroscopeData  # type: ignore

    chart_input = {
        "year": args.year,
        "month": args.month,
        "day": args.day,
        "hour": args.hour,
        "minute": args.minute,
        "second": args.second,
        "latitude": args.latitude,
        "longitude": args.longitude,
        "timezone": args.timezone,
        "ayanamsa": args.ayanamsa,
        "house_system": args.house_system,
    }
    v = VedicHoroscopeData(
        args.year,
        args.month,
        args.day,
        args.hour,
        args.minute,
        args.second,
        args.latitude,
        args.longitude,
        tz=args.timezone,
        ayanamsa=args.ayanamsa,
        house_system=args.house_system,
    )
    houses = v.get_houses_data_from_chart(v.generate_chart())
    rows = [row._asdict() for row in houses]
    raw = {
        "request": chart_input,
        "houses": rows,
    }
    return {
        "scope": "vedicastro_kp_house_cusp_probe",
        "created_at": "2026-07-19",
        "status": "complete",
        "claim_status": "observation_only",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "engine": "VedicAstro",
        "dependency_identity": {
            "required_flatlib_source": "git+https://github.com/diliprk/flatlib.git@sidereal",
            "observed_pinned_flatlib_commit": "2618c348ce1ab2588548f935ff65f031630b4872",
            "flatlib": package_version("flatlib"),
            "polars": package_version("polars"),
            "timezonefinder": package_version("timezonefinder"),
        },
        "raw_hash": hashlib.sha256(stable(raw).encode("utf-8")).hexdigest(),
        "schema_fingerprint": {
            "house_count": len(rows),
            "fields": list(rows[0].keys()) if rows else [],
        },
        "raw": raw,
        "boundary": "KP house cusp star/sub/sub-sub raw from VedicAstro runtime. Observation-only until matched against a public numeric KP worked example.",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=1955)
    ap.add_argument("--month", type=int, default=2)
    ap.add_argument("--day", type=int, default=24)
    ap.add_argument("--hour", type=int, default=19)
    ap.add_argument("--minute", type=int, default=15)
    ap.add_argument("--second", type=int, default=0)
    ap.add_argument("--latitude", type=float, default=37.3382)
    ap.add_argument("--longitude", type=float, default=-122.0383)
    ap.add_argument("--timezone", default="America/Los_Angeles")
    ap.add_argument("--ayanamsa", default="Krishnamurti")
    ap.add_argument("--house-system", default="Placidus")
    ap.add_argument("--output")
    args = ap.parse_args()
    payload = build(args)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
