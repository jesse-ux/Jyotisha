#!/usr/bin/env python3
"""Parse PyJHora Shadbala stdout into same-unit component rows."""
from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "references/oracle/artifacts/pyjhora_steve_jobs_shadbala_lahiri_stdout_20260627.txt"
OUTPUT = ROOT / "references/oracle/pyjhora_steve_jobs_shadbala_stdout_components_2026_07_21.json"
PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
COMPONENTS = ["sthana", "dig", "kala", "chesta", "naisargika", "drik"]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _extract_component_json(text: str) -> dict[str, dict[str, float]]:
    prefix = "SHADBALA_COMPONENT_RUPA_JSON "
    line = next((row[len(prefix) :] for row in text.splitlines() if row.startswith(prefix)), None)
    if line is None:
        raise ValueError("SHADBALA_COMPONENT_RUPA_JSON line missing")
    raw = json.loads(line)
    return {
        planet: {key: float(value) for key, value in values.items()}
        for planet, values in raw.items()
    }


def _extract_raw_virupa(text: str) -> list[list[float]]:
    prefix = "SHADBALA_RAW_VIRUPA "
    line = next((row[len(prefix) :] for row in text.splitlines() if row.startswith(prefix)), None)
    if line is None:
        raise ValueError("SHADBALA_RAW_VIRUPA line missing")
    return ast.literal_eval(line)


def build() -> dict[str, Any]:
    text = SOURCE.read_text(encoding="utf-8")
    source_hash = _sha256(SOURCE)
    component_rupa = _extract_component_json(text)
    raw_virupa = _extract_raw_virupa(text)
    rows: list[dict[str, Any]] = []
    for planet in PLANETS:
        values = component_rupa[planet]
        for component in COMPONENTS:
            rupa = round(values[component], 4)
            rows.append(
                {
                    "planet": planet,
                    "component": component,
                    "rupa": rupa,
                    "virupa": round(rupa * 60, 2),
                    "source_unit": "rupa",
                    "normalized_unit": "virupa",
                    "source_artifact": str(SOURCE.relative_to(ROOT)),
                    "source_artifact_sha256": source_hash,
                }
            )
    return {
        "scope": "pyjhora_shadbala_stdout_component_packet",
        "created_at": "2026-07-21",
        "claim_status": "observation_only",
        "truth_matrix_allowed": False,
        "production_tuning_allowed": False,
        "source_artifact": str(SOURCE.relative_to(ROOT)),
        "source_artifact_sha256": source_hash,
        "source_raw_rows": {
            "shadbala_raw_virupa_row_count": len(raw_virupa),
            "component_rows_present": "SHADBALA_COMPONENT_RUPA_JSON",
        },
        "summary": {
            "planet_count": len(PLANETS),
            "component_count": len(COMPONENTS),
            "component_row_count": len(rows),
        },
        "component_rows": rows,
        "boundary": "Parsed PyJHora stdout into same-unit component observations only. This does not arbitrate formula variants or create absolute Shadbala parity.",
    }


def main() -> int:
    packet = build()
    OUTPUT.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(packet, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
