#!/usr/bin/env python3
"""Extract jyotishganit Shadbala object surface raw/hash."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "references/open_source_sources/jyotishganit"


def clean(v: Any) -> Any:
    if isinstance(v, dict):
        return {k: clean(val) for k, val in v.items()}
    if isinstance(v, list):
        return [clean(x) for x in v]
    if hasattr(v, "item"):
        try:
            return v.item()
        except Exception:
            pass
    return v


def stable(data: Any) -> str:
    return json.dumps(clean(data), ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def build(args: argparse.Namespace) -> dict[str, Any]:
    sys.path.insert(0, str(SRC))
    from jyotishganit.main import calculate_birth_chart  # type: ignore

    chart = calculate_birth_chart(
        datetime.fromisoformat(args.datetime),
        args.latitude,
        args.longitude,
        args.timezone,
        args.location,
        args.name,
    )
    rows = {
        p.celestial_body: clean(p.shadbala)
        for p in chart.d1_chart.planets
        if p.shadbala
    }
    required = ["Sthanabala", "Digbala", "Kaalabala", "Cheshtabala", "Naisargikabala", "Drikbala", "Shadbala"]
    coverage = {
        body: {key: key in values for key in required}
        for body, values in rows.items()
    }
    raw = {"request": vars(args), "shadbala": rows}
    return {
        "scope": "jyotishganit_shadbala_surface_probe",
        "created_at": "2026-07-19",
        "status": "complete" if rows else "missing",
        "claim_status": "observation_only",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "source_path": "references/open_source_sources/jyotishganit/jyotishganit/components/strengths.py",
        "api_surface": {
            "calculate_all_strengths": True,
            "compute_shadbala": True,
            "six_strengths": required[:6],
        },
        "coverage": coverage,
        "raw_hash": hashlib.sha256(stable(raw).encode("utf-8")).hexdigest(),
        "raw": raw,
        "boundary": "jyotishganit exposes Shadbala via object surface, not top-level to_dict. Observation-only until component units and external worked examples are compared.",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--datetime", default="1955-02-24T19:15:00")
    ap.add_argument("--latitude", type=float, default=37.3382)
    ap.add_argument("--longitude", type=float, default=-122.0383)
    ap.add_argument("--timezone", type=float, default=-8.0)
    ap.add_argument("--location", default="San Francisco, CA")
    ap.add_argument("--name", default="Steve Jobs public")
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
