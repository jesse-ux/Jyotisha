#!/usr/bin/env python3
"""Triage public worked-example sources before numeric oracle capture."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "references/oracle/public_worked_example_source_triage_2026_07_20.json"


def obs_hash(row: dict[str, Any]) -> str:
    payload = json.dumps({k: row[k] for k in sorted(row) if k != "observation_hash"}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def source(**row: Any) -> dict[str, Any]:
    base = {
        "numeric_fields_present": False,
        "upgrade_status": "candidate_not_oracle",
        "missing_for_oracle": [],
        "claim_boundary": "Source triage only; do not upgrade until raw page capture, exact settings, expected numeric values, hash, and replay comparison are archived.",
    }
    base.update(row)
    base["observation_hash"] = obs_hash(base)
    return base


def build(date: str) -> dict[str, Any]:
    rows = [
        source(
            source_id="mypanchang_edison_2025_panchangam",
            domain="muhurta_factor_scoring",
            topic="Tarabala/Chandrabala/Panchangam daily factors",
            url="https://www.mypanchang.com/phppanchang.php?cityhead=&cityname=Edison-NJ&mn=04&monthtype=1&yr=2025",
            source_role="numeric_candidate",
            numeric_fields_present=True,
            observed_numeric_fields=["tarabalam periods", "chandrabalam periods", "nakshatra", "rasi", "tithi", "yoga", "karana"],
            missing_for_oracle=["raw_capture_hash", "exact_date_selection", "timezone", "sunrise", "formula_weight_contract"],
        ),
        source(
            source_id="drikpanchang_mumbai_rahu_2026_07_20",
            domain="muhurta_factor_scoring",
            topic="Rahu Kalam daily interval",
            url="https://www.drikpanchang.com/muhurat/rahu-kalam.html?date=20/07/2026&geoname-id=1275339",
            source_role="numeric_candidate",
            numeric_fields_present=True,
            observed_numeric_fields=["rahu kalam interval", "weekday", "city/date scoped daily table"],
            missing_for_oracle=["raw_capture_hash", "sunrise", "sunset", "timezone", "calculation_rule_replay"],
        ),
        source(
            source_id="mypanchang_tarabalam_chakra",
            domain="muhurta_factor_scoring",
            topic="Tarabalam/Chandrabalam formula reference",
            url="https://www.mypanchang.com/tarabalam.php",
            source_role="formula_reference",
            numeric_fields_present=False,
            observed_numeric_fields=[],
            missing_for_oracle=["birth_moon_nakshatra", "current_moon_nakshatra", "worked_numeric_example", "raw_capture_hash"],
        ),
        source(
            source_id="astrosage_kp_cuspal_sub_lord",
            domain="kp_precision_timing",
            topic="KP cuspal sub lord calculator/reference",
            url="https://www.astrosage.com/kp/cuspal-sub-lord.asp",
            source_role="runtime_or_reference_candidate",
            numeric_fields_present=False,
            observed_numeric_fields=[],
            missing_for_oracle=["public_birth_or_query_input", "cusp_longitude", "star_lord", "sub_lord", "sub_sub_lord", "raw_capture_hash"],
        ),
        source(
            source_id="astrojyoti_shadbala_formula",
            domain="shadbala_component_closure",
            topic="Shadbala formula reference",
            url="https://www.astrojyoti.com/shadbala.htm",
            source_role="formula_reference",
            numeric_fields_present=False,
            observed_numeric_fields=[],
            missing_for_oracle=["complete_birth_input", "component_virupa_table", "method_variant", "raw_capture_hash"],
        ),
    ]
    return {
        "scope": "public_worked_example_source_triage",
        "created_at": date,
        "status": "source_triage_ready",
        "claim_status": "source_intake_only",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "summary": {
            "source_count": len(rows),
            "numeric_candidate_count": sum(1 for row in rows if row["numeric_fields_present"]),
            "formula_reference_count": sum(1 for row in rows if row["source_role"] == "formula_reference"),
            "oracle_ready_count": 0,
        },
        "sources": rows,
        "boundary": "Public source triage only. Numeric candidates require raw capture and replay before becoming oracle packets.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default="2026-07-20")
    args = parser.parse_args()
    print(json.dumps(build(args.date), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
