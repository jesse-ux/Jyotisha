#!/usr/bin/env python3
"""Create CI-safe capture packets for Muhurta numeric source candidates."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TRIAGE = ROOT / "references/oracle/public_worked_example_source_triage_2026_07_20.json"
OUT = ROOT / "references/oracle/muhurta_numeric_candidate_capture_packet_2026_07_20.json"


def sha(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def next_path(source_id: str) -> str:
    return f"references/oracle/artifacts/{source_id}_raw_capture_packet.json"


def build(date: str) -> dict[str, Any]:
    triage = json.loads(TRIAGE.read_text(encoding="utf-8"))
    rows = []
    for src in triage["sources"]:
        if src["domain"] != "muhurta_factor_scoring" or not src["numeric_fields_present"]:
            continue
        request = {
            "source_id": src["source_id"],
            "url": src["url"],
            "topic": src["topic"],
            "observed_numeric_fields": src["observed_numeric_fields"],
        }
        missing = list(src["missing_for_oracle"])
        for field in ["raw_capture_hash", "exact_method_settings", "replay_comparison"]:
            if field not in missing:
                missing.append(field)
        rows.append(
            {
                "source_id": src["source_id"],
                "domain": src["domain"],
                "topic": src["topic"],
                "url": src["url"],
                "source_observation_hash": src["observation_hash"],
                "canonical_request_hash": sha(request),
                "observed_numeric_fields": src["observed_numeric_fields"],
                "raw_capture_status": "pending_raw_page_capture",
                "upgrade_status": "not_oracle_ready",
                "missing_for_oracle": missing,
                "next_artifact_path": next_path(src["source_id"]),
                "claim_boundary": "Numeric-looking public source; not oracle-ready until raw page, exact settings, hash, and local replay comparison are archived.",
            }
        )
    return {
        "scope": "muhurta_numeric_candidate_capture_packet",
        "created_at": date,
        "status": "capture_packet_ready",
        "claim_status": "source_intake_only",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "sources": {"source_triage": str(TRIAGE.relative_to(ROOT))},
        "summary": {
            "candidate_count": len(rows),
            "oracle_ready_count": 0,
            "pending_raw_capture_count": sum(1 for row in rows if row["raw_capture_status"] == "pending_raw_page_capture"),
        },
        "capture_rows": rows,
        "boundary": "Capture packet staging only; does not calculate or validate Muhurta verdicts.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default="2026-07-20")
    args = parser.parse_args()
    print(json.dumps(build(args.date), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
