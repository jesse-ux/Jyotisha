#!/usr/bin/env python3
"""Generate a public benchmark dashboard for Jyotish skill readiness."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def _run_json(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=90,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    return json.loads(completed.stdout)


def _oracle_readiness(oracle_file: str) -> dict[str, Any]:
    queue = _run_json([PYTHON, "scripts/oracle_collection_queue.py", "--oracle-file", oracle_file, "--format", "json"])
    with tempfile.NamedTemporaryFile("w+", suffix=".json", encoding="utf-8", delete=True) as fh:
        json.dump(queue, fh, ensure_ascii=False)
        fh.flush()
        validation = _run_json([PYTHON, "scripts/oracle_evidence_validator.py", "--queue-file", fh.name])
    summary = validation["summary"]
    return {
        "total_packets": summary["total_packets"],
        "valid_packets": summary["valid_packets"],
        "ready_for_calibration": summary["ready_for_calibration"],
        "production_tuning_allowed": summary["production_tuning_allowed"],
        "all_packets_external_verified": summary["all_packets_external_verified"],
        "queue_status_counts": queue["summary"].get("by_status", {}),
        "boundary": validation["boundary"],
    }


def _dasha_readiness(oracle_file: str) -> dict[str, Any]:
    queue = _run_json([PYTHON, "scripts/oracle_collection_queue.py", "--oracle-file", oracle_file, "--format", "json"])
    with tempfile.NamedTemporaryFile("w+", suffix=".json", encoding="utf-8", delete=True) as fh:
        json.dump(queue, fh, ensure_ascii=False)
        fh.flush()
        validation = _run_json([PYTHON, "scripts/dasha_oracle_evidence_validator.py", "--queue-file", fh.name])
    return validation["summary"]


def _shadbala_readiness(oracle_file: str) -> dict[str, Any]:
    report = _run_json([
        PYTHON,
        "scripts/shadbala_oracle_closure_status.py",
        "--oracle-file",
        oracle_file,
        "--format",
        "json",
    ])
    return report["summary"]


def _boundary_audit(oracle_file: str) -> dict[str, Any]:
    report = _run_json([PYTHON, "scripts/oracle_boundary_audit.py", "--oracle-file", oracle_file])
    summary = report["summary"]
    return {
        "template_cases": summary["template_cases"],
        "external_verified_template_cases": summary.get("external_verified_template_cases", 0),
        "dasha_cases": summary["dasha_cases"],
        "longitude_cases": summary["longitude_cases"],
        "shadbala_cases": summary["shadbala_cases"],
        "production_tuning_recommended": summary["production_tuning_recommended"],
        "open_items": summary["open_items"],
        "template_comparison_count": len(report.get("template_comparisons", [])),
    }


def _pyjhora_blackbox_assets() -> dict[str, Any]:
    return _run_json([PYTHON, "scripts/generate_pyjhora_oracle_artifact_manifest.py"])


def build_dashboard(oracle_file: str) -> dict[str, Any]:
    capability = _run_json([PYTHON, "scripts/audit_capabilities.py", "--mode", "validate"])
    oracle = _oracle_readiness(oracle_file)
    boundary = _boundary_audit(oracle_file)
    dasha = _dasha_readiness(oracle_file)
    shadbala = _shadbala_readiness(oracle_file)
    pyjhora_assets = _pyjhora_blackbox_assets()
    global_first_gap = (
        f"Dasha-only external oracle readiness is {dasha['valid_dasha_packets']}/"
        f"{dasha['total_dasha_packets']}; Shadbala external absolute-value readiness is "
        f"{shadbala['external_verified_shadbala_tasks']}/{shadbala['shadbala_task_count']}; "
        f"PyJHora black-box assets are {pyjhora_assets['artifact_count']} artifacts / "
        f"{pyjhora_assets['packet_count']} packets; "
        "public long-term benchmark history is not yet comparable to the strongest "
        "global open-source projects."
    )
    can_claim_global_first = bool(
        capability.get("valid")
        and oracle["production_tuning_allowed"]
        and boundary["production_tuning_recommended"]
    )
    return {
        "scope": "public_jyotish_benchmark_dashboard",
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "technique_count": capability["technique_count"],
            "capability_valid": capability["valid"],
            "problem_count": capability["problem_count"],
            "status_counts": capability["status_counts"],
        },
        "oracle_readiness": oracle,
        "dasha_oracle_readiness": dasha,
        "shadbala_oracle_readiness": shadbala,
        "pyjhora_blackbox_assets": pyjhora_assets,
        "boundary_audit": boundary,
        "public_claim": {
            "can_claim_global_first": can_claim_global_first,
            "reason": (
                "Do not claim global first until Dasha/Shadbala external oracle packets are valid, "
                "production tuning is allowed, and public benchmark history is stable."
            ),
        },
        "global_first_gap": global_first_gap,
        "next_actions": [
            "Expand public benchmark history instead of over-claiming from the current closed target set.",
            "Run oracle_boundary_audit.py to inspect Dasha/Shadbala deltas without tuning constants.",
            "Regenerate Tajika/Dasha/Shadbala status boards after each new external packet batch.",
            "Publish this dashboard after each validated sample batch so public claim boundaries stay conservative.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    oracle = report["oracle_readiness"]
    dasha = report["dasha_oracle_readiness"]
    shadbala = report["shadbala_oracle_readiness"]
    boundary = report["boundary_audit"]
    claim = report["public_claim"]
    lines = [
        "# Public Jyotish Benchmark Dashboard",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        "## Capability Registry",
        "",
        f"- technique_count: `{report['summary']['technique_count']}`",
        f"- capability_valid: `{str(report['summary']['capability_valid']).lower()}`",
        f"- problem_count: `{report['summary']['problem_count']}`",
        "",
        "## Dasha/Shadbala Oracle Readiness",
        "",
        f"- total_packets: `{oracle['total_packets']}`",
        f"- valid_packets: `{oracle['valid_packets']}`",
        f"- ready_for_calibration: `{oracle['ready_for_calibration']}`",
        f"- production_tuning_allowed: `{str(oracle['production_tuning_allowed']).lower()}`",
        f"- valid_dasha_packets: `{dasha['valid_dasha_packets']}`",
        f"- total_dasha_packets: `{dasha['total_dasha_packets']}`",
        f"- external_verified_shadbala_tasks: `{shadbala['external_verified_shadbala_tasks']}`",
        f"- shadbala_task_count: `{shadbala['shadbala_task_count']}`",
        "",
        "## PyJHora Black-Box Assets",
        "",
        f"- artifact_count: `{report['pyjhora_blackbox_assets']['artifact_count']}`",
        f"- packet_count: `{report['pyjhora_blackbox_assets']['packet_count']}`",
        f"- dasha_artifacts: `{report['pyjhora_blackbox_assets']['fronts']['dasha']['artifact_count']}`",
        f"- shadbala_artifacts: `{report['pyjhora_blackbox_assets']['fronts']['shadbala']['artifact_count']}`",
        f"- tajika_sahams_artifacts: `{report['pyjhora_blackbox_assets']['fronts']['tajika_sahams']['artifact_count']}`",
        "",
        "## Boundary Audit",
        "",
        f"- external_verified_template_cases: `{boundary['external_verified_template_cases']}`",
        f"- template_comparison_count: `{boundary['template_comparison_count']}`",
        f"- production_tuning_recommended: `{str(boundary['production_tuning_recommended']).lower()}`",
        "",
        "## Global First Claim",
        "",
        f"- can_claim_global_first: `{str(claim['can_claim_global_first']).lower()}`",
        f"- reason: {claim['reason']}",
        "",
        "## Remaining Gap",
        "",
        report["global_first_gap"],
        "",
        "## Next Actions",
        "",
    ]
    lines.extend(f"- {item}" for item in report["next_actions"])
    lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate public Jyotish benchmark dashboard")
    parser.add_argument("--oracle-file", default="references/oracle/dasha_shadbala_oracle_cases.json")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--output", help="Optional output path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_dashboard(args.oracle_file)
    text = json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else render_markdown(report)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
