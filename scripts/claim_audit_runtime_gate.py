#!/usr/bin/env python3
"""Runtime claim gate backed by evidence_packet_index."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

HIGH_CLAIMS = {"verified_precise_prediction", "complete_absolute_truth", "production_ready", "external_verified"}


def evaluate_claim(index_path: Path, domain: str, requested_claim: str) -> dict:
    index = json.loads(index_path.read_text(encoding="utf-8"))
    packets = [row for row in index["packets"] if row["domain"] == domain]
    if not packets:
        return {
            "decision": "block",
            "domain": domain,
            "requested_claim": requested_claim,
            "allowed_claim_status": "blocked_unknown_domain",
            "production_tuning_allowed": False,
            "blocking_packets": [],
            "boundaries": [f"No evidence packet indexed for domain: {domain}"],
        }

    bad = [row for row in packets if row["claim_status"] in {"blocked", "open_queue"}]
    partial = [row for row in packets if row["claim_status"] in {"partial", "observation_only"}]
    ready = [row for row in packets if row["claim_status"] == "ready_contract"]

    if bad and requested_claim in HIGH_CLAIMS:
        return {
            "decision": "block",
            "domain": domain,
            "requested_claim": requested_claim,
            "allowed_claim_status": "exploratory_unvalidated",
            "production_tuning_allowed": False,
            "blocking_packets": [row["packet_id"] for row in bad],
            "boundaries": [row["claim_boundary"] for row in bad],
        }
    if partial and requested_claim in HIGH_CLAIMS:
        return {
            "decision": "degrade",
            "domain": domain,
            "requested_claim": requested_claim,
            "allowed_claim_status": "partial_method_variant",
            "production_tuning_allowed": False,
            "blocking_packets": [row["packet_id"] for row in partial],
            "boundaries": [row["claim_boundary"] for row in partial],
        }
    if ready and requested_claim == "ready_contract" and not bad and not partial:
        return {
            "decision": "allow",
            "domain": domain,
            "requested_claim": requested_claim,
            "allowed_claim_status": "ready_contract",
            "production_tuning_allowed": False,
            "blocking_packets": [],
            "boundaries": [row["claim_boundary"] for row in ready],
        }
    return {
        "decision": "degrade" if partial or bad else "allow",
        "domain": domain,
        "requested_claim": requested_claim,
        "allowed_claim_status": "limited_research_claim",
        "production_tuning_allowed": False,
        "blocking_packets": [row["packet_id"] for row in bad + partial],
        "boundaries": [row["claim_boundary"] for row in bad + partial + ready],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=Path("references/oracle/evidence_packet_index_2026_07_19.json"))
    parser.add_argument("--domain", required=True)
    parser.add_argument("--claim", required=True)
    args = parser.parse_args()
    print(json.dumps(evaluate_claim(args.index, args.domain, args.claim), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
