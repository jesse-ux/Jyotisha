#!/usr/bin/env python3
"""Build a single-truth inventory for oracle and benchmark assets."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ORACLE_DIR = ROOT / "references" / "oracle"
ARTIFACTS_DIR = ORACLE_DIR / "artifacts"
PENDING_PACKETS_DIR = ARTIFACTS_DIR / "pending_packets"
CASES_DIR = ORACLE_DIR / "cases"
EVIDENCE_TEMPLATES_DIR = ORACLE_DIR / "evidence_packet_templates"
DOCS_DIR = ROOT / "docs" / "research"
PYJHORA_MANIFEST = ARTIFACTS_DIR / "pyjhora_oracle_artifact_manifest.json"

DASHBOARD_CANDIDATES = [
    DOCS_DIR / "oracle_closure_master_dashboard_latest.md",
    DOCS_DIR / "public_benchmark_dashboard_latest.md",
    DOCS_DIR / "tajika_annual_benchmark_dashboard_latest.md",
    DOCS_DIR / "tajika_annual_closure_status_latest.md",
]


def _relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _front_for_name(name: str) -> str:
    lowered = name.lower()
    if "ashtakoot" in lowered or "koota" in lowered:
        return "ashtakoot"
    if "varshaphala" in lowered or "saham" in lowered or "tajika" in lowered or "annual" in lowered:
        return "tajika_sahams"
    if "shadbala" in lowered or "moon_longitude" in lowered:
        return "shadbala"
    if "dasha" in lowered or "vimshottari" in lowered or "historical_epoch" in lowered:
        return "dasha"
    return "general"


def _load_json(path: Path) -> tuple[dict[str, Any] | list[Any] | None, str | None]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - exact parser messages vary
        return None, f"{type(exc).__name__}: {exc}"
    if isinstance(data, (dict, list)):
        return data, None
    return None, "JSON root is not an object or array"


def _compact_json_metadata(path: Path, data: dict[str, Any] | list[Any] | None) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {}

    metadata: dict[str, Any] = {}
    for key in ("scope", "schema_version", "status", "case_id", "capture_id", "id", "source"):
        if key in data:
            metadata[key] = data[key]

    if isinstance(data.get("metadata"), dict):
        source_artifact = data["metadata"].get("source_artifact")
        tool_name = data["metadata"].get("tool_name")
        if source_artifact:
            metadata["source_artifact"] = source_artifact
        if tool_name:
            metadata["tool_name"] = tool_name

    if isinstance(data.get("settings"), dict):
        settings = data["settings"]
        for key in ("ayanamsa", "node_mode", "annual_system", "target_year"):
            if key in settings:
                metadata[key] = settings[key]

    for case_list_key in ("template_cases", "longitude_cases", "ashtakoot_cases", "cases"):
        if isinstance(data.get(case_list_key), list):
            metadata[f"{case_list_key}_count"] = len(data[case_list_key])

    target_placeholders = data.get("target_placeholders")
    if isinstance(target_placeholders, dict):
        metadata["target_placeholder_count"] = len(target_placeholders)

    if path.name == PYJHORA_MANIFEST.name:
        metadata["artifact_count"] = data.get("artifact_count")
        metadata["packet_count"] = data.get("packet_count")

    return metadata


def _file_entry(path: Path, category: str) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "path": _relative(path),
        "name": path.name,
        "category": category,
        "front": _front_for_name(path.name),
        "bytes": path.stat().st_size,
    }
    if path.suffix == ".json":
        data, error = _load_json(path)
        entry["json_valid"] = error is None
        if error:
            entry["json_error"] = error
        entry.update(_compact_json_metadata(path, data))
    return entry


def _existing_files(paths: list[Path]) -> list[Path]:
    return [path for path in paths if path.is_file()]


def _front_summary(groups: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, int]]:
    fronts: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "oracle_registry_count": 0,
            "oracle_case_count": 0,
            "evidence_template_count": 0,
            "pending_packet_count": 0,
            "pyjhora_artifact_count": 0,
            "dashboard_count": 0,
        }
    )
    category_map = {
        "oracle_registries": "oracle_registry_count",
        "oracle_cases": "oracle_case_count",
        "evidence_templates": "evidence_template_count",
        "pending_packets": "pending_packet_count",
        "pyjhora_artifacts": "pyjhora_artifact_count",
        "dashboards": "dashboard_count",
    }
    for group_name, count_key in category_map.items():
        for entry in groups.get(group_name, []):
            fronts[entry["front"]][count_key] += 1
    return {front: dict(payload) for front, payload in sorted(fronts.items())}


def _count_pyjhora_packets(entries: list[dict[str, Any]]) -> int:
    return sum(1 for entry in entries if "pyjhora_" in entry["name"].lower())


def build_inventory() -> dict[str, Any]:
    oracle_registries = [
        _file_entry(path, "oracle_registry")
        for path in sorted(ORACLE_DIR.glob("*_oracle_cases.json"))
        if path.is_file()
    ]
    oracle_cases = [
        _file_entry(path, "oracle_case")
        for path in sorted(CASES_DIR.glob("*.json"))
        if path.is_file()
    ]
    evidence_templates = [
        _file_entry(path, "evidence_template")
        for path in sorted(EVIDENCE_TEMPLATES_DIR.glob("*.json"))
        if path.is_file()
    ]
    pending_packets = [
        _file_entry(path, "pending_packet")
        for path in sorted(PENDING_PACKETS_DIR.glob("*.json"))
        if path.is_file()
    ]
    pyjhora_artifacts = [
        _file_entry(path, "pyjhora_artifact")
        for path in sorted(ARTIFACTS_DIR.glob("pyjhora_*"))
        if path.is_file() and path.name != PYJHORA_MANIFEST.name
    ]
    dashboards = [
        _file_entry(path, "dashboard")
        for path in _existing_files(DASHBOARD_CANDIDATES)
    ]

    pyjhora_manifest_entry = _file_entry(PYJHORA_MANIFEST, "pyjhora_manifest") if PYJHORA_MANIFEST.is_file() else {}
    groups = {
        "oracle_registries": oracle_registries,
        "oracle_cases": oracle_cases,
        "evidence_templates": evidence_templates,
        "pending_packets": pending_packets,
        "pyjhora_artifacts": pyjhora_artifacts,
        "dashboards": dashboards,
    }

    pending_pyjhora_packet_count = _count_pyjhora_packets(pending_packets)
    summary = {
        "oracle_registry_count": len(oracle_registries),
        "oracle_case_count": len(oracle_cases),
        "evidence_template_count": len(evidence_templates),
        "pending_packet_count": len(pending_packets),
        "pending_pyjhora_packet_count": pending_pyjhora_packet_count,
        "pending_non_pyjhora_packet_count": len(pending_packets) - pending_pyjhora_packet_count,
        "pyjhora_artifact_count": len(pyjhora_artifacts),
        "dashboard_count": len(dashboards),
    }

    return {
        "scope": "oracle_benchmark_single_truth_inventory",
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "fronts": _front_summary(groups),
        "files": {
            "oracle_registries": oracle_registries,
            "oracle_cases": oracle_cases,
            "evidence_templates": evidence_templates,
            "pending_packets": pending_packets,
            "pyjhora_artifacts": pyjhora_artifacts,
            "pyjhora_manifest": pyjhora_manifest_entry,
            "dashboards": dashboards,
        },
        "boundary": (
            "This inventory tracks external oracle evidence only. It does not import PyJHora/JHora "
            "implementation code, does not tune production constants, and does not treat internal "
            "consistency as external validation."
        ),
        "next_actions": [
            "Promote verified pending packets into the relevant oracle registry only after metadata and source_artifact pass validation.",
            "Keep PyJHora outputs as black-box artifacts and regenerate the artifact manifest after each external capture batch.",
            "Update public_benchmark_dashboard_latest.md after each validated packet batch so public claims stay conservative.",
            "Use this inventory before changing strict workflow or adjudicator logic that depends on external truth.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Oracle Benchmark Single-Truth Inventory",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- oracle_registry_count: `{summary['oracle_registry_count']}`",
        f"- oracle_case_count: `{summary['oracle_case_count']}`",
        f"- evidence_template_count: `{summary['evidence_template_count']}`",
        f"- pending_packet_count: `{summary['pending_packet_count']}`",
        f"- pending_pyjhora_packet_count: `{summary['pending_pyjhora_packet_count']}`",
        f"- pending_non_pyjhora_packet_count: `{summary['pending_non_pyjhora_packet_count']}`",
        f"- pyjhora_artifact_count: `{summary['pyjhora_artifact_count']}`",
        f"- dashboard_count: `{summary['dashboard_count']}`",
        "",
        "## Oracle Registries",
        "",
    ]
    for entry in report["files"]["oracle_registries"]:
        lines.append(f"- `{entry['path']}` ({entry['front']})")
    lines.extend(["", "## Oracle Case Files", ""])
    for entry in report["files"]["oracle_cases"]:
        lines.append(f"- `{entry['path']}` ({entry['front']})")
    lines.extend(["", "## Pending Evidence Packets", ""])
    for entry in report["files"]["pending_packets"]:
        status = entry.get("status", "unknown")
        case_id = entry.get("case_id") or entry.get("capture_id") or entry["name"]
        lines.append(f"- `{entry['path']}` ({entry['front']}, status: `{status}`, case: `{case_id}`)")
    lines.extend(["", "## PyJHora Black-Box Assets", ""])
    for entry in report["files"]["pyjhora_artifacts"]:
        lines.append(f"- `{entry['path']}` ({entry['front']})")
    manifest = report["files"].get("pyjhora_manifest") or {}
    if manifest:
        lines.extend(["", f"Manifest: `{manifest['path']}`"])
    lines.extend(["", "## Dashboards", ""])
    for entry in report["files"]["dashboards"]:
        lines.append(f"- `{entry['path']}`")
    lines.extend(["", "## Boundary", "", report["boundary"], "", "## Next Actions", ""])
    lines.extend(f"- {item}" for item in report["next_actions"])
    lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate oracle/benchmark single-truth inventory")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--output", help="Optional output path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_inventory()
    text = json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else render_markdown(report)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + ("\n" if not text.endswith("\n") else ""), encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
