#!/usr/bin/env python3
"""Generate a repeatable external-oracle collection queue.

This script turns oracle template rows into executable data-collection tasks.
It does not compute Jyotish values and must not be used to tune production
constants. A task is only calibration-ready after external target fields are
filled and the status is promoted to external_verified.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from typing import Any


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


SOURCE_GUIDANCE = {
    "longitude": {
        "preferred_sources": ["VedAstro HTTP API", "JHora manual screenshot", "PyJHora black-box output"],
        "steps": [
            "Set the exact birth data, ayanamsa, node mode and timezone in the external tool.",
            "Record sidereal longitude in absolute 0-360 degree format and sign-local DMS format.",
            "Attach source metadata: tool name, version or URL, ayanamsa, node mode and capture date.",
        ],
        "promotion_criteria": [
            "External source metadata is present.",
            "A numeric sidereal longitude target is filled.",
            "The value did not come from this repository's local engine output.",
        ],
    },
    "dasha": {
        "preferred_sources": ["JHora manual screenshot", "PyJHora black-box output", "secondary VedAstro API check"],
        "steps": [
            "Capture Moon longitude, nakshatra, pada and Vimshottari start-boundary settings.",
            "Record Mahadasha and Antardasha boundary dates in ISO date format.",
            "Keep year-length, timezone and daylight-saving assumptions with the row.",
        ],
        "promotion_criteria": [
            "At least one external Dasha boundary date is filled.",
            "Moon longitude, ayanamsa and node mode are documented beside the date.",
            "A second source or manual screenshot is attached before production tuning is considered.",
        ],
    },
    "shadbala": {
        "preferred_sources": ["JHora manual screenshot", "PyJHora black-box output"],
        "steps": [
            "Capture planet-by-planet Sthana, Dig, Kala, Chesta, Naisargika and Drik Bala rows.",
            "Record Virupa and Rupa totals without applying a global scaling factor.",
            "Preserve the external tool's ayanamsa, house and node settings.",
        ],
        "promotion_criteria": [
            "All six component targets are filled for the seven Shadbala planets.",
            "Totals are traceable to component sums.",
            "The row is not derived from this repository's local Shadbala output.",
        ],
    },
    "ashtakoot": {
        "preferred_sources": ["JHora compatibility screenshot", "VedAstro HTTP/API output", "AstroSage public compatibility screen"],
        "steps": [
            "Set both birth records or both Moon longitudes in the external compatibility tool.",
            "Record the 36-point total score and all eight Kuta component scores.",
            "Capture Kuja/Manglik status and any visible ayanamsa, node mode or matching settings.",
        ],
        "promotion_criteria": [
            "All eight Ashtakoot component targets are filled from an external compatibility source.",
            "The 36-point total is traceable to component scores.",
            "The row is not derived from this repository's local synastry/ashtakoot output.",
        ],
    },
}


FIELD_TO_MODULE = {
    "moon_sidereal_longitude_deg": "longitude",
    "sun_sidereal_longitude_deg": "longitude",
    "ascendant_longitude_deg": "longitude",
    "vimshottari_start_date": "dasha",
    "shadbala_components": "shadbala",
    "total_score": "ashtakoot",
    "varna": "ashtakoot",
    "vashya": "ashtakoot",
    "tara": "ashtakoot",
    "yoni": "ashtakoot",
    "graha_maitri": "ashtakoot",
    "gana": "ashtakoot",
    "bhakoot": "ashtakoot",
    "nadi": "ashtakoot",
    "kuja_status": "ashtakoot",
}

REQUIRED_EVIDENCE_METADATA_FIELDS = [
    "tool_name",
    "tool_version_or_url",
    "capture_date",
    "source_artifact",
    "ayanamsa",
    "node_mode",
    "timezone",
    "operator_note",
]


def _resolve_path(path: str) -> str:
    if os.path.isabs(path):
        return path
    return os.path.join(ROOT_DIR, path)


def _load_json(path: str) -> dict[str, Any]:
    with open(_resolve_path(path), "r", encoding="utf-8") as fh:
        return json.load(fh)


def _write_json(path: str, value: dict[str, Any]) -> None:
    with open(_resolve_path(path), "w", encoding="utf-8") as fh:
        json.dump(value, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def _target_fields(value: Any, prefix: str = "target") -> list[str]:
    if prefix == "target" and isinstance(value, dict):
        return [f"{prefix}.{key}" for key in value]
    fields: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            fields.extend(_target_fields(child, f"{prefix}.{key}"))
    else:
        fields.append(prefix)
    return fields


def _target_value(target: dict[str, Any], field: str) -> Any:
    value: Any = target
    for part in field.split(".")[1:]:
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def _missing_target_fields(value: Any, prefix: str = "target") -> list[str]:
    missing: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            missing.extend(_missing_target_fields(child, f"{prefix}.{key}"))
    elif value is None:
        missing.append(prefix)
    return missing


def _target_modules(missing_fields: list[str]) -> list[str]:
    modules: list[str] = []
    for field in missing_fields:
        leaf = field.split(".")[-1]
        module = FIELD_TO_MODULE.get(leaf)
        if module and module not in modules:
            modules.append(module)
    return modules


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _evidence_packet(case: dict[str, Any], target_fields: list[str]) -> dict[str, Any]:
    case_id = case.get("id") or case.get("case_id")
    existing = case.get("evidence_packet", {})
    target = case.get("target", {})
    target_placeholders = {
        field: _target_value(target, field)
        for field in target_fields
    }
    existing_placeholders = existing.get("target_placeholders", {})
    if isinstance(existing_placeholders, dict):
        target_placeholders.update(existing_placeholders)
    default_metadata = {
        "tool_name": "",
        "tool_version_or_url": "",
        "capture_date": "",
        "source_artifact": "references/oracle/artifacts/",
        "ayanamsa": case.get("settings", {}).get("ayanamsa", ""),
        "node_mode": case.get("settings", {}).get("node_mode", ""),
        "timezone": case.get("birth", {}).get("tz", ""),
        "operator_note": "",
    }
    existing_metadata = existing.get("metadata", {})
    if isinstance(existing_metadata, dict):
        default_metadata.update(existing_metadata)
    return {
        "capture_id": existing.get("capture_id") or f"external_{case_id}",
        "status": existing.get("status", "draft"),
        "case_id": case_id,
        "birth": case.get("birth", {}),
        "settings": case.get("settings", {}),
        "required_metadata_fields": REQUIRED_EVIDENCE_METADATA_FIELDS,
        "metadata": default_metadata,
        "target_placeholders": target_placeholders,
        "integrity_checks": {
            "must_not_come_from_local_engine": True,
            "requires_external_artifact": True,
            "requires_status_external_verified_before_calibration": True,
            "reject_global_shadbala_scaling": "target.shadbala_components" in target_fields,
        },
        "promotion_status_after_fill": "external_verified",
    }


def _task_from_template(case: dict[str, Any]) -> dict[str, Any]:
    case_id = case.get("id") or case.get("case_id")
    target = case.get("target", {})
    target_fields = _target_fields(target)
    missing_fields = _missing_target_fields(target)
    modules = _target_modules(target_fields)
    preferred_sources: list[str] = []
    collection_steps: list[str] = []
    promotion_criteria: list[str] = []

    for module in modules:
        guidance = SOURCE_GUIDANCE[module]
        preferred_sources.extend(guidance["preferred_sources"])
        collection_steps.extend(guidance["steps"])
        promotion_criteria.extend(guidance["promotion_criteria"])

    status = case.get("status", "template_only")
    ready_for_calibration = status == "external_verified" and not missing_fields
    if ready_for_calibration or missing_fields:
        blocked_reason = ""
    else:
        blocked_reason = "external_evidence_status_required"

    return {
        "task_id": f"collect_{case_id}",
        "case_id": case_id,
        "status": status,
        "source": case.get("source"),
        "privacy": case.get("privacy"),
        "birth": case.get("birth", {}),
        "settings": case.get("settings", {}),
        "target_fields": target_fields,
        "missing_target_fields": missing_fields,
        "target_modules": modules,
        "preferred_sources": _dedupe(preferred_sources),
        "collection_steps": _dedupe(collection_steps),
        "promotion_criteria": _dedupe(promotion_criteria),
        "evidence_packet": _evidence_packet(case, target_fields),
        "ready_for_collection": bool(missing_fields),
        "ready_for_calibration": ready_for_calibration,
        "blocked_reason": blocked_reason,
        "do_not_tune_production": not ready_for_calibration,
        "verification_note": case.get("verification_note", ""),
    }


def build_queue(oracle: dict[str, Any]) -> dict[str, Any]:
    tasks = [_task_from_template(case) for case in oracle.get("template_cases", [])]
    by_status: dict[str, int] = {}
    for task in tasks:
        status = task.get("status", "unknown")
        by_status[status] = by_status.get(status, 0) + 1

    ready_for_calibration = sum(1 for task in tasks if task["ready_for_calibration"])
    return {
        "scope": "external_oracle_collection_queue",
        "schema_version": 1,
        "summary": {
            "total_tasks": len(tasks),
            "by_status": by_status,
            "ready_for_collection": sum(1 for task in tasks if task["ready_for_collection"]),
            "ready_for_calibration": ready_for_calibration,
            "production_tuning_allowed": ready_for_calibration > 0 and ready_for_calibration == len(tasks),
            "next_action": "Collect external target values, then promote individual rows to external_verified.",
        },
        "tasks": tasks,
        "boundary": (
            "Rows remain collection tasks until external targets are filled. Local engine output and "
            "template-only rows must not be used for Dasha/Shadbala production tuning."
        ),
    }


def _markdown_escape(value: Any) -> str:
    text = ", ".join(value) if isinstance(value, list) else str(value)
    return text.replace("|", "\\|")


def render_markdown(queue: dict[str, Any]) -> str:
    summary = queue["summary"]
    lines = [
        "# Dasha/Shadbala External Oracle Collection Queue",
        "",
        f"total_tasks: `{summary['total_tasks']}`",
        f"ready_for_collection: `{summary['ready_for_collection']}`",
        f"ready_for_calibration: `{summary['ready_for_calibration']}`",
        f"production_tuning_allowed: `{str(summary['production_tuning_allowed']).lower()}`",
        "",
        "## Evidence Packet Fields",
        "",
        "Each JSON task includes an `evidence_packet.capture_id` draft packet with these required metadata fields:",
        "",
        ", ".join(REQUIRED_EVIDENCE_METADATA_FIELDS),
        "",
        "| task_id | case_id | status | missing fields | preferred sources |",
        "|---|---|---|---|---|",
    ]
    for task in queue["tasks"]:
        lines.append(
            "| {task_id} | {case_id} | `{status}` | {missing} | {sources} |".format(
                task_id=_markdown_escape(task["task_id"]),
                case_id=_markdown_escape(task["case_id"]),
                status=_markdown_escape(task["status"]),
                missing=_markdown_escape(task["missing_target_fields"]),
                sources=_markdown_escape(task["preferred_sources"]),
            )
        )
    lines.extend(["", queue["boundary"], ""])
    return "\n".join(lines)


def _safe_filename(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")
    return safe or "external_oracle_packet"


def _set_target_value(target: dict[str, Any], field: str, value: Any) -> None:
    parts = field.split(".")
    if not parts or parts[0] != "target":
        return
    cursor = target
    for part in parts[1:-1]:
        child = cursor.get(part)
        if not isinstance(child, dict):
            child = {}
            cursor[part] = child
        cursor = child
    cursor[parts[-1]] = value


def apply_evidence_packet(oracle: dict[str, Any], packet: dict[str, Any]) -> bool:
    case_id = packet.get("case_id")
    if not case_id:
        return False
    for case in oracle.get("template_cases", []):
        if case.get("id") != case_id and case.get("case_id") != case_id:
            continue
        target = case.setdefault("target", {})
        placeholders = packet.get("target_placeholders", {})
        if isinstance(placeholders, dict):
            for field, value in placeholders.items():
                _set_target_value(target, field, value)
        case["status"] = packet.get("status", case.get("status", "draft"))
        case["evidence_packet"] = {
            "capture_id": packet.get("capture_id"),
            "status": packet.get("status"),
            "metadata": packet.get("metadata", {}),
        }
        return True
    return False


def write_evidence_packets(queue: dict[str, Any], output_dir: str) -> int:
    os.makedirs(output_dir, exist_ok=True)
    written = 0
    for task in queue.get("tasks", []):
        packet = task.get("evidence_packet", {})
        capture_id = packet.get("capture_id") or f"external_{task.get('case_id', 'unknown')}"
        packet_path = os.path.join(output_dir, f"{_safe_filename(str(capture_id))}.json")
        with open(packet_path, "w", encoding="utf-8") as fh:
            json.dump(packet, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        written += 1
    return written


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate external oracle collection tasks")
    parser.add_argument("--oracle-file", required=True, help="Path to oracle fixture JSON")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument(
        "--write-packet-dir",
        help="Optional directory where draft evidence_packet JSON files should be written.",
    )
    parser.add_argument(
        "--apply-packet",
        action="append",
        default=[],
        help="Filled evidence_packet JSON to merge back into the oracle file.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    oracle = _load_json(args.oracle_file)
    applied_packets = 0
    for packet_path in args.apply_packet:
        packet = _load_json(packet_path)
        if apply_evidence_packet(oracle, packet):
            applied_packets += 1
    if applied_packets:
        _write_json(args.oracle_file, oracle)
    queue = build_queue(oracle)
    if applied_packets:
        queue["summary"]["applied_evidence_packets"] = applied_packets
    if args.write_packet_dir:
        queue["summary"]["written_evidence_packets"] = write_evidence_packets(queue, args.write_packet_dir)
    if args.format == "markdown":
        print(render_markdown(queue))
    else:
        print(json.dumps(queue, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
