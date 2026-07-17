#!/usr/bin/env python3
"""Build VedAstro Shadbala/Ashtakavarga oracle request packets.

This packet is secondary evidence only. It does not execute prediction,
change local scores, or promote final labels.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ADJUDICATOR_POLICY = {
    "role": "external_technique_evidence",
    "can_change_score": False,
    "can_set_dominant_label": False,
    "can_set_payout_label": False,
    "allowed_destinations": ["secondary_context", "technique_audit"],
}

STRENGTH_METHODS = [
    {
        "technique": "VedAstro Shadbala Oracle",
        "method": "CalculateShadbala",
        "api_endpoint": "Calculate/Shadbala",
    },
    {
        "technique": "VedAstro Ashtakavarga Oracle",
        "method": "CalculateAshtakavarga",
        "api_endpoint": "Calculate/Ashtakavarga",
    },
]


def build_strength_oracle_packet(domain: str = "career") -> dict[str, Any]:
    requests = [
        {
            "operation": "calculation_method",
            "role": "external_technique_evidence",
            "domain": domain,
            "method": item["method"],
            "api_endpoint": item["api_endpoint"],
            "status": "preview",
        }
        for item in STRENGTH_METHODS
    ]
    audit_rows = [
        {
            "technique": item["technique"],
            "status": "preview",
            "role": "external_strength_evidence",
            "effect": "secondary_context_only_no_score_or_label_lift",
        }
        for item in STRENGTH_METHODS
    ]
    return {
        "scope": "vedastro_strength_oracle_packet",
        "status": "preview",
        "domain": domain,
        "adjudicator_policy": dict(ADJUDICATOR_POLICY),
        "requests": requests,
        "technique_audit_rows": audit_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domain", default="career")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    packet = build_strength_oracle_packet(args.domain)
    text = json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
