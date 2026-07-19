#!/usr/bin/env python3
"""Audit local Jyotish project fragments against real product surfaces.

The capability registry can say that a technique is covered, but this audit
checks whether the claim has a concrete path through CLI, API, frontend source,
tests, or a real file. It is intentionally stdlib-only so it can run inside the
normal quality gate.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "references" / "technique_registry.json"
SCRIPTS_DIR = ROOT / "scripts"
APP_DIR = ROOT / "jyotish-app"
TESTS_DIR = ROOT / "tests"
OPEN_SOURCE_DIR = ROOT / "references" / "open_source_sources"

API_COMMAND_MAP = {
    "chart": "/api/chart",
    "kp": "/api/kp",
    "prashna": "/api/prashna",
    "synastry": "/api/synastry",
    "ashtakoot": "/api/synastry",
    "dasha": "/api/dasha",
    "remedies": "/api/remedies",
    "sade_sati": "/api/sade_sati",
    "pancha_mahapurusha": "/api/pancha_mahapurusha",
    "career": "/api/career",
    "relationship": "/api/relationship",
    "full-reading": "/api/chart",
    "tajika": "/api/annual",
    "solar-return": "/api/annual",
    "muhurta": "/api/muhurta",
    "panchanga-range": "/api/panchanga_range",
    "bhava-chalit": "/api/bhava_chalit",
    "sudarshana": "/api/sudarshana",
    "nakshatra-full": "/api/nakshatra_full",
    "varga-full": "/api/varga_full",
    "jaimini": "/api/jaimini",
    "ashtakavarga": "/api/ashtakavarga",
    "shadbala": "/api/shadbala",
    "yoga": "/api/yogas",
    "aspects": "/api/aspects",
    "rectification": "/api/rectification_gate",
    "case-validation": "/api/case_validation",
    "deep-varga-avastha": "/api/deep_varga_avastha",
    "divisional-yoga": "/api/divisional_yoga",
    "kakshya": "/api/kakshya",
    "bhava-bala": "/api/bhava_bala",
    "transit-trigger": "/api/transit",
    "audit-capabilities": "/api/capability_audit",
    "thematic-report": "/api/thematic_report",
    "high-rigor-workflow": "/api/high_rigor_workflow",
    "report-artifact": "/api/report_artifact",
}

FRONTEND_MARKERS = {
    "remedies": ["remedies-section", "remedies.evidence_chain"],
    "career": ["computeCareer", "事业分析", "career analysis"],
    "relationship": ["computeRelationship", "感情分析", "relationship analysis"],
    "kp": ["computeKP", "tab-kp", "kp-section"],
    "prashna": ["computePrashna", "tab-prashna"],
    "synastry": ["computeSynastry", "tab-synastry"],
    "muhurta": ["computeMuhurta", "muhurta"],
    "panchanga-range": ["computePanchangaRange", "panchanga-range"],
    "solar-return": ["computeAnnual", "varshaphala", "tajika"],
    "tajika": ["computeAnnual", "varshaphala", "tajika"],
    "bhava-bala": ["computeBhavaBala", "bhava bala"],
    "divisional-yoga": ["computeDivisionalYoga", "divisional yoga"],
    "rectification": ["computeRectificationGate", "rectification"],
    "case-validation": ["computeCaseValidation", "mevg", "case validation"],
    "deep-varga-avastha": ["deepVargaAvastha", "deep_varga_avastha", "Sayanadi/Shayanadi", "D24/D30/D60"],
    "transit-trigger": ["computeTransitTriggers", "transit trigger"],
    "kakshya": ["computeKakshya", "kakshya"],
}

SCRIPT_IGNORE = {
    "__init__.py",
    "_compute_one_chart.py",
    "add_d60_to_test_charts.py",
    "add_high_confidence_yogas_batch1.py",
    "analyze_yoga_errors.py",
    "audit_capabilities.py",
    "audit_fragments.py",
    "benchmark_yoga_coverage.py",
    "build_planet_positions_60.py",
    "build_standard_test_charts.py",
    "chart_renderer.py",
    "generate_yoga_rules.py",
    "hermes_bridge.py",
    "jyotish_api_server.py",
    "jyotish_engine.py",
    "oss_monitor.py",
    "run_quality_gate.py",
    "validate.py",
    "validate_bphs_invariants.py",
    "validate_logic_v2.py",
    "validate_yoga_accuracy.py",
}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def load_registry() -> dict[str, Any]:
    return json.loads(read_text(REGISTRY_PATH))


def scan_engine_commands() -> set[str]:
    text = read_text(SCRIPTS_DIR / "jyotish_engine.py")
    return set(re.findall(r"add_parser\(['\"]([^'\"]+)['\"]", text))


def scan_api_endpoints() -> set[str]:
    text = read_text(SCRIPTS_DIR / "jyotish_api_server.py")
    return set(re.findall(r"path == ['\"](/api/[^'\"]+)['\"]", text))


def scan_frontend() -> dict[str, Any]:
    text_parts: list[str] = []
    files: list[str] = []
    if APP_DIR.exists():
        for path in APP_DIR.rglob("*"):
            if any(part in {"node_modules", "dist", ".vite"} for part in path.parts):
                continue
            if path.suffix not in {".js", ".html", ".css"}:
                continue
            files.append(str(path.relative_to(ROOT)))
            text_parts.append(read_text(path))
    text = "\n".join(text_parts)
    return {
        "file_count": len(files),
        "api_paths": sorted(set(re.findall(r"['\"](/api/[^'\"]+)['\"]", text))),
        "api_functions": sorted(set(re.findall(r"async function (compute[A-Z][A-Za-z0-9_]*|getCapabilityAudit)", text))),
        "source_text": text,
    }


def scan_test_text() -> str:
    parts: list[str] = []
    if TESTS_DIR.exists():
        for path in TESTS_DIR.rglob("*.py"):
            parts.append(read_text(path))
    return "\n".join(parts)


def git_untracked() -> list[str]:
    try:
        completed = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if completed.returncode != 0:
        return []
    return sorted(line for line in completed.stdout.splitlines() if line)


def git_lost_found() -> list[str]:
    root = ROOT / ".git" / "lost-found"
    if not root.exists():
        return []
    return sorted(str(path.relative_to(ROOT)) for path in root.rglob("*") if path.is_file())


def first_token_path(value: str) -> str:
    return value.split()[0] if value else value


def output_path_exists(path: str) -> tuple[bool, str]:
    if path.startswith("scripts/"):
        rel = first_token_path(path)
        if ":" in rel:
            rel = rel.split(":", 1)[0]
        elif ".py." in rel:
            rel = rel.split(".py.", 1)[0] + ".py"
        return (ROOT / rel).exists(), rel
    if path.endswith(".py"):
        return (ROOT / path).exists(), path
    return True, path


def command_surface(command: str, engine_commands: set[str], api_endpoints: set[str]) -> str | None:
    if command in engine_commands:
        return "engine"
    endpoint = API_COMMAND_MAP.get(command)
    if endpoint and endpoint in api_endpoints:
        return "api"
    if command.startswith("scripts/") and (ROOT / first_token_path(command)).exists():
        return "script"
    return None


def frontend_reaches(command: str, frontend: dict[str, Any]) -> bool:
    endpoint = API_COMMAND_MAP.get(command)
    if endpoint and endpoint in frontend["api_paths"]:
        return True
    source = frontend["source_text"].lower()
    markers = FRONTEND_MARKERS.get(command, [])
    return any(marker.lower() in source for marker in markers)


def registry_script_refs(registry: dict[str, Any]) -> set[str]:
    refs: set[str] = set()
    for technique in registry.get("techniques", {}).values():
        for field in ("commands", "output_paths"):
            for value in technique.get(field, []):
                if isinstance(value, str) and value.startswith("scripts/"):
                    refs.add(Path(first_token_path(value)).name)
    return refs


def source_referenced_scripts(*texts: str) -> set[str]:
    combined = "\n".join(texts)
    refs: set[str] = set()
    for path in SCRIPTS_DIR.glob("*.py"):
        stem = path.stem
        if re.search(rf"\b(import|from)\s+(?:scripts\.)?{re.escape(stem)}\b", combined):
            refs.add(path.name)
        if path.name in combined or stem in combined:
            refs.add(path.name)
    return refs


def transitive_source_referenced_scripts(*texts: str) -> set[str]:
    """Follow local script imports so indirect runtime modules are not fragments."""
    combined = "\n".join(texts)
    names = set(re.findall(r"(?:from|import)\s+(?:scripts\.)?([A-Za-z_][A-Za-z0-9_]*)", combined))
    names |= set(re.findall(r"_load_local_module\(['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]\)", combined))
    referenced = {f"{name}.py" for name in names if (SCRIPTS_DIR / f"{name}.py").exists()}
    pending = list(referenced)
    visited: set[str] = set()
    while pending:
        filename = pending.pop()
        if filename in visited:
            continue
        visited.add(filename)
        path = SCRIPTS_DIR / filename
        if not path.exists():
            continue
        text = read_text(path)
        child_names = set(re.findall(r"(?:from|import)\s+(?:scripts\.)?([A-Za-z_][A-Za-z0-9_]*)", text))
        child_names |= set(re.findall(r"_load_local_module\(['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]\)", text))
        for child in {f"{name}.py" for name in child_names if (SCRIPTS_DIR / f"{name}.py").exists()}:
            if child not in referenced:
                referenced.add(child)
                pending.append(child)
    return referenced


def find_script_fragments(registry: dict[str, Any], frontend: dict[str, Any], test_text: str) -> dict[str, Any]:
    api_text = read_text(SCRIPTS_DIR / "jyotish_api_server.py")
    engine_text = read_text(SCRIPTS_DIR / "jyotish_engine.py")
    app_text = frontend["source_text"]
    referenced = set(SCRIPT_IGNORE)
    referenced |= registry_script_refs(registry)
    referenced |= source_referenced_scripts(api_text, engine_text, app_text, test_text)
    referenced |= transitive_source_referenced_scripts(api_text, engine_text, app_text, test_text)
    candidates = []
    for path in sorted(SCRIPTS_DIR.glob("*.py")):
        if path.name in referenced:
            continue
        candidates.append(path.name)
    return {
        "ignored_count": len(SCRIPT_IGNORE),
        "referenced_count": len(referenced),
        "candidate_count": len(candidates),
        "candidates": candidates,
    }


def list_open_source_sources() -> list[dict[str, Any]]:
    if not OPEN_SOURCE_DIR.exists():
        return []
    result = []
    for path in sorted(p for p in OPEN_SOURCE_DIR.iterdir() if p.is_dir()):
        files = [p for p in path.rglob("*") if p.is_file() and ".git" not in p.parts]
        result.append({
            "name": path.name,
            "path": str(path.relative_to(ROOT)),
            "file_count": len(files),
            "has_license": any(p.name.lower() in {"license", "license.md", "licence"} for p in files),
            "has_readme": any(p.name.lower() == "readme.md" for p in files),
        })
    return result


def audit() -> dict[str, Any]:
    registry = load_registry()
    techniques = registry.get("techniques", {})
    engine_commands = scan_engine_commands()
    api_endpoints = scan_api_endpoints()
    frontend = scan_frontend()
    test_text = scan_test_text()

    problems: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []

    for tech_id, technique in sorted(techniques.items()):
        status = technique.get("status")
        commands = [c for c in technique.get("commands", []) if isinstance(c, str)]
        output_paths = [p for p in technique.get("output_paths", []) if isinstance(p, str)]
        command_surfaces = {command: command_surface(command, engine_commands, api_endpoints) for command in commands}
        frontend_commands = [command for command in commands if frontend_reaches(command, frontend)]

        if status in {"covered", "complete"} and not commands:
            problems.append({
                "kind": "covered_without_command",
                "technique_id": tech_id,
                "message": "covered/complete techniques must declare at least one real command or API command",
            })

        for command, surface in command_surfaces.items():
            if surface is None:
                problems.append({
                    "kind": "unreachable_command",
                    "technique_id": tech_id,
                    "command": command,
                    "message": "registry command is not found in CLI commands, API endpoints, or script files",
                })

        for path in output_paths:
            ok, checked = output_path_exists(path)
            if not ok:
                problems.append({
                    "kind": "missing_output_path",
                    "technique_id": tech_id,
                    "output_path": path,
                    "checked_path": checked,
                })

        api_commands = [cmd for cmd, surface in command_surfaces.items() if surface == "api"]
        if api_commands and not frontend_commands:
            warnings.append({
                "kind": "api_without_frontend_marker",
                "technique_id": tech_id,
                "commands": api_commands,
                "message": "API exists, but no obvious frontend bridge/topic marker was detected",
            })

        rows.append({
            "id": tech_id,
            "status": status,
            "commands": commands,
            "command_surfaces": command_surfaces,
            "frontend_commands": frontend_commands,
            "output_paths": output_paths,
        })

    fragments = find_script_fragments(registry, frontend, test_text)
    open_sources = list_open_source_sources()
    untracked = git_untracked()
    lost_found = git_lost_found()

    return {
        "valid": not problems,
        "problem_count": len(problems),
        "warning_count": len(warnings),
        "registry": {
            "technique_count": len(techniques),
            "version": registry.get("version"),
        },
        "surfaces": {
            "engine_command_count": len(engine_commands),
            "engine_commands": sorted(engine_commands),
            "api_endpoint_count": len(api_endpoints),
            "api_endpoints": sorted(api_endpoints),
            "frontend_file_count": frontend["file_count"],
            "frontend_api_paths": frontend["api_paths"],
            "frontend_api_functions": frontend["api_functions"],
        },
        "fragments": fragments,
        "open_source_sources": {
            "source_count": len(open_sources),
            "sources": open_sources,
        },
        "workspace_residue": {
            "untracked_count": len(untracked),
            "untracked_files": untracked,
            "git_lost_found_count": len(lost_found),
            "git_lost_found_files": lost_found,
        },
        "problems": problems,
        "warnings": warnings,
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Jyotish registry, product surfaces, and local fragments")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when hard problems are found")
    args = parser.parse_args()
    result = audit()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if args.strict and not result["valid"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
