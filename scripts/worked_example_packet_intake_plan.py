#!/usr/bin/env python3
"""Build a domain intake plan from numeric worked-example eligibility rows."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ELIGIBILITY = ROOT / "references/oracle/worked_example_numeric_packet_eligibility_2026_07_20.json"
OUT = ROOT / "references/oracle/worked_example_packet_intake_plan_2026_07_20.json"

DOMAIN_BY_TOPIC = {
    "KP cusp": "kp_precision_timing",
    "KP sub-lord table": "kp_precision_timing",
    "Tarabala/Chandrabala": "muhurta_factor_scoring",
    "Rahu Kalam": "muhurta_factor_scoring",
    "Shadbala Virupa": "shadbala_component_closure",
}

STATUS_RANK = {
    "runtime_only_public_oracle_missing": 4,
    "reference_table_hash_needed": 3,
    "raw_capture_needed": 2,
    "fixture_and_raw_capture_needed": 2,
    "formula_reference_only": 1,
}

CANONICAL_BLOCKERS = {
    "fixed public input case": "public_numeric_expected_values",
    "per-component Virupa expected values": "public_numeric_expected_values",
    "expected factor table": "public_numeric_expected_values",
    "expected interval": "public_numeric_expected_values",
    "worked example link": "public_numeric_expected_values",
    "raw output hash": "raw_capture_hash",
    "captured raw hash": "raw_capture_hash",
    "raw capture hash": "raw_capture_hash",
    "table hash": "source_table_hash",
    "captured table raw": "source_table_raw",
    "license/copyright boundary": "license_boundary",
    "formula variant": "method_variant",
    "method settings": "method_settings",
    "ayanamsa": "method_settings",
    "house_system": "method_settings",
}


def canonicalize(fields: list[str]) -> list[str]:
    out = []
    for field in fields:
        key = CANONICAL_BLOCKERS.get(field, field)
        if key not in out:
            out.append(key)
    return out


def topic_domain(topic: str) -> str:
    return DOMAIN_BY_TOPIC.get(topic, "worked_example_collection")


def build(date: str) -> dict[str, Any]:
    source = json.loads(ELIGIBILITY.read_text(encoding="utf-8"))
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in source["rows"]:
        item = {
            "topic": row["topic"],
            "url": row["url"],
            "candidate_type": row["candidate_type"],
            "eligibility_status": row["eligibility_status"],
            "runtime_observation_available": row["runtime_observation_available"],
            "blocking_fields": canonicalize(row["missing_for_oracle"]),
            "upgrade_policy": "observation_only_until_numeric_packet",
            "next_capture_artifact": f"references/oracle/artifacts/{row['topic'].lower().replace('/', '_').replace(' ', '_')}_worked_example_packet.json",
        }
        grouped[topic_domain(row["topic"])].append(item)

    domain_queues = []
    for domain in sorted(grouped):
        items = grouped[domain]
        statuses = [item["eligibility_status"] for item in items]
        blockers = []
        for item in items:
            for field in item["blocking_fields"]:
                if field not in blockers:
                    blockers.append(field)
        domain_queues.append(
            {
                "domain": domain,
                "candidate_count": len(items),
                "highest_status": max(statuses, key=lambda x: STATUS_RANK.get(x, 0)),
                "blocking_fields": blockers,
                "next_action_owner": "oracle_intake",
                "closure_condition": "Promote only after exact public input, method settings, expected numeric values, raw capture, raw hash, and replay comparison are archived.",
                "items": items,
            }
        )

    return {
        "scope": "worked_example_packet_intake_plan",
        "created_at": date,
        "status": "intake_plan_ready",
        "claim_status": "open_queue",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "sources": {"eligibility": str(ELIGIBILITY.relative_to(ROOT))},
        "summary": {
            "domain_count": len(domain_queues),
            "candidate_count": sum(row["candidate_count"] for row in domain_queues),
            "oracle_ready_count": 0,
            "domains_with_runtime_observation": sum(
                1 for row in domain_queues if any(item["runtime_observation_available"] for item in row["items"])
            ),
        },
        "domain_queues": domain_queues,
        "boundary": "Intake plan only; public examples remain observation-only until numeric packets are captured and replayed.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default="2026-07-20")
    args = parser.parse_args()
    print(json.dumps(build(args.date), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
