#!/usr/bin/env python3
"""Validate Dasha-only external oracle evidence packets.

The generic oracle evidence validator is intentionally strict for combined
Dasha/Shadbala rows. This validator isolates the Dasha closure path so one
external Vimshottari boundary can be accepted without waiting for Shadbala
absolute-value components.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from typing import Any


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DASHA_TARGET_FIELD = "target.vimshottari_start_date"
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


def _is_missing_external_artifact(value: Any) -> bool:
    if _is_blank(value):
        return True
    text = str(value).strip()
    return text.endswith("/") or text in {"references/oracle/artifacts", "references/oracle/artifacts/"}


def _artifact_exists(value: Any) -> bool:
    if _is_missing_external_artifact(value):
        return False
    return os.path.exists(_resolve_path(str(value)))


def _is_local_engine_artifact(packet: dict[str, Any]) -> bool:
    metadata = packet.get("metadata", {})
    haystack = " ".join(
        str(metadata.get(field, ""))
        for field in ["tool_name", "tool_version_or_url", "source_artifact", "operator_note"]
    ).lower()
    return any(marker in haystack for marker in LOCAL_ENGINE_MARKERS)


def _valid_iso_date(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is not None


def _validate_dasha_packet(task: dict[str, Any]) -> dict[str, Any]:
    packet = task.get("evidence_packet", {})
    metadata = packet.get("metadata", {})
    placeholders = packet.get("target_placeholders", {})
    problems: list[str] = []

    for field in packet.get("required_metadata_fields", []):
        if _is_blank(metadata.get(field)):
            problems.append(f"missing_metadata:{field}")

    source_artifact = metadata.get("source_artifact")
    if _is_missing_external_artifact(source_artifact):
        problems.append("missing_external_artifact")
    elif not _artifact_exists(source_artifact):
        problems.append("external_artifact_not_found")

    if packet.get("status") != "external_verified":
        problems.append(f"status_not_external_verified:{packet.get('status', 'missing')}")

    value = placeholders.get(DASHA_TARGET_FIELD)
    if _is_blank(value):
        problems.append(f"placeholder_unfilled:{DASHA_TARGET_FIELD}")
    elif not _valid_iso_date(value):
        problems.append(f"invalid_dasha_date:{DASHA_TARGET_FIELD}")

    integrity = packet.get("integrity_checks", {})
    if integrity.get("must_not_come_from_local_engine") and _is_local_engine_artifact(packet):
        problems.append("local_engine_artifact_rejected")

    valid = not problems
    return {
        "task_id": task.get("task_id"),
        "case_id": task.get("case_id"),
        "capture_id": packet.get("capture_id") or f"missing_capture_id:{task.get('case_id', 'unknown')}",
        "status": packet.get("status", "missing"),
        "target_field": DASHA_TARGET_FIELD,
        "valid": valid,
        "ready_for_dasha_calibration": valid and packet.get("status") == "external_verified",
        "problems": problems,
    }


def build_report(queue: dict[str, Any]) -> dict[str, Any]:
    packets = [
        _validate_dasha_packet(task)
        for task in queue.get("tasks", [])
        if DASHA_TARGET_FIELD in task.get("target_fields", [])
    ]
    valid_packets = sum(1 for packet in packets if packet["valid"])
    ready_for_dasha_calibration = sum(1 for packet in packets if packet["ready_for_dasha_calibration"])
    return {
        "scope": "dasha_external_oracle_evidence_validation",
        "schema_version": 1,
        "summary": {
            "total_dasha_packets": len(packets),
            "valid_dasha_packets": valid_packets,
            "ready_for_dasha_calibration": ready_for_dasha_calibration,
            "all_dasha_packets_external_verified": bool(packets) and valid_packets == len(packets),
            "production_tuning_allowed": bool(packets) and ready_for_dasha_calibration == len(packets),
        },
        "packets": packets,
        "boundary": (
            "This validator only accepts external Dasha boundary evidence. "
            "It does not validate Shadbala absolute values and must not be used to claim full oracle closure."
        ),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Dasha-only external oracle evidence packets")
    parser.add_argument("--queue-file", required=True, help="Path to oracle collection queue JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    queue = _load_json(args.queue_file)
    print(json.dumps(build_report(queue), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
