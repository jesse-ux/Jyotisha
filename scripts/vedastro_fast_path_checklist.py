#!/usr/bin/env python3
"""Render the fastest practical VedAstro integration checklist.

This artifact turns the parity matrix plus live official catalog snapshot into
an execution-friendly view:

- what should go through official MCP
- what should go through the official Python bridge
- what should go through the REST adapter
- what should stay local because the repo is already stronger there
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts import vedastro_parity_matrix


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON_PATH = ROOT / "docs" / "research" / "vedastro_fast_path_checklist_latest.json"
DEFAULT_MARKDOWN_PATH = ROOT / "docs" / "research" / "vedastro_fast_path_checklist_latest.md"
CATALOG_PATH = ROOT / "scratch" / "local" / "vedastro_adapter" / "method_catalog_snapshot.json"

LANE_TITLES = {
    "official_mcp": "Direct Official MCP",
    "official_python_bridge": "Official Python Bridge",
    "rest_adapter": "REST Adapter",
    "local_native_preferred": "Local Native Preferred",
    "hybrid_router": "Hybrid Router",
    "external_evidence_only": "External Evidence Only",
}


def _load_catalog_summary() -> dict[str, Any]:
    if not CATALOG_PATH.exists():
        return {
            "available": False,
            "path": str(CATALOG_PATH),
            "tag_count": 0,
            "method_count": 0,
        }
    payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    summary = payload.get("summary") or {}
    return {
        "available": True,
        "path": str(CATALOG_PATH),
        "tag_count": int(summary.get("tag_count", 0) or 0),
        "method_count": int(summary.get("method_count", 0) or 0),
    }


def build_checklist() -> dict[str, Any]:
    matrix = vedastro_parity_matrix.build_matrix()
    catalog = _load_catalog_summary()

    grouped: dict[str, list[dict[str, Any]]] = {lane: [] for lane in LANE_TITLES}
    for row in matrix["rows"]:
        grouped.setdefault(row["fastest_path_lane"], []).append(
            {
                "capability": row["vedastro_capability"],
                "priority": row["priority"],
                "recommended_path": row["recommended_path"],
                "local_status": row["local_status"],
                "adjudicator_use": row["adjudicator_use"],
                "route_notes": row["route_notes"],
                "gap_notes": row["gap_notes"],
                "local_assets": row["local_assets"],
            }
        )

    return {
        "scope": "vedastro_fast_path_checklist",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "row_count": len(matrix["rows"]),
            "local_registry_technique_count": matrix["summary"].get("local_registry_technique_count"),
            "catalog_tag_count": catalog["tag_count"],
            "catalog_method_count": catalog["method_count"],
        },
        "boundary": {
            "do_not_clone_vedastro": True,
            "keep_local_adjudicator_authoritative": True,
            "external_outputs_default_to_secondary_context": True,
        },
        "official_catalog": catalog,
        "lanes": grouped,
    }


def render_markdown(checklist: dict[str, Any]) -> str:
    summary = checklist["summary"]
    catalog = checklist["official_catalog"]
    lines = [
        "# VedAstro 596+ Nodes Fast-Path Checklist",
        "",
        f"- Generated: `{checklist['generated_at']}`",
        f"- Local registry techniques: `{summary['local_registry_technique_count']}`",
        f"- Official catalog tags: `{summary['catalog_tag_count']}`",
        f"- Official catalog methods/events: `{summary['catalog_method_count']}`",
        "",
        "## Boundary",
        "",
        "- Do not clone VedAstro wholesale into local code.",
        "- Keep the local adjudicator as the final reasoning layer.",
        "- Default all external outputs to secondary evidence unless explicitly promoted by local tests and contracts.",
        "",
        "## Lane Breakdown",
        "",
    ]

    for lane, title in LANE_TITLES.items():
        rows = checklist["lanes"].get(lane) or []
        lines.append(f"### {title}")
        lines.append("")
        if not rows:
            lines.append("- None.")
            lines.append("")
            continue
        for row in rows:
            assets = ", ".join(row["local_assets"]) if row["local_assets"] else "-"
            lines.append(
                f"- `{row['capability']}` [{row['priority']}]"
                f" - local=`{row['local_status']}`, adjudicator=`{row['adjudicator_use']}`"
                f"; assets: {assets}"
            )
            lines.append(f"  route: {row['route_notes']}")
            lines.append(f"  gap: {row['gap_notes']}")
        lines.append("")

    lines.extend(
        [
            "## Immediate Execution Order",
            "",
            "1. Use `Direct Official MCP` where an official MCP surface is available to agents.",
            "2. Use `Official Python Bridge` for broad calculator access that does not need browser/session orchestration.",
            "3. Use `REST Adapter` for range scans and endpoint-style external evidence.",
            "4. Keep `Local Native Preferred` rows local; do not waste time rebuilding what is already stronger here.",
            "5. Use `Hybrid Router` only where parity or oracle closure still matters more than raw breadth.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(
    checklist: dict[str, Any],
    *,
    json_path: Path = DEFAULT_JSON_PATH,
    markdown_path: Path = DEFAULT_MARKDOWN_PATH,
) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(checklist, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(checklist) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)

    checklist = build_checklist()
    if args.write:
        write_outputs(checklist)
    if args.format == "json":
        print(json.dumps(checklist, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(checklist))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
