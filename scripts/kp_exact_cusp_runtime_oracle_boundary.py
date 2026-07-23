#!/usr/bin/env python3
"""Summarize KP exact cusp runtime state vs public numeric oracle blocker."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_RAW = ROOT / "references/oracle/vedicastro_kp_house_cusp_probe_steve_jobs_2026_07_23.json"
HUNT = ROOT / "references/oracle/kp_exact_cusp_public_worked_example_hunt_v2_2026_07_22.json"
OUTPUT = ROOT / "references/oracle/kp_exact_cusp_runtime_oracle_boundary_2026_07_23.json"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _stable_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _runtime_summary(raw: dict[str, Any]) -> dict[str, Any]:
    houses = ((raw.get("raw") or {}).get("houses") or [])
    return {
        "artifact": str(RUNTIME_RAW.relative_to(ROOT)),
        "artifact_sha256": hashlib.sha256(RUNTIME_RAW.read_bytes()).hexdigest(),
        "engine": raw.get("engine"),
        "claim_status": raw.get("claim_status"),
        "house_count": len(houses),
        "fields": ["cusp_longitude", "star_lord", "sub_lord", "sub_sub_lord"],
        "schema_fingerprint": raw.get("schema_fingerprint") or {},
        "raw_hash": raw.get("raw_hash"),
    }


def build() -> dict[str, Any]:
    raw = _load(RUNTIME_RAW)
    hunt = _load(HUNT)
    required = hunt.get("required_numeric_oracle_fields") or [
        "birth_or_question_input",
        "ayanamsa",
        "house_system_or_kp_cusp_method",
        "exact_cusp_longitudes",
        "cusp_star_lord",
        "cusp_sub_lord",
        "cusp_sub_sub_lord",
    ]
    required = [
        "birth_or_question_input" if item == "birth_or_query_input" else item
        for item in required
    ]
    candidate_sources = [
        {
            "id": "archive_kp_reader_candidate",
            "source": "references/oracle/kp_archive_numeric_extraction_result_2026_07_21.json",
            "missing": ["complete input", "full 12-cusp star/sub/sub-sub table"],
            "promotion": "queue_only",
        },
        {
            "id": "astrosage_kp_cuspal_sub_lord",
            "source": "https://www.astrosage.com/kp/cuspal-sub-lord.asp",
            "missing": ["fixed public input", "published expected 12-cusp output table", "raw hash"],
            "promotion": "queue_only",
        },
        {
            "id": "vedicastro_python_surface",
            "source": "references/open_source_sources/VedicAstro/vedicastro/VedicAstro.py",
            "missing": ["independent expected values"],
            "promotion": "queue_only",
        },
    ]
    packet = {
        "scope": "kp_exact_cusp_runtime_oracle_boundary",
        "created_at": "2026-07-23",
        "claim_status": "calculable_displayable_public_oracle_blocked",
        "runtime_raw_status": "single_engine_observation_ready",
        "public_numeric_oracle_status": "blocked_missing_complete_worked_example",
        "truth_matrix_allowed": False,
        "production_tuning_allowed": False,
        "runtime_raw": _runtime_summary(raw),
        "required_oracle_fields": required,
        "complete_numeric_oracle_count": 0,
        "candidate_sources": candidate_sources,
        "packet_hash": hashlib.sha256(_stable_json(candidate_sources + [required]).encode("utf-8")).hexdigest(),
        "boundary": "KP exact cusp/star/sub/sub-sub can be displayed from runtime raw as observation; it cannot be used as verified precise event timing until a public numeric worked example closes.",
    }
    return packet


def main() -> int:
    packet = build()
    OUTPUT.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(packet, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
