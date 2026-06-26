#!/usr/bin/env python3
"""Validate filled external oracle evidence packets.

This validator checks evidence packets produced by oracle_collection_queue.py.
It does not promote oracle rows or tune production constants; it only reports
whether a packet is internally complete enough to be reviewed as external
evidence.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_ENGINE_MARKERS = [
    "local engine",
    "this-repo",
    "jyotish_engine.py",
    "scripts/jyotish",
    "oracle_collection_queue.py",
    "oracle_boundary_audit.py",
]
SHADBALA_REQUIRED_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
SHADBALA_REQUIRED_COMPONENTS = ["sthana", "dig", "kala", "chesta", "naisargika", "drik"]
SHADBALA_COMPONENT_MAX_RUPA = 20.0
SHADBALA_DRIK_MIN_RUPA = -20.0
SHADBALA_TOTAL_TOLERANCE_RUPA = 0.05
ASHTAKOOT_SCORE_RANGES = {
    "target.total_score": (0.0, 36.0),
    "target.varna": (0.0, 1.0),
    "target.vashya": (0.0, 2.0),
    "target.tara": (0.0, 3.0),
    "target.yoni": (0.0, 4.0),
    "target.graha_maitri": (0.0, 5.0),
    "target.gana": (0.0, 6.0),
    "target.bhakoot": (0.0, 7.0),
    "target.nadi": (0.0, 8.0),
}
ASHTAKOOT_COMPONENT_FIELDS = [
    "target.varna",
    "target.vashya",
    "target.tara",
    "target.yoni",
    "target.graha_maitri",
    "target.gana",
    "target.bhakoot",
    "target.nadi",
]


def _resolve_path(path: str) -> str:
    if os.path.isabs(path):
        return path
    return os.path.join(ROOT_DIR, path)


def _load_json(path: str) -> dict[str, Any]:
    with open(_resolve_path(path), "r", encoding="utf-8") as fh:
        return json.load(fh)


def _is_blank(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def _is_missing_external_artifact(value: Any) -> bool:
    if _is_blank(value):
        return True
    text = str(value).strip()
    if text.endswith("/"):
        return True
    return text in {"references/oracle/artifacts", "references/oracle/artifacts/"}


def _is_local_engine_artifact(packet: dict[str, Any]) -> bool:
    metadata = packet.get("metadata", {})
    haystack = " ".join(
        str(metadata.get(field, ""))
        for field in ["tool_name", "tool_version_or_url", "source_artifact", "operator_note"]
    ).lower()
    return any(marker in haystack for marker in LOCAL_ENGINE_MARKERS)


def _validate_packet(task: dict[str, Any]) -> dict[str, Any]:
    packet = task.get("evidence_packet", {})
    problems: list[str] = []
    capture_id = packet.get("capture_id") or f"missing_capture_id:{task.get('case_id', 'unknown')}"
    metadata = packet.get("metadata", {})

    for field in packet.get("required_metadata_fields", []):
        if _is_blank(metadata.get(field)):
            problems.append(f"missing_metadata:{field}")

    if _is_missing_external_artifact(metadata.get("source_artifact")):
        problems.append("missing_external_artifact")

    target_placeholders = packet.get("target_placeholders", {})
    expected_fields = task.get("target_fields") or task.get("missing_target_fields", [])
    if set(target_placeholders.keys()) != set(expected_fields):
        problems.append("target_placeholder_mismatch")

    for field, value in target_placeholders.items():
        if _is_blank(value):
            problems.append(f"placeholder_unfilled:{field}")

    shadbala_components = target_placeholders.get("target.shadbala_components")
    if "target.shadbala_components" in expected_fields:
        problems.extend(_validate_shadbala_components(shadbala_components))

    if "target.total_score" in expected_fields:
        problems.extend(_validate_ashtakoot_scores(target_placeholders))

    integrity = packet.get("integrity_checks", {})
    if integrity.get("must_not_come_from_local_engine") and _is_local_engine_artifact(packet):
        problems.append("local_engine_artifact_rejected")

    if integrity.get("requires_external_artifact") and _is_missing_external_artifact(metadata.get("source_artifact")):
        if "missing_external_artifact" not in problems:
            problems.append("missing_external_artifact")

    if packet.get("status") != "external_verified":
        problems.append(f"status_not_external_verified:{packet.get('status', 'missing')}")

    valid = not problems
    return {
        "task_id": task.get("task_id"),
        "case_id": task.get("case_id"),
        "capture_id": capture_id,
        "status": packet.get("status", "missing"),
        "valid": valid,
        "ready_for_calibration": valid and packet.get("status") == "external_verified",
        "problems": problems,
    }


def _validate_shadbala_components(value: Any) -> list[str]:
    problems: list[str] = []
    if _is_blank(value) or not isinstance(value, dict):
        return ["missing_shadbala_component:all_planets"]
    for planet in SHADBALA_REQUIRED_PLANETS:
        row = value.get(planet)
        if not isinstance(row, dict) or _is_blank(row):
            problems.append(f"missing_shadbala_component:{planet}")
            continue
        for component in SHADBALA_REQUIRED_COMPONENTS:
            component_value = row.get(component)
            if _is_blank(component_value):
                problems.append(f"missing_shadbala_component:{planet}.{component}")
                continue
            if not isinstance(component_value, (int, float)) or isinstance(component_value, bool):
                problems.append(f"invalid_shadbala_component_type:{planet}.{component}")
                continue
            if component == "drik" and component_value < SHADBALA_DRIK_MIN_RUPA:
                problems.append(f"invalid_shadbala_component_range:{planet}.{component}")
                continue
            if component != "drik" and component_value < 0:
                problems.append(f"invalid_shadbala_component_negative:{planet}.{component}")
                continue
            if component_value > SHADBALA_COMPONENT_MAX_RUPA:
                problems.append(f"invalid_shadbala_component_range:{planet}.{component}")
        total_rupa = row.get("total_rupa")
        if _is_blank(total_rupa):
            problems.append(f"missing_shadbala_total_rupa:{planet}")
            continue
        if not isinstance(total_rupa, (int, float)) or isinstance(total_rupa, bool):
            problems.append(f"invalid_shadbala_total_rupa_type:{planet}")
            continue
        if total_rupa < 0:
            problems.append(f"invalid_shadbala_total_rupa_negative:{planet}")
            continue
        if total_rupa > SHADBALA_COMPONENT_MAX_RUPA * len(SHADBALA_REQUIRED_COMPONENTS):
            problems.append(f"invalid_shadbala_total_rupa_range:{planet}")
            continue
        numeric_components = [
            float(row[component])
            for component in SHADBALA_REQUIRED_COMPONENTS
            if isinstance(row.get(component), (int, float)) and not isinstance(row.get(component), bool)
        ]
        if len(numeric_components) == len(SHADBALA_REQUIRED_COMPONENTS):
            component_sum = sum(numeric_components)
            if abs(component_sum - float(total_rupa)) > SHADBALA_TOTAL_TOLERANCE_RUPA:
                problems.append(f"shadbala_total_rupa_sum_mismatch:{planet}")
    return problems


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _validate_ashtakoot_scores(target_placeholders: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    numeric_values: dict[str, float] = {}
    for field, (minimum, maximum) in ASHTAKOOT_SCORE_RANGES.items():
        if field not in target_placeholders:
            continue
        value = target_placeholders.get(field)
        if _is_blank(value):
            continue
        if not _is_number(value):
            problems.append(f"invalid_ashtakoot_score_type:{field}")
            continue
        numeric_value = float(value)
        numeric_values[field] = numeric_value
        if numeric_value < minimum or numeric_value > maximum:
            problems.append(f"invalid_ashtakoot_score_range:{field}")

    if "target.total_score" in numeric_values and all(
        field in numeric_values for field in ASHTAKOOT_COMPONENT_FIELDS
    ):
        component_sum = sum(numeric_values[field] for field in ASHTAKOOT_COMPONENT_FIELDS)
        if abs(component_sum - numeric_values["target.total_score"]) > 0.01:
            problems.append("ashtakoot_score_sum_mismatch")
    return problems


def build_report(queue: dict[str, Any]) -> dict[str, Any]:
    packets = [_validate_packet(task) for task in queue.get("tasks", [])]
    ready_for_calibration = sum(1 for packet in packets if packet["ready_for_calibration"])
    valid_packets = sum(1 for packet in packets if packet["valid"])
    return {
        "scope": "external_oracle_evidence_validation",
        "schema_version": 1,
        "summary": {
            "total_packets": len(packets),
            "valid_packets": valid_packets,
            "ready_for_calibration": ready_for_calibration,
            "all_packets_external_verified": bool(packets) and valid_packets == len(packets),
            "production_tuning_allowed": bool(packets) and ready_for_calibration == len(packets),
        },
        "packets": packets,
        "boundary": (
            "Evidence packets can become review-ready only with external artifacts and filled target "
            "values. Local engine output remains rejected as an external oracle source."
        ),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate external oracle evidence packets")
    parser.add_argument("--queue-file", required=True, help="Path to oracle collection queue JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    queue = _load_json(args.queue_file)
    print(json.dumps(build_report(queue), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
