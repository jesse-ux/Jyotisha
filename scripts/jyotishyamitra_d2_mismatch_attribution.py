#!/usr/bin/env python3
"""Extract D2-only disagreement from a pinned jyotishyamitra observation packet."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_report(packet: dict) -> dict:
    comparison = packet.get("comparison") or {}
    rows = comparison.get("rows") or []
    d2_rows = [row for row in rows if row.get("section") == "D2"]
    disagreements = [
        row for row in d2_rows
        if row.get("local_status") == "mismatch" and row.get("xalen_status") == "mismatch"
    ]
    non_d2_disagreements = [
        row for row in rows if row.get("section") != "D2" and row.get("local_status") == "mismatch"
    ]
    return {
        "scope": "jyotishyamitra_d2_mismatch_attribution",
        "source_packet": packet.get("scope"),
        "source_raw_sha256": packet.get("raw_sha256"),
        "source_wheel_sha256": packet.get("wheel_sha256"),
        "status": "d2_source_rule_attributed_external_truth_open",
        "claim_status": "observation_only",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "summary": {
            "d2_row_count": len(d2_rows),
            "joint_disagreement_count": len(disagreements),
            "non_d2_local_disagreement_count": len(non_d2_disagreements),
        },
        "joint_disagreements": disagreements,
        "source_rule_attribution": {
            "engine": "jyotishyamitra 1.4.0",
            "source_member": "support/mod_divisional.py::hora_from_long",
            "rule_summary": "Assign D2 sign from successive 15-degree chunks across absolute zodiac longitude.",
            "local_contrast": "Local and Xalen use the Parashara Leo/Cancer Hora mapping by sign parity and half-sign.",
        },
        "external_method_references": [
            {
                "url": "https://www.cosmicsquares.com/free-horoscope/hora-chart",
                "tier": "secondary_calculator_documentation",
                "supports": "Odd/even sign parity maps D2 halves to Leo/Cancer.",
                "does_not_support": "Same-input numeric oracle for this public case.",
            },
            {
                "url": "https://sarvpujavidhi.com/hora-chart-in-vedic-astrology/",
                "tier": "secondary_method_reference",
                "supports": "Each sign is bisected into 15-degree Sun/Moon Hora halves with Leo/Cancer mapping.",
                "does_not_support": "Software implementation identity or a reproducible worked-case replay.",
            },
        ],
        "candidate_explanation": "Source-rule attribution is complete; external worked-example truth arbitration is still open.",
        "required_before_resolution": [
            "public numeric D2 worked example with input/settings",
            "same-input replay against at least two independent engines",
        ],
        "boundary": "A source-rule attribution explains the disagreement but does not select a D2 tradition. Do not tune wealth interpretation or select an engine by majority vote.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = build_report(json.loads(args.packet.read_text(encoding="utf-8")))
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
