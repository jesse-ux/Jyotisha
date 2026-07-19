#!/usr/bin/env python3
"""Validate evidence packet index paths, ids, claim statuses, and boundaries."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"
VALID_CLAIM_STATUSES = {
    "blocked",
    "blocked_until_human_labels",
    "blocked_until_oracle",
    "open_queue",
    "observation_only",
    "partial",
    "ready_contract",
    "reference_only",
    "source_intake_only",
    "tooling_observation_only",
}


def repo_path(path: str) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else ROOT / candidate


def build(index_path: Path) -> dict[str, Any]:
    index = json.loads(index_path.read_text(encoding="utf-8"))
    packets = index.get("packets", [])
    ids = [row.get("packet_id") for row in packets]
    id_counts = Counter(ids)
    duplicate_ids = sorted(packet_id for packet_id, count in id_counts.items() if packet_id and count > 1)

    missing_paths = [
        {"packet_id": row.get("packet_id"), "path": row.get("path")}
        for row in packets
        if not row.get("path") or not repo_path(row["path"]).exists()
    ]
    invalid_claim_statuses = [
        {"packet_id": row.get("packet_id"), "claim_status": row.get("claim_status")}
        for row in packets
        if row.get("claim_status") not in VALID_CLAIM_STATUSES
    ]
    missing_required_fields = [
        {
            "packet_id": row.get("packet_id"),
            "missing": [
                field
                for field in ("packet_id", "path", "domain", "claim_status", "consumer_policy", "claim_boundary")
                if not row.get(field)
            ],
        }
        for row in packets
    ]
    missing_required_fields = [row for row in missing_required_fields if row["missing"]]

    status = "pass"
    if missing_paths or duplicate_ids or invalid_claim_statuses or missing_required_fields:
        status = "fail"

    return {
        "scope": "evidence_packet_index_integrity",
        "created_at": "2026-07-19",
        "status": status,
        "source_index": str(index_path.relative_to(ROOT)) if index_path.is_relative_to(ROOT) else str(index_path),
        "summary": {
            "packet_count": len(packets),
            "missing_path_count": len(missing_paths),
            "duplicate_packet_id_count": len(duplicate_ids),
            "invalid_claim_status_count": len(invalid_claim_statuses),
            "missing_required_field_count": len(missing_required_fields),
        },
        "duplicate_packet_ids": duplicate_ids,
        "missing_paths": missing_paths,
        "invalid_claim_statuses": invalid_claim_statuses,
        "missing_required_fields": missing_required_fields,
        "valid_claim_statuses": sorted(VALID_CLAIM_STATUSES),
        "boundary": "Integrity pass means indexed packets are present and shaped; it does not upgrade any oracle claim.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    args = parser.parse_args()
    print(json.dumps(build(args.index), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
