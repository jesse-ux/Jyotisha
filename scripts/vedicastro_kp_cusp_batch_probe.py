#!/usr/bin/env python3
"""Batch VedicAstro KP cusp raw/hash over public cases."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "references/open_source_sources/VedicAstro"
CASES = ROOT / "references/public_oracle_cases.json"


def stable(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def build(args: argparse.Namespace) -> dict[str, Any]:
    sys.path.insert(0, str(SRC))
    from vedicastro.VedicAstro import VedicHoroscopeData  # type: ignore

    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))["cases"]
    rows = []
    for case in cases[: args.limit]:
        b = case["birth"]
        try:
            v = VedicHoroscopeData(
                b["year"],
                b["month"],
                b["day"],
                b["hour"],
                b["minute"],
                b.get("second", 0),
                b["lat"],
                b["lon"],
                tz=None,
                ayanamsa=args.ayanamsa,
                house_system=args.house_system,
            )
            houses = [r._asdict() for r in v.get_houses_data_from_chart(v.generate_chart())]
            raw = {"case_id": case["id"], "name": case["name"], "sources": case.get("sources", []), "houses": houses}
            rows.append(
                {
                    "case_id": case["id"],
                    "name": case["name"],
                    "status": "complete",
                    "house_count": len(houses),
                    "raw_hash": hashlib.sha256(stable(raw).encode("utf-8")).hexdigest(),
                    "raw": raw,
                }
            )
        except Exception as exc:
            rows.append({"case_id": case["id"], "name": case["name"], "status": "blocked", "error": str(exc), "error_type": type(exc).__name__})
    return {
        "scope": "vedicastro_kp_cusp_batch_probe",
        "created_at": "2026-07-19",
        "status": "complete",
        "claim_status": "observation_only",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "dependency_identity": {
            "required_flatlib_source": "git+https://github.com/diliprk/flatlib.git@sidereal",
            "observed_pinned_flatlib_commit": "2618c348ce1ab2588548f935ff65f031630b4872",
        },
        "settings": {"ayanamsa": args.ayanamsa, "house_system": args.house_system, "timezone_policy": "timezonefinder_from_public_lat_lon"},
        "summary": {
            "case_count": len(rows),
            "complete_count": sum(1 for r in rows if r["status"] == "complete"),
            "blocked_count": sum(1 for r in rows if r["status"] != "complete"),
        },
        "cases": rows,
        "boundary": "Batch public-case KP cusp runtime raw. Observation-only; public worked-example expected values are still required for numeric oracle readiness.",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default=str(CASES))
    ap.add_argument("--limit", type=int, default=3)
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
