#!/usr/bin/env python3
"""Summarize VedAstro/PyJHora/jyotishganit sanity closure status.

This is an audit ledger, not a calculator. It cross-references existing
external evidence and reports which parts are closed, partial, or blocked
without importing PyJHora AGPL code or treating local consistency as truth.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
DEFAULT_DASHA_ORACLE_FILE = "references/oracle/dasha_shadbala_oracle_cases.json"
DEFAULT_TAJIKA_ORACLE_FILE = "references/oracle/tajika_annual_oracle_cases.json"
JYOTISHGANIT_ROOT = ROOT / "references" / "open_source_sources" / "jyotishganit"


def _run_json(command: list[str], *, timeout: int = 120) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        return {
            "status": "blocked",
            "command": command,
            "stderr": completed.stderr.strip(),
            "stdout_excerpt": completed.stdout.strip()[:500],
        }
    try:
        data = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        return {
            "status": "blocked",
            "command": command,
            "reason": f"invalid_json: {exc}",
            "stdout_excerpt": completed.stdout.strip()[:500],
        }
    if isinstance(data, dict):
        return data
    return {"status": "blocked", "command": command, "reason": "json_root_not_object"}


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - exact filesystem errors vary
        return {"status": "blocked", "reason": f"{type(exc).__name__}: {exc}"}
    return data if isinstance(data, dict) else {"status": "blocked", "reason": "json_root_not_object"}


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _vedastro_ledger(oracle_file: str, *, live_official_full_snapshot: bool = False) -> dict[str, Any]:
    boundary = _run_json([PYTHON, "scripts/oracle_boundary_audit.py", "--oracle-file", oracle_file])
    longitude_cases = boundary.get("longitude_cases") if isinstance(boundary.get("longitude_cases"), list) else []
    within_threshold = [
        row for row in longitude_cases
        if isinstance(row, dict) and row.get("within_threshold") is True
    ]
    max_delta = max(
        (float(row.get("max_abs_delta_arcsec", 0.0)) for row in longitude_cases if isinstance(row, dict)),
        default=None,
    )
    boundary_status = "ok" if longitude_cases and len(within_threshold) == len(longitude_cases) else "blocked"

    if live_official_full_snapshot:
        snapshot = _run_json([
            PYTHON,
            "scripts/vedastro_service_adapter.py",
            "--official-full-snapshot",
            "--case",
            "steve_jobs_public_aa",
        ])
    else:
        snapshot = {
            "status": "not_run_default_non_blocking",
            "source_metadata": {
                "official_python_bundle": {
                    "status": "not_run_default_non_blocking",
                },
            },
            "official_chart": {},
        }
    snapshot_status = str(snapshot.get("status") or "blocked")
    source_metadata = snapshot.get("source_metadata") if isinstance(snapshot.get("source_metadata"), dict) else {}
    official_bundle = source_metadata.get("official_python_bundle") if isinstance(source_metadata.get("official_python_bundle"), dict) else {}
    official_chart = snapshot.get("official_chart") if isinstance(snapshot.get("official_chart"), dict) else {}
    official_chart_available = bool(
        isinstance(official_chart.get("planets"), dict)
        and official_chart.get("planets")
        and isinstance(official_chart.get("ascendant"), dict)
        and official_chart.get("ascendant")
    )

    fine_status_ok = snapshot_status in {"ok", "partial"} and official_chart_available
    if fine_status_ok and boundary_status == "ok":
        status = "ok"
        verdict = "official_precision_sanity_passed"
    else:
        status = "blocked"
        verdict = (
            "official_longitude_sanity_passed_but_full_snapshot_blocked"
            if boundary_status == "ok"
            else "official_precision_sanity_blocked"
        )

    return {
        "name": "VedAstro",
        "role": "official_precision_sanity",
        "status": status,
        "verdict": verdict,
        "live_official_full_snapshot": live_official_full_snapshot,
        "fine_calc_blocked": status != "ok",
        "longitude_case_count": len(longitude_cases),
        "longitude_cases_within_threshold": len(within_threshold),
        "max_abs_delta_arcsec": max_delta,
        "snapshot_status": snapshot_status,
        "official_chart_available": official_chart_available,
        "official_python_bundle_status": official_bundle.get("status"),
        "evidence_paths": [
            "references/oracle/dasha_shadbala_oracle_cases.json",
            "scripts/oracle_boundary_audit.py",
            "scripts/vedastro_service_adapter.py",
        ],
        "blocked_reason": None if status == "ok" else (
            "Official fine snapshot is not a stable ok chart, or only longitude sanity is currently closed."
        ),
    }


def _pyjhora_ledger() -> dict[str, Any]:
    manifest_path = ROOT / "references" / "oracle" / "artifacts" / "pyjhora_oracle_artifact_manifest.json"
    manifest = _load_json(manifest_path)
    artifact_count = int(manifest.get("artifact_count") or 0)
    packet_count = int(manifest.get("packet_count") or 0)
    fronts = manifest.get("fronts") if isinstance(manifest.get("fronts"), dict) else {}
    status = "ok" if artifact_count >= 8 and packet_count >= 8 else "partial" if artifact_count else "blocked"
    return {
        "name": "PyJHora",
        "role": "black_box_external_oracle",
        "status": status,
        "verdict": "black_box_artifact_ledger_available" if status != "blocked" else "black_box_artifact_ledger_missing",
        "artifact_count": artifact_count,
        "packet_count": packet_count,
        "fronts": fronts,
        "license_boundary": "black_box_artifacts_only_no_agpl_code_import",
        "evidence_paths": [_relative(manifest_path)],
    }


def _jyotishganit_ledger() -> dict[str, Any]:
    package_init = JYOTISHGANIT_ROOT / "jyotishganit" / "__init__.py"
    license_path = JYOTISHGANIT_ROOT / "LICENSE"
    source_available = package_init.is_file()
    license_text = ""
    if license_path.is_file():
        license_text = license_path.read_text(encoding="utf-8", errors="ignore")[:2000].lower()
    license_name = "MIT" if "mit license" in license_text or "permission is hereby granted" in license_text else "unknown"

    importable = False
    import_error = None
    if source_available:
        spec = importlib.util.spec_from_file_location("jyotishganit", package_init)
        importable = spec is not None
        if not importable:
            import_error = "cannot_build_import_spec"

    benchmark_path = ROOT / "references" / "jyotishganit_benchmark.md"
    status = "ok" if source_available and license_name == "MIT" and benchmark_path.is_file() else "partial" if source_available else "blocked"
    return {
        "name": "jyotishganit",
        "role": "mit_reference_layer",
        "status": status,
        "verdict": "mit_reference_source_available" if status != "blocked" else "mit_reference_source_missing",
        "license": license_name,
        "source_available": source_available,
        "import_spec_available": importable,
        "import_error": import_error,
        "benchmark_available": benchmark_path.is_file(),
        "evidence_paths": [
            _relative(JYOTISHGANIT_ROOT),
            _relative(benchmark_path),
        ],
        "boundary": "MIT reference layer and local comparison asset; not a complete second runtime oracle for every request.",
    }


def _oracle_master(dasha_oracle_file: str, tajika_oracle_file: str) -> dict[str, Any]:
    return _run_json([
        PYTHON,
        "scripts/oracle_closure_master_dashboard.py",
        "--dasha-oracle-file",
        dasha_oracle_file,
        "--tajika-oracle-file",
        tajika_oracle_file,
        "--format",
        "json",
    ])


def build_report(
    dasha_oracle_file: str,
    tajika_oracle_file: str,
    *,
    live_official_full_snapshot: bool = False,
) -> dict[str, Any]:
    vedastro = _vedastro_ledger(
        dasha_oracle_file,
        live_official_full_snapshot=live_official_full_snapshot,
    )
    pyjhora = _pyjhora_ledger()
    jyotishganit = _jyotishganit_ledger()
    master = _oracle_master(dasha_oracle_file, tajika_oracle_file)

    ledgers = {
        "vedastro": vedastro,
        "pyjhora": pyjhora,
        "jyotishganit": jyotishganit,
    }
    blocked = [key for key, value in ledgers.items() if value.get("status") == "blocked"]
    partial = [key for key, value in ledgers.items() if value.get("status") == "partial"]
    ok = [key for key, value in ledgers.items() if value.get("status") == "ok"]
    can_claim_fully_closed = not blocked and not partial and master.get("summary", {}).get("can_claim_global_oracle_closure") is True

    return {
        "scope": "external_official_sanity_oracle_closure",
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "required_oracles": ["VedAstro", "PyJHora", "jyotishganit"],
            "ok_count": len(ok),
            "partial_count": len(partial),
            "blocked_count": len(blocked),
            "ok_oracles": ok,
            "partial_oracles": partial,
            "blocked_oracles": blocked,
            "external_verified_tasks": master.get("summary", {}).get("external_verified_tasks"),
            "total_tasks": master.get("summary", {}).get("total_tasks"),
            "open_tasks": master.get("summary", {}).get("open_tasks"),
            "live_official_full_snapshot": live_official_full_snapshot,
        },
        "oracle_ledger": ledgers,
        "master_oracle_dashboard": {
            "summary": master.get("summary", {}),
            "fronts": master.get("fronts", {}),
        },
        "honesty_boundary": {
            "can_claim_fully_closed": can_claim_fully_closed,
            "can_claim_high_rigor_with_blocks": bool(pyjhora.get("status") in {"ok", "partial"} and jyotishganit.get("status") in {"ok", "partial"}),
            "blocked_reason": (
                None if can_claim_fully_closed else
                "At least one official precision/oracle layer is partial or blocked; report must expose blocked rows instead of claiming full closure."
            ),
            "license_boundary": "PyJHora is black-box evidence only; jyotishganit MIT assets may be referenced/reused within existing project policy.",
        },
        "next_actions": [
            "Run --live-official-full-snapshot when foreground VedAstro budget/network credentials are available, then promote VedAstro only if the full official chart is stable.",
            "Keep PyJHora as artifact-backed oracle evidence; do not import AGPL implementation code.",
            "If a report needs full closure language, require all oracle ledger rows to be ok and the master oracle dashboard open_tasks to be 0.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# External Official Sanity / Oracle Closure",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- ok_count: `{summary['ok_count']}`",
        f"- partial_count: `{summary['partial_count']}`",
        f"- blocked_count: `{summary['blocked_count']}`",
        f"- total_tasks: `{summary.get('total_tasks')}`",
        f"- external_verified_tasks: `{summary.get('external_verified_tasks')}`",
        f"- open_tasks: `{summary.get('open_tasks')}`",
        "",
        "## Oracle Ledger",
        "",
        "| oracle | status | role | verdict |",
        "|---|---|---|---|",
    ]
    for key, row in report["oracle_ledger"].items():
        lines.append(f"| `{key}` | `{row.get('status')}` | `{row.get('role')}` | `{row.get('verdict')}` |")
    lines.extend([
        "",
        "## Honesty Boundary",
        "",
        f"- can_claim_fully_closed: `{str(report['honesty_boundary']['can_claim_fully_closed']).lower()}`",
        f"- can_claim_high_rigor_with_blocks: `{str(report['honesty_boundary']['can_claim_high_rigor_with_blocks']).lower()}`",
        f"- blocked_reason: {report['honesty_boundary']['blocked_reason']}",
        "",
        "## Next Actions",
        "",
    ])
    lines.extend(f"- {item}" for item in report["next_actions"])
    lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit VedAstro/PyJHora/jyotishganit sanity closure")
    parser.add_argument("--dasha-oracle-file", default=DEFAULT_DASHA_ORACLE_FILE)
    parser.add_argument("--tajika-oracle-file", default=DEFAULT_TAJIKA_ORACLE_FILE)
    parser.add_argument(
        "--live-official-full-snapshot",
        action="store_true",
        help="Run the heavy VedAstro official full snapshot probe; default stays non-blocking for CI.",
    )
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--output")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_report(
        args.dasha_oracle_file,
        args.tajika_oracle_file,
        live_official_full_snapshot=args.live_official_full_snapshot,
    )
    text = json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else render_markdown(report)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
