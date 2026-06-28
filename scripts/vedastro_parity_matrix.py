#!/usr/bin/env python3
"""Build a VedAstro-to-local parity matrix.

The matrix is an audit/planning artifact. It keeps VedAstro service evidence,
local native implementation, and adjudicator use separate so external API
coverage is not mislabeled as local production parity.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON_PATH = ROOT / "docs" / "research" / "vedastro_parity_matrix_latest.json"
DEFAULT_MARKDOWN_PATH = ROOT / "docs" / "research" / "vedastro_parity_matrix_latest.md"

ALLOWED_RECOMMENDED_PATHS = {
    "local_native",
    "vedastro_adapter",
    "new_local_impl",
    "external_evidence_only",
    "hybrid_local_plus_vedastro",
}

ALLOWED_FASTEST_PATH_LANES = {
    "local_native_preferred",
    "official_mcp",
    "official_python_bridge",
    "rest_adapter",
    "hybrid_router",
    "external_evidence_only",
}


VEDASTRO_CAPABILITY_SEEDS: list[dict[str, Any]] = [
    {
        "vedastro_capability": "EventsAtRange / Life Event Graph",
        "category": "timing_range_scan",
        "domains": ["event", "timing", "transit"],
        "local_assets": ["transit_trigger", "dasha", "narayana_dasha", "vedastro_service_adapter.range_scan"],
        "can_call_vedastro": True,
        "recommended_path": "hybrid_local_plus_vedastro",
        "fastest_path_lane": "rest_adapter",
        "priority": "P0",
        "license_boundary": "external_service_or_clean_room_only",
        "adjudicator_use": "oracle_only",
        "gap_notes": "Local timing modules exist, but a high-frequency day/hour event graph is not yet a local productized radar.",
        "route_notes": "Use official REST adapter first for range scans; keep local adjudicator as the reasoning layer.",
    },
    {
        "vedastro_capability": "Ayanamsa Selection",
        "category": "ephemeris_policy",
        "domains": ["core"],
        "local_assets": ["ayanamsa_utils", "ephemeris_adapter_contract"],
        "can_call_vedastro": True,
        "recommended_path": "hybrid_local_plus_vedastro",
        "fastest_path_lane": "hybrid_router",
        "priority": "P0",
        "license_boundary": "external_service_or_clean_room_only",
        "adjudicator_use": "oracle_only",
        "gap_notes": "Local Lahiri path is usable, but broad ayanamsa parity and public comparison artifacts remain incomplete.",
        "route_notes": "Prefer local ayanamsa controls for production and use VedAstro only as parity/oracle evidence.",
    },
    {
        "vedastro_capability": "D1-D60 Divisional Charts",
        "category": "varga",
        "domains": ["varga", "divisional", "d60"],
        "local_assets": ["varga", "varga_full", "shodasavarga", "divisional_charts_extended"],
        "can_call_vedastro": True,
        "recommended_path": "local_native",
        "fastest_path_lane": "local_native_preferred",
        "priority": "P0",
        "license_boundary": "local_native_or_clean_room",
        "adjudicator_use": "primary",
        "gap_notes": "Local varga coverage is strong; keep VedAstro/PyJHora as benchmark evidence rather than replacing local math.",
        "route_notes": "Do not pay external-call cost here; local engine is already the primary route.",
    },
    {
        "vedastro_capability": "Ashtakavarga",
        "category": "strength",
        "domains": ["ashtakavarga", "strength"],
        "local_assets": ["ashtakavarga", "ashtakavarga_pav", "ashtakavarga_sodhita", "finance_ashtakavarga_bridge"],
        "can_call_vedastro": True,
        "recommended_path": "hybrid_local_plus_vedastro",
        "fastest_path_lane": "official_python_bridge",
        "priority": "P0",
        "license_boundary": "local_native_or_external_oracle",
        "adjudicator_use": "secondary",
        "gap_notes": "SAV/BAV is in production; PAV/Sodhita/Kakshya bridges need continued regression before being dominant labels.",
        "route_notes": "Use the Python bridge for broad calculator access while local strict workflows stay authoritative.",
    },
    {
        "vedastro_capability": "Shadbala",
        "category": "strength",
        "domains": ["shadbala", "strength"],
        "local_assets": ["shadbala", "shadbala_advanced", "shadbala_component_cap", "oracle_shadbala_queue"],
        "can_call_vedastro": True,
        "recommended_path": "hybrid_local_plus_vedastro",
        "fastest_path_lane": "official_python_bridge",
        "priority": "P0",
        "license_boundary": "local_native_or_external_oracle",
        "adjudicator_use": "secondary",
        "gap_notes": "Local component-aware cap exists; absolute external oracle closure is still incomplete.",
        "route_notes": "Broad strength calculators are easiest through the Python bridge, then folded back as oracle evidence.",
    },
    {
        "vedastro_capability": "Jaimini / Chara Dasha",
        "category": "jaimini",
        "domains": ["jaimini", "narayana", "karaka"],
        "local_assets": ["jaimini.py", "AK", "DK", "UL", "Chara Dasha", "Jaimini marriage bridge v1"],
        "can_call_vedastro": True,
        "recommended_path": "local_native",
        "fastest_path_lane": "local_native_preferred",
        "priority": "P0",
        "license_boundary": "local_native_mit_attribution_for_reused_parts",
        "adjudicator_use": "secondary",
        "gap_notes": "Core Jaimini exists; mission/career/marriage quality adjudicator folding is not yet exhaustive.",
        "route_notes": "Keep Jaimini native; external engines help only as spot-check evidence.",
    },
    {
        "vedastro_capability": "Synastry / Ashtakoot",
        "category": "relationship_matching",
        "domains": ["synastry", "relationship", "marriage"],
        "local_assets": ["synastry.py", "ashtakoot.py", "36-point Ashtakoot", "16-factor compatibility"],
        "can_call_vedastro": True,
        "recommended_path": "local_native",
        "fastest_path_lane": "local_native_preferred",
        "priority": "P0",
        "license_boundary": "local_native_mit_attribution_for_reused_parts",
        "adjudicator_use": "secondary",
        "gap_notes": "Matching modules exist and API-backed; relationship adjudicator still needs a formal bridge.",
        "route_notes": "Local matching is already stronger than a thin external call unless you need an oracle comparison.",
    },
    {
        "vedastro_capability": "Tajika Annual",
        "category": "annual_prediction",
        "domains": ["tajika", "annual", "varshaphala", "saham"],
        "local_assets": ["tajika.py", "varshaphala.py", "sahams", "solar_return"],
        "can_call_vedastro": True,
        "recommended_path": "hybrid_local_plus_vedastro",
        "fastest_path_lane": "official_python_bridge",
        "priority": "P0",
        "license_boundary": "local_native_or_external_oracle",
        "adjudicator_use": "secondary",
        "gap_notes": "Annual modules exist; yearly career/wealth/month windows need stronger strict-workflow integration.",
        "route_notes": "Use Python bridge for breadth, but keep year-chart reasoning and labels local.",
    },
    {
        "vedastro_capability": "Prashna / Horary",
        "category": "horary",
        "domains": ["prashna", "kp"],
        "local_assets": ["prashna.py", "kp_system.py", "upagraha_gulika_maandi", "sphuta_trisphuta_family"],
        "can_call_vedastro": True,
        "recommended_path": "local_native",
        "fastest_path_lane": "local_native_preferred",
        "priority": "P0",
        "license_boundary": "local_native_or_clean_room",
        "adjudicator_use": "secondary",
        "gap_notes": "Horary modules exist but are not yet a first-class question adjudicator route.",
        "route_notes": "No need to outsource core horary math while local modules already exist.",
    },
    {
        "vedastro_capability": "Report Rendering",
        "category": "presentation",
        "domains": ["report", "image"],
        "local_assets": ["report_artifact API", "report_builder.py", "chart_renderer.py", "jyotish-app export"],
        "can_call_vedastro": False,
        "recommended_path": "new_local_impl",
        "fastest_path_lane": "local_native_preferred",
        "priority": "P0",
        "license_boundary": "local_native",
        "adjudicator_use": "not_used",
        "gap_notes": "HTML/PDF artifact path exists; polished SVG/PDF chart rendering and cloud-scale report production are not finished.",
        "route_notes": "Rendering is a local product concern, not a VedAstro dependency.",
    },
    {
        "vedastro_capability": "MCP / API Surface",
        "category": "service_surface",
        "domains": ["event", "relationship", "wealth", "career"],
        "local_assets": [
            "mcp_server.py",
            "jyotish_api_server.py",
            "strict workflows",
            "vedastro_service_adapter.py",
            "vedastro_official_mcp_bridge.py",
        ],
        "can_call_vedastro": True,
        "recommended_path": "hybrid_local_plus_vedastro",
        "fastest_path_lane": "official_mcp",
        "priority": "P0",
        "license_boundary": "external_service_or_local_native",
        "adjudicator_use": "primary",
        "gap_notes": "Local API/MCP surfaces exist and the official public MCP bridge is live; REST adapter official endpoint smoke still depends on configured endpoint-backed execution.",
        "route_notes": "If official MCP is available, that is the fastest direct agent path; otherwise fall back to local REST adapter.",
    },
    {
        "vedastro_capability": "Numerology / Non-Jyotish Tools",
        "category": "adjacent_tools",
        "domains": [],
        "local_assets": [],
        "can_call_vedastro": True,
        "recommended_path": "external_evidence_only",
        "fastest_path_lane": "external_evidence_only",
        "priority": "P2",
        "license_boundary": "external_service_only",
        "adjudicator_use": "not_used",
        "gap_notes": "Adjacent product feature; not required for Jyotish adjudicator depth.",
        "route_notes": "Do not implement locally unless it becomes product-critical.",
    },
    {
        "vedastro_capability": "Birth Time ML / Rectification Assistant",
        "category": "birth_time_rectification",
        "domains": ["birth"],
        "local_assets": ["birth_time_rectifier.py", "rectification_gate", "jyotish-app rectification"],
        "can_call_vedastro": True,
        "recommended_path": "hybrid_local_plus_vedastro",
        "fastest_path_lane": "rest_adapter",
        "priority": "P1",
        "license_boundary": "external_service_or_local_native",
        "adjudicator_use": "secondary",
        "gap_notes": "Local rectification exists; ML parity with VedAstro-style service behavior is not established.",
        "route_notes": "Use VedAstro externally only as supporting evidence; local rectification gate stays in control.",
    },
]


def _run_audit_capabilities() -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, "scripts/audit_capabilities.py", "--mode", "validate"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(proc.stdout)


def _infer_local_status(seed: dict[str, Any], audit: dict[str, Any]) -> str:
    domain_counts = audit.get("domain_counts") if isinstance(audit, dict) else {}
    status_counts = audit.get("status_counts") if isinstance(audit, dict) else {}
    domains = seed.get("domains") or []

    if not seed.get("local_assets"):
        return "missing"

    matched_domains = [domain for domain in domains if int(domain_counts.get(domain, 0) or 0) > 0]
    if matched_domains:
        if seed["recommended_path"] in {"new_local_impl", "hybrid_local_plus_vedastro"}:
            return "partial"
        return "covered" if int(status_counts.get("covered", 0) or 0) else "complete"

    if seed["recommended_path"] == "external_evidence_only":
        return "external_only"
    return "partial"


def _build_row(seed: dict[str, Any], audit: dict[str, Any]) -> dict[str, Any]:
    recommended_path = seed["recommended_path"]
    if recommended_path not in ALLOWED_RECOMMENDED_PATHS:
        raise ValueError(f"unsupported recommended_path: {recommended_path}")

    return {
        "vedastro_capability": seed["vedastro_capability"],
        "category": seed["category"],
        "local_status": _infer_local_status(seed, audit),
        "local_assets": list(seed["local_assets"]),
        "can_call_vedastro": bool(seed["can_call_vedastro"]),
        "recommended_path": recommended_path,
        "fastest_path_lane": seed["fastest_path_lane"],
        "priority": seed["priority"],
        "license_boundary": seed["license_boundary"],
        "adjudicator_use": seed["adjudicator_use"],
        "gap_notes": seed["gap_notes"],
        "route_notes": seed["route_notes"],
    }


def build_matrix(audit: dict[str, Any] | None = None) -> dict[str, Any]:
    audit = audit if audit is not None else _run_audit_capabilities()
    rows = [_build_row(seed, audit) for seed in VEDASTRO_CAPABILITY_SEEDS]
    rows.sort(key=lambda row: (row["priority"], row["category"], row["vedastro_capability"]))

    status_counts: dict[str, int] = {}
    path_counts: dict[str, int] = {}
    lane_counts: dict[str, int] = {}
    priority_counts: dict[str, int] = {}
    for row in rows:
        status_counts[row["local_status"]] = status_counts.get(row["local_status"], 0) + 1
        path_counts[row["recommended_path"]] = path_counts.get(row["recommended_path"], 0) + 1
        lane_counts[row["fastest_path_lane"]] = lane_counts.get(row["fastest_path_lane"], 0) + 1
        priority_counts[row["priority"]] = priority_counts.get(row["priority"], 0) + 1

    return {
        "scope": "vedastro_parity_matrix",
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "row_count": len(rows),
            "p0_count": priority_counts.get("P0", 0),
            "status_counts": status_counts,
            "recommended_path_counts": path_counts,
            "fastest_path_lane_counts": lane_counts,
            "local_registry_technique_count": audit.get("technique_count"),
        },
        "boundary": {
            "not_a_clone_claim": True,
            "external_outputs_are_adapter_evidence_until_promoted": True,
            "local_adjudicator_remains_final_reasoning_layer": True,
        },
        "rows": rows,
    }


def render_markdown(matrix: dict[str, Any]) -> str:
    summary = matrix["summary"]
    lines = [
        "# VedAstro Parity Matrix",
        "",
        f"- Generated: `{matrix['generated_at']}`",
        f"- Rows: `{summary['row_count']}`",
        f"- P0 rows: `{summary['p0_count']}`",
        f"- Local registry technique count: `{summary.get('local_registry_technique_count')}`",
        "",
        "## Honesty Boundary",
        "",
        "VedAstro calls are external adapter evidence until a capability is promoted by local tests, oracle artifacts, or strict workflow integration. This matrix does not claim clone-level parity.",
        "",
        "## Summary",
        "",
        f"- Local status counts: `{json.dumps(summary['status_counts'], ensure_ascii=False, sort_keys=True)}`",
        f"- Recommended path counts: `{json.dumps(summary['recommended_path_counts'], ensure_ascii=False, sort_keys=True)}`",
        f"- Fastest path lane counts: `{json.dumps(summary['fastest_path_lane_counts'], ensure_ascii=False, sort_keys=True)}`",
        "",
        "## Matrix",
        "",
        "| VedAstro capability | Category | Local status | Path | Fastest lane | Priority | Adjudicator use | Local assets | Gap notes |",
        "|---|---|---:|---|---|---:|---|---|---|",
    ]
    for row in matrix["rows"]:
        assets = ", ".join(row["local_assets"]) if row["local_assets"] else "-"
        lines.append(
            "| {vedastro_capability} | {category} | {local_status} | {recommended_path} | {fastest_path_lane} | {priority} | {adjudicator_use} | {assets} | {gap_notes} |".format(
                assets=assets,
                **row,
            )
        )
    lines.extend(
        [
            "",
            "## Next Actions",
            "",
            "1. Promote `VedAstro adapter MVP` from contract to endpoint-backed smoke tests.",
            "2. Add a relationship bridge for `Synastry / Ashtakoot` before using matching scores as primary labels.",
            "3. Build `Life Event Graph v1` from local monthly/day scan plus optional VedAstro range-scan evidence.",
            "4. Keep ayanamsa and Shadbala parity under oracle closure before claiming production tuning.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(
    matrix: dict[str, Any],
    *,
    json_path: Path = DEFAULT_JSON_PATH,
    markdown_path: Path = DEFAULT_MARKDOWN_PATH,
) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(matrix, ensure_ascii=False, indent=2) + "\n")
    markdown_path.write_text(render_markdown(matrix) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--write", action="store_true", help="write latest JSON and Markdown snapshots")
    args = parser.parse_args(argv)

    matrix = build_matrix()
    if args.write:
        write_outputs(matrix)
    if args.format == "json":
        print(json.dumps(matrix, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(matrix))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
