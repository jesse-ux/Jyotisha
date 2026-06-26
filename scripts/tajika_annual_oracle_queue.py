#!/usr/bin/env python3
"""Generate Tajika/Sahams annual external-oracle collection tasks.

This is skill-level verification infrastructure. It does not compute annual
chart values and must not be used to tune production rules from template rows.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REQUIRED_EVIDENCE_METADATA_FIELDS = [
    "tool_name",
    "tool_version_or_url",
    "capture_date",
    "source_artifact",
    "ayanamsa",
    "node_mode",
    "timezone",
    "annual_system",
    "target_year",
    "operator_note",
]

SOURCE_GUIDANCE = {
    "preferred_sources": [
        "JHora Varshaphala screenshot",
        "PyJHora black-box annual output",
        "Printed Tajika/Varshaphala example",
    ],
    "collection_steps": [
        "Set the exact birth data, ayanamsa, node mode, timezone and target year in the external annual-chart tool.",
        "Record solar return datetime, Varsha Lagna, Muntha sign, Year Lord and first Mudda Dasha lord.",
        "Record Punya Saham, Rajya Saham and Vivah Saham in absolute 0-360 degree format.",
        "Record visible Tajika Yogas without translating them through this repository's interpretation layer.",
        "Attach a redacted screenshot, stdout snippet or book-example citation under references/oracle/artifacts/.",
    ],
    "promotion_criteria": [
        "All target fields are filled from a documented external annual-chart source.",
        "The source artifact is external evidence, not scripts/varshaphala.py or this repository's local output.",
        "Solar return and timezone/DST conventions are documented before promotion to external_verified.",
        "At least one human-reviewable artifact path is preserved in target.source_artifact.",
    ],
}


def _resolve_path(path: str) -> str:
    if os.path.isabs(path):
        return path
    return os.path.join(ROOT_DIR, path)


def _load_json(path: str) -> dict[str, Any]:
    with open(_resolve_path(path), "r", encoding="utf-8") as fh:
        return json.load(fh)


def _target_fields(value: Any, prefix: str = "target") -> list[str]:
    if prefix == "target" and isinstance(value, dict):
        fields: list[str] = []
        for key, child in value.items():
            fields.extend(_target_fields(child, f"{prefix}.{key}"))
        return fields
    if isinstance(value, dict):
        fields = []
        for key, child in value.items():
            fields.extend(_target_fields(child, f"{prefix}.{key}"))
        return fields
    return [prefix]


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
    elif value is None or value == "" or value == [] or value == {}:
        missing.append(prefix)
    return missing


def _evidence_packet(case: dict[str, Any], target_fields: list[str]) -> dict[str, Any]:
    case_id = case.get("id") or case.get("case_id")
    target = case.get("target", {})
    settings = case.get("settings", {})
    metadata = {
        "tool_name": "",
        "tool_version_or_url": "",
        "capture_date": "",
        "source_artifact": "references/oracle/artifacts/",
        "ayanamsa": settings.get("ayanamsa", ""),
        "node_mode": settings.get("node_mode", ""),
        "timezone": case.get("birth", {}).get("tz", ""),
        "annual_system": settings.get("annual_system", "varshaphala"),
        "target_year": settings.get("target_year", ""),
        "operator_note": "",
    }
    return {
        "capture_id": f"external_{case_id}",
        "status": "draft",
        "case_id": case_id,
        "birth": case.get("birth", {}),
        "settings": settings,
        "required_metadata_fields": REQUIRED_EVIDENCE_METADATA_FIELDS,
        "metadata": metadata,
        "target_placeholders": {field: _target_value(target, field) for field in target_fields},
        "integrity_checks": {
            "must_not_come_from_local_engine": True,
            "requires_external_artifact": True,
            "requires_status_external_verified_before_calibration": True,
            "requires_solar_return_convention": True,
        },
        "promotion_status_after_fill": "external_verified",
    }


def _task_from_template(case: dict[str, Any]) -> dict[str, Any]:
    case_id = case.get("id") or case.get("case_id")
    target = case.get("target", {})
    target_fields = _target_fields(target)
    missing_fields = _missing_target_fields(target)
    status = case.get("status", "template_only")
    ready_for_calibration = status == "external_verified" and not missing_fields
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
        "preferred_sources": SOURCE_GUIDANCE["preferred_sources"],
        "collection_steps": SOURCE_GUIDANCE["collection_steps"],
        "promotion_criteria": SOURCE_GUIDANCE["promotion_criteria"],
        "evidence_packet": _evidence_packet(case, target_fields),
        "ready_for_collection": bool(missing_fields),
        "ready_for_calibration": ready_for_calibration,
        "blocked_reason": "" if ready_for_calibration else "external_annual_evidence_required",
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
        "scope": "tajika_sahams_annual_oracle_collection_queue",
        "schema_version": 1,
        "summary": {
            "total_tasks": len(tasks),
            "by_status": by_status,
            "ready_for_collection": sum(1 for task in tasks if task["ready_for_collection"]),
            "ready_for_calibration": ready_for_calibration,
            "production_tuning_allowed": ready_for_calibration > 0 and ready_for_calibration == len(tasks),
            "next_action": "Collect external Varshaphala target values, then promote rows to external_verified.",
        },
        "tasks": tasks,
        "boundary": (
            "Rows remain collection tasks until external solar return, Muntha, Year Lord, Mudda Dasha, "
            "Sahams and Tajika Yogas targets are filled. Local annual-chart output and template-only rows "
            "must not be used for production tuning."
        ),
    }


def render_markdown(queue: dict[str, Any]) -> str:
    summary = queue["summary"]
    lines = [
        "# Tajika/Sahams Annual External Oracle Collection Queue",
        "",
        f"total_tasks: `{summary['total_tasks']}`",
        f"ready_for_collection: `{summary['ready_for_collection']}`",
        f"ready_for_calibration: `{summary['ready_for_calibration']}`",
        f"production_tuning_allowed: `{str(summary['production_tuning_allowed']).lower()}`",
        "",
        "## Required Evidence",
        "",
        "Solar return datetime, Varsha Lagna, Muntha, Year Lord, Mudda Dasha, Punya Saham, Rajya Saham, Vivah Saham and Tajika Yogas.",
        "",
        "| task_id | status | missing fields | preferred sources |",
        "|---|---|---|---|",
    ]
    for task in queue["tasks"]:
        lines.append(
            f"| {task['task_id']} | `{task['status']}` | {', '.join(task['missing_target_fields'])} | {', '.join(task['preferred_sources'])} |"
        )
    lines.extend(["", queue["boundary"], ""])
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Tajika/Sahams annual oracle collection tasks")
    parser.add_argument("--oracle-file", required=True)
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    queue = build_queue(_load_json(args.oracle_file))
    if args.format == "markdown":
        print(render_markdown(queue))
    else:
        print(json.dumps(queue, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
