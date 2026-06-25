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


def _resolve_path(path: str) -> str:
    if os.path.isabs(path):
        return path
    return os.path.join(ROOT_DIR, path)


def _load_json(path: str) -> dict[str, Any]:
    with open(_resolve_path(path), "r", encoding="utf-8") as fh:
        return json.load(fh)


def _is_blank(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


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

    if _is_blank(metadata.get("source_artifact")):
        problems.append("missing_external_artifact")

    target_placeholders = packet.get("target_placeholders", {})
    expected_fields = task.get("target_fields") or task.get("missing_target_fields", [])
    if set(target_placeholders.keys()) != set(expected_fields):
        problems.append("target_placeholder_mismatch")

    for field, value in target_placeholders.items():
        if _is_blank(value):
            problems.append(f"placeholder_unfilled:{field}")

    integrity = packet.get("integrity_checks", {})
    if integrity.get("must_not_come_from_local_engine") and _is_local_engine_artifact(packet):
        problems.append("local_engine_artifact_rejected")

    if integrity.get("requires_external_artifact") and _is_blank(metadata.get("source_artifact")):
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
