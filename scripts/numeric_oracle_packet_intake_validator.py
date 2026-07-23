#!/usr/bin/env python3
"""Validate KP/Prashna/Saham/Sphuta numeric oracle packet intake shape."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE = ROOT / "references/oracle/numeric_oracle_packet_intake_template_2026_07_23.json"

REQUIRED_BY_DOMAIN = {
    "kp_12_cusp": [
        "birth_or_question_input",
        "timezone",
        "ayanamsa",
        "house_system",
        "twelve_exact_cusp_longitudes",
        "twelve_star_lords",
        "twelve_sub_lords",
        "twelve_sub_sub_lords",
        "source_provenance",
        "local_replay",
    ],
    "prashna_sphuta": [
        "complete_question_input",
        "location_timezone",
        "ayanamsa_node_mode",
        "formula_variant",
        "expected_numeric_values",
        "source_provenance",
        "local_replay",
    ],
    "tajika_saham": [
        "complete_annual_input",
        "location_timezone",
        "ayanamsa_node_mode",
        "day_night_convention",
        "expected_numeric_values",
        "source_provenance",
        "local_replay",
    ],
    "advanced_ashtakavarga": [
        "complete_chart_input",
        "location_timezone",
        "ayanamsa_node_mode",
        "technique_variant",
        "expected_numeric_values",
        "source_provenance",
        "local_replay",
    ],
}


def build_template() -> dict[str, Any]:
    return {
        "scope": "numeric_oracle_packet_intake_template",
        "created_at": "2026-07-23",
        "claim_status": "candidate_queue",
        "truth_matrix_allowed": False,
        "production_tuning_allowed": False,
        "packets": [
            {
                "packet_id": "",
                "domain": "kp_12_cusp",
                "birth_or_question_input": {},
                "timezone": "",
                "ayanamsa": "",
                "house_system": "",
                "twelve_exact_cusp_longitudes": [],
                "twelve_star_lords": [],
                "twelve_sub_lords": [],
                "twelve_sub_sub_lords": [],
                "source_provenance": {"url": "", "page_or_artifact_hash": ""},
                "local_replay": {"status": "", "delta_summary": ""},
            },
            {
                "packet_id": "",
                "domain": "advanced_ashtakavarga",
                "complete_chart_input": {},
                "location_timezone": {},
                "ayanamsa_node_mode": "",
                "technique_variant": "",
                "expected_numeric_values": {},
                "source_provenance": {"url": "", "page_or_artifact_hash": ""},
                "local_replay": {"status": "", "delta_summary": ""},
            },
        ],
        "boundary": "Template only. A packet is not a numeric oracle until the validator reports ready_for_replay_packet.",
    }


def validate_packet(packet: dict[str, Any]) -> dict[str, Any]:
    domain = packet.get("domain")
    blockers = []
    if domain not in REQUIRED_BY_DOMAIN:
        blockers.append("unknown_domain")
        required: list[str] = []
    else:
        required = REQUIRED_BY_DOMAIN[domain]
    for field in required:
        value = packet.get(field)
        if value in (None, "", [], {}):
            blockers.append(f"missing_{field}")
    if domain == "kp_12_cusp":
        for field in ("twelve_exact_cusp_longitudes", "twelve_star_lords", "twelve_sub_lords", "twelve_sub_sub_lords"):
            if len(packet.get(field) or []) != 12:
                blockers.append(f"{field}_must_have_12_rows")
    provenance = packet.get("source_provenance") or {}
    if not provenance.get("url") or not provenance.get("page_or_artifact_hash"):
        blockers.append("missing_source_url_or_hash")
    replay = packet.get("local_replay") or {}
    if replay.get("status") not in {"match", "within_tolerance", "mismatch_explained"}:
        blockers.append("local_replay_not_acceptable")
    return {
        "packet_id": packet.get("packet_id", ""),
        "domain": domain,
        "validation_status": "ready_for_replay_packet" if not blockers else "blocked_missing_numeric_or_replay_fields",
        "blockers": sorted(set(blockers)),
    }


def validate_document(document: dict[str, Any]) -> dict[str, Any]:
    rows = [validate_packet(packet) for packet in document.get("packets", [])]
    ready = [row for row in rows if row["validation_status"] == "ready_for_replay_packet"]
    return {
        "scope": "numeric_oracle_packet_intake_validation",
        "claim_status": "ready_contract" if ready else "candidate_queue",
        "truth_matrix_allowed": False,
        "production_tuning_allowed": False,
        "summary": {
            "packet_count": len(rows),
            "ready_packet_count": len(ready),
            "blocked_packet_count": len(rows) - len(ready),
        },
        "rows": rows,
        "boundary": "Validation only; ready packets still need independent review before truth-matrix promotion.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--validate", type=Path)
    args = parser.parse_args()
    data = validate_document(json.loads(args.validate.read_text(encoding="utf-8"))) if args.validate else build_template()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
