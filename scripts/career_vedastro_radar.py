#!/usr/bin/env python3
"""VedAstro-assisted career timing radar.

External VedAstro signals are secondary evidence only. They do not change
local scores, dominant labels, or final career/prashna adjudication by
themselves.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import vedastro_service_adapter


def build_career_radar_packet(case: dict[str, Any], *, start_date: str, end_date: str, case_id: str = "user_chart") -> dict[str, Any]:
    result = vedastro_service_adapter.run_range_scan_for_case(
        case,
        "career",
        start_date,
        end_date,
        case_id=case_id,
    )
    policy = result.get("adjudicator_policy") if isinstance(result.get("adjudicator_policy"), dict) else {}
    can_change_score = bool(policy.get("can_change_score", False))
    status = result.get("status", "blocked")
    return {
        "scope": "career_vedastro_radar",
        "status": "ok" if status == "ok" else "blocked",
        "blocked_reason": None if status == "ok" else result.get("reason") or status,
        "domain": "career",
        "adjudicator_use": "secondary_evidence_only",
        "can_change_score": can_change_score,
        "can_set_final_verdict": False,
        "start_date": start_date,
        "end_date": end_date,
        "vedastro_range_scan_result": result,
        "technique_audit_row": {
            "technique": "VedAstro Career Range Scan",
            "used": status == "ok",
            "status": status,
            "role": "external_secondary_evidence",
            "confidence_effect": "raises_attention_only_not_final_score" if status == "ok" else "blocked_no_effect",
        },
    }


def _load_case(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-json", type=Path, required=True)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--case-id", default="user_chart")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    packet = build_career_radar_packet(
        _load_case(args.case_json),
        start_date=args.start_date,
        end_date=args.end_date,
        case_id=args.case_id,
    )
    text = json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if packet["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
