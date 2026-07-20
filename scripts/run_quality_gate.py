#!/usr/bin/env python3
"""Run the Jyotish skill quality gate used by local development and CI."""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from local_env import load_local_env  # noqa: E402

load_local_env(ROOT)
APP = ROOT / "frontend"
PYTHON = sys.executable

COMPILE_DIRS = [
    ROOT / "scripts",
    ROOT / "jyotish_vedic",
]

EXTRA_COMPILE_TARGETS = [
    ROOT / "mcp_server.py",
    ROOT / "scripts" / "audit_fragments.py",
    ROOT / "scripts" / "character_level_inventory_manifest.py",
    ROOT / "scripts" / "dasha_reference_audit.py",
    ROOT / "scripts" / "external_oracle_sanity_closure.py",
    ROOT / "scripts" / "interpretation_source_inventory_gate.py",
    ROOT / "scripts" / "oracle_boundary_audit.py",
    ROOT / "scripts" / "oracle_collection_queue.py",
    ROOT / "scripts" / "oracle_evidence_validator.py",
    ROOT / "scripts" / "sync_final_evidence_packet_status.py",
    ROOT / "tests" / "run_golden_cases.py",
    ROOT / "tests" / "run_real_case_revalidation.py",
]

CORE_PYTEST_TARGETS = [
    "tests/test_cli_smoke.py",
    "tests/test_api_server_security.py",
    "tests/test_jaimini.py",
    "tests/test_shadbala_complete.py",
    "tests/test_transit_trigger.py",
    "tests/test_oracle_collection_queue.py",
    "tests/test_oracle_evidence_validator.py",
    "tests/test_external_oracle_sanity_closure.py",
]

RUNTIME_TRUTH_PYTEST_TARGETS = [
    "tests/test_api_server_security.py::test_high_rigor_vedastro_official_summary_passes_through_contract_fields",
    "tests/test_api_server_security.py::test_high_rigor_vedastro_official_summary_exposes_top_reader_contract_from_full_snapshot",
    "tests/test_vedastro_external_technique_evidence.py::test_strict_workflow_uses_shared_consultation_executor",
    "tests/test_vedastro_runtime_mode_diagnostics.py",
    "tests/test_interpretation_source_inventory_gate.py::test_quality_gate_runs_interpretation_source_inventory_gate",
    "tests/test_interpretation_source_runtime_coverage.py",
    "tests/test_final_jhora_evidence_packet_acceptance.py",
]

RELEASE_CRITICAL_UNTRACKED_PATHS = [
    "docs/research/desktop_packaging_spike_2026_06_23.md",
    "docs/research/ephemeris_abstraction_feasibility_2026_06_23.md",
    "docs/research/ephemeris_adapter_contract_2026_06_23.md",
    "docs/research/ephemeris_candidate_adapter_spike_2026_06_23.md",
    "docs/research/open_source_scan_2026_06_22.md",
    "docs/research/product_gap_matrix_2026_06_22.md",
    "docs/research/whole_machine_git_audit_2026_06_23.md",
    "findings.md",
    "progress.md",
    "references/oracle/dasha_shadbala_oracle_cases.json",
    "scripts/audit_fragments.py",
    "scripts/deep_varga_avastha.py",
    "scripts/dasha_reference_audit.py",
    "scripts/ephemeris_adapter_contract.py",
    "scripts/ephemeris_backend_probe.py",
    "scripts/ephemeris_candidate_adapter_spike.py",
    "scripts/oracle_boundary_audit.py",
    "scripts/oracle_collection_queue.py",
    "scripts/oracle_evidence_validator.py",
    "task_plan.md",
    "tests/test_api_server_security.py",
    "tests/test_dasha_reference_audit.py",
    "tests/test_deep_varga_avastha.py",
    "tests/test_oracle_boundary_audit.py",
    "tests/test_oracle_collection_queue.py",
    "tests/test_oracle_evidence_validator.py",
]

QUALITY_GATE_PROFILES = {
    "quick": {
        "skip_slow": True,
        "skip_yoga_logic": True,
        "skip_frontend_runtime": False,
        "check_release_hygiene": False,
        "skip_real_cases": True,
        "skip_dasha_audit": True,
        "skip_oracle_audit": True,
        "skip_local_accuracy_report": True,
        "skip_vedastro_live": True,
    },
    "browser": {
        "skip_slow": True,
        "skip_yoga_logic": True,
        "skip_frontend_runtime": False,
        "check_release_hygiene": False,
        "skip_real_cases": True,
        "skip_dasha_audit": True,
        "skip_oracle_audit": True,
        "skip_local_accuracy_report": True,
        "skip_vedastro_live": True,
    },
    "release": {
        "skip_slow": False,
        "skip_yoga_logic": False,
        "skip_frontend_runtime": False,
        "check_release_hygiene": True,
        "skip_real_cases": False,
        "skip_dasha_audit": False,
        "skip_oracle_audit": False,
        "skip_local_accuracy_report": False,
        "skip_vedastro_live": True,
    },
    "accuracy": {
        "skip_slow": True,
        "skip_yoga_logic": False,
        "skip_frontend_runtime": True,
        "check_release_hygiene": False,
        "skip_real_cases": False,
        "skip_dasha_audit": False,
        "skip_oracle_audit": False,
        "skip_local_accuracy_report": False,
        "skip_vedastro_live": True,
    },
    "vedastro-live": {
        "skip_slow": True,
        "skip_yoga_logic": True,
        "skip_frontend_runtime": True,
        "check_release_hygiene": False,
        "skip_real_cases": True,
        "skip_dasha_audit": True,
        "skip_oracle_audit": True,
        "skip_local_accuracy_report": True,
        "skip_vedastro_live": False,
    },
    "runtime-truth": {
        "skip_slow": True,
        "skip_yoga_logic": True,
        "skip_frontend_runtime": True,
        "check_release_hygiene": False,
        "skip_real_cases": True,
        "skip_dasha_audit": True,
        "skip_oracle_audit": True,
        "skip_local_accuracy_report": True,
        "skip_vedastro_live": True,
    },
}

DASHA_REFERENCE_AUDIT_CMD = [
    PYTHON,
    "scripts/dasha_reference_audit.py",
    "--year",
    "REDACTED_YEAR",
    "--month",
    "4",
    "--day",
    "17",
    "--hour",
    "14",
    "--minute",
    "45",
    "--second",
    "20",
    "--lat",
    "36.466667",
    "--lon",
    "114.2",
    "--tz",
    "8",
    "--target-start-date",
    "1986-05-18",
    "--target-source",
    "private_chart_reference.pdf",
]

ORACLE_BOUNDARY_AUDIT_CMD = [
    PYTHON,
    "scripts/oracle_boundary_audit.py",
    "--oracle-file",
    "references/oracle/dasha_shadbala_oracle_cases.json",
]

EXTERNAL_ORACLE_SANITY_CLOSURE_CMD = [
    PYTHON,
    "scripts/external_oracle_sanity_closure.py",
    "--format",
    "json",
]

ORACLE_COLLECTION_QUEUE_CMD = [
    PYTHON,
    "scripts/oracle_collection_queue.py",
    "--oracle-file",
    "references/oracle/dasha_shadbala_oracle_cases.json",
    "--format",
    "json",
]
ORACLE_COLLECTION_QUEUE_EXPECTED_FIELDS = ["evidence_packet", "capture_id", "target_fields"]

ORACLE_EVIDENCE_VALIDATOR_CMD = [
    PYTHON,
    "scripts/oracle_evidence_validator.py",
    "--queue-file",
    "{queue_file}",
]


def tail_text(text: str, *, limit: int = 2400) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return f"...\n{text[-limit:]}"


def extract_json_payload(text: str) -> dict:
    text = text.strip()
    if not text:
        return {}
    for start in [text.find("{"), text.rfind("{")]:
        if start < 0:
            continue
        try:
            payload = json.loads(text[start:])
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    return {}


def format_failure_summary(
    step: str,
    cmd: list[str],
    returncode: int,
    *,
    stdout: str = "",
    stderr: str = "",
    cwd: Path = ROOT,
) -> str:
    combined_payload = extract_json_payload(stderr) or extract_json_payload(stdout)
    reason = combined_payload.get("reason") if isinstance(combined_payload, dict) else None
    snapshot = combined_payload.get("process_snapshot") if isinstance(combined_payload, dict) else None
    lines = [
        "",
        "== Quality gate failed ==",
        f"step: {step}",
        f"exit code: {returncode}",
        f"cwd: {cwd.relative_to(ROOT) if cwd != ROOT else '.'}",
        f"command: {' '.join(cmd)}",
    ]
    if reason:
        lines.append(f"reason: {reason}")
    if snapshot:
        lines.append(f"process_snapshot: {json.dumps(snapshot, ensure_ascii=False)}")
    if stdout.strip():
        lines.append(f"stdout tail:\n{tail_text(stdout)}")
    if stderr.strip():
        lines.append(f"stderr tail:\n{tail_text(stderr)}")
    lines.extend([
        "普通用户启动路径:",
        "1. 本地 API 服务：.venv/bin/python scripts/jyotish_api_server.py --host 127.0.0.1 --port 5200",
        "2. 网页服务：npm run dev --prefix frontend",
        "3. Open http://127.0.0.1:3000 and verify /api/health.",
        "Next action: Run the focused command above, then rerun the affected Python or Next.js check.",
        "",
    ])
    return "\n".join(lines)


def run(cmd: list[str], *, optional: bool = False, step: str | None = None, cwd: Path = ROOT) -> bool:
    label = step or " ".join(cmd[:2])
    print(f"\n$ {' '.join(cmd)}")
    completed = subprocess.run(cmd, cwd=cwd, text=True)
    if completed.returncode == 0:
        return True
    if optional:
        print(f"Optional step failed with exit code {completed.returncode}; continuing.")
        return False
    print(
        format_failure_summary(label, cmd, completed.returncode, stdout="", stderr="", cwd=cwd),
        file=sys.stderr,
    )
    raise SystemExit(completed.returncode)


def run_oracle_collection_queue_and_validator() -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as handle:
        queue_path = Path(handle.name)
    try:
        print(f"\n$ {' '.join(ORACLE_COLLECTION_QUEUE_CMD)}")
        completed = subprocess.run(ORACLE_COLLECTION_QUEUE_CMD, cwd=ROOT, text=True, capture_output=True)
        if completed.stdout:
            print(completed.stdout, end="" if completed.stdout.endswith("\n") else "\n")
        if completed.stderr:
            print(completed.stderr, end="" if completed.stderr.endswith("\n") else "\n", file=sys.stderr)
        if completed.returncode != 0:
            print(
                format_failure_summary(
                    "oracle_collection_queue",
                    ORACLE_COLLECTION_QUEUE_CMD,
                    completed.returncode,
                    stdout=completed.stdout,
                    stderr=completed.stderr,
                ),
                file=sys.stderr,
            )
            raise SystemExit(completed.returncode)
        queue_path.write_text(completed.stdout, encoding="utf-8")
        validator_cmd = [part if part != "{queue_file}" else str(queue_path) for part in ORACLE_EVIDENCE_VALIDATOR_CMD]
        run(validator_cmd, step="oracle_evidence_validator")
    finally:
        with contextlib.suppress(FileNotFoundError):
            queue_path.unlink()


def git_untracked_files() -> set[str]:
    completed = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(
            format_failure_summary(
                "release_hygiene_check",
                ["git", "ls-files", "--others", "--exclude-standard"],
                completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
            )
        )
    return {line.strip() for line in completed.stdout.splitlines() if line.strip()}


def release_hygiene_check(require_external_parity: bool = False) -> None:
    print("\n== Release hygiene check ==")
    untracked = git_untracked_files()
    critical = [path for path in RELEASE_CRITICAL_UNTRACKED_PATHS if path in untracked]
    if critical:
        payload = {
            "reason": "release_critical_untracked_files",
            "untracked_count": len(critical),
            "untracked_files": critical,
            "next_action": "Stage or commit these product files before running the release profile.",
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
        raise SystemExit(1)
    run([PYTHON, "scripts/public_release_privacy_scan.py", "--json"])
    run([PYTHON, "scripts/report_renderer_isolation_poc.py", "--strict"])
    parity_command = [PYTHON, "scripts/three_engine_parity_replay_validator.py", "references/oracle/three_engine_parity_replay_manifest.json"]
    if require_external_parity:
        parity_command.append("--require-pass")
    run(parity_command)
    print("release_hygiene_check ok: no release-critical product files are untracked")


def run_vedastro_live_smoke() -> None:
    print("\n== VedAstro live adapter smoke ==")
    endpoint = os.environ.get("VEDASTRO_API_ENDPOINT", "").strip()
    network_enabled = os.environ.get("VEDASTRO_ENABLE_NETWORK", "").strip().lower() in {"1", "true", "yes"}
    if not endpoint or not network_enabled:
        print(json.dumps({
            "status": "blocked",
            "reason": "vedastro_live_endpoint_or_network_flag_missing",
            "required_env": {
                "endpoint": "VEDASTRO_API_ENDPOINT",
                "network": "VEDASTRO_ENABLE_NETWORK",
            },
            "boundary": "Default CI stays deterministic; configure both env vars to run a real VedAstro live smoke.",
        }, ensure_ascii=False, indent=2))
        return
    run([
        PYTHON,
        "scripts/vedastro_service_adapter.py",
        "--range-scan",
        "--domain",
        "career",
        "--case",
        "beijing_first_use_demo",
        "--start-date",
        "2026-01-01",
        "--end-date",
        "2026-12-31",
    ])


def compile_targets() -> None:
    print("\n== Compile core Python files ==")
    targets: list[Path] = []
    for directory in COMPILE_DIRS:
        targets.extend(sorted(directory.glob("*.py")))
    targets.extend(EXTRA_COMPILE_TARGETS)

    seen: set[Path] = set()
    for target in targets:
        if target in seen or not target.exists():
            continue
        seen.add(target)
        print(f"compile {target.relative_to(ROOT)}")
        py_compile.compile(str(target), doraise=True)


def validate_json_files() -> None:
    print("\n== Validate critical JSON files ==")
    for relative in [
        "references/technique_registry.json",
        "references/yoga_rules.json",
        "references/standard_test_charts.json",
        "references/validation_logic_report.json",
        "references/oracle/dasha_shadbala_oracle_cases.json",
        "tests/golden/golden_cases.json",
    ]:
        path = ROOT / relative
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as handle:
            json.load(handle)
        print(f"json ok {relative}")


def run_profile(args: argparse.Namespace) -> dict:
    profile = dict(QUALITY_GATE_PROFILES[args.profile])
    for key in [
        "skip_slow",
        "skip_yoga_logic",
        "skip_frontend_runtime",
        "skip_real_cases",
        "skip_dasha_audit",
        "skip_oracle_audit",
        "skip_local_accuracy_report",
        "skip_vedastro_live",
    ]:
        if getattr(args, key):
            profile[key] = True
    return profile


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Jyotish skill quality gate")
    parser.add_argument("--profile", choices=["quick", "browser", "release", "accuracy", "vedastro-live", "runtime-truth"], default="browser", help="Quality gate profile: quick, browser, release, accuracy, vedastro-live, or runtime-truth")
    parser.add_argument("--skip-slow", action="store_true", help="Skip slow golden-case regressions")
    parser.add_argument("--skip-yoga-logic", action="store_true", help="Skip Yoga logic comparison report refresh")
    parser.add_argument("--skip-frontend-runtime", action="store_true", help="Skip Next.js tests, lint, and production build")
    parser.add_argument("--skip-real-cases", action="store_true", help="Skip public real-person chart revalidation")
    parser.add_argument("--skip-dasha-audit", action="store_true", help="Skip Dasha reference-drift audit")
    parser.add_argument("--skip-oracle-audit", action="store_true", help="Skip combined Dasha/Shadbala external oracle boundary audit")
    parser.add_argument("--skip-local-accuracy-report", action="store_true", help="Skip consolidated local accuracy report")
    parser.add_argument("--skip-vedastro-live", action="store_true", help="Skip optional VedAstro live endpoint smoke")
    parser.add_argument("--all-tests", action="store_true", help="Run every pytest file, including optional-dependency suites")
    parser.add_argument("--require-external-parity", action="store_true", help="Fail the release gate unless the three-engine raw parity manifest passes.")
    args = parser.parse_args()
    profile = run_profile(args)

    os.environ.setdefault("PYTHONPATH", str(ROOT / "scripts"))
    print(f"\n== Quality gate profile: {args.profile} ==")
    print(json.dumps(profile, ensure_ascii=False, indent=2))
    if args.profile == "runtime-truth":
        for target in [
            ROOT / "scripts" / "jyotish_api_server.py",
            ROOT / "scripts" / "diagnose_vedastro_mode.py",
            ROOT / "scripts" / "diagnose_external_engine_adapters.py",
            ROOT / "scripts" / "interpretation_source_runtime_coverage.py",
            ROOT / "scripts" / "sync_final_evidence_packet_status.py",
            ROOT / "scripts" / "external_validation_release_gate.py",
        ]:
            py_compile.compile(str(target), doraise=True)
            print(f"compiled {target.relative_to(ROOT)}")
        run([PYTHON, "scripts/sync_final_evidence_packet_status.py"])
        run([PYTHON, "scripts/interpretation_source_inventory_gate.py"])
        run([PYTHON, "scripts/diagnose_vedastro_mode.py", "--json"])
        run([PYTHON, "scripts/diagnose_external_engine_adapters.py", "--json"])
        run([PYTHON, "scripts/external_validation_release_gate.py", "--require-match"])
    else:
        compile_targets()
        validate_json_files()
        run([PYTHON, "scripts/audit_capabilities.py", "--mode", "validate"])
        run([PYTHON, "scripts/audit_fragments.py", "--strict"])
        run([PYTHON, "scripts/interpretation_source_inventory_gate.py"])
        run([PYTHON, "scripts/character_level_inventory_manifest.py", "--scope", "project", "--no-write", "--summary-only"])
        if profile["check_release_hygiene"]:
            release_hygiene_check(require_external_parity=args.require_external_parity)
        run([PYTHON, "scripts/validate_bphs_invariants.py"])
    if args.all_tests:
        pytest_targets = ["tests"]
    elif args.profile == "runtime-truth":
        pytest_targets = RUNTIME_TRUTH_PYTEST_TARGETS
    else:
        pytest_targets = CORE_PYTEST_TARGETS
    run([PYTHON, "-m", "pytest", *pytest_targets])
    if not profile["skip_frontend_runtime"]:
        run(["npm", "test"], optional=False, cwd=APP)
        run(["npm", "run", "lint"], optional=False, cwd=APP)
        run(["npm", "run", "build"], optional=False, cwd=APP)
    if not profile["skip_slow"]:
        run([PYTHON, "tests/run_golden_cases.py", "--python", PYTHON])
    if not profile["skip_real_cases"]:
        run([PYTHON, "tests/run_real_case_revalidation.py", "--python", PYTHON, "--summary"])
    if not profile["skip_dasha_audit"]:
        run(DASHA_REFERENCE_AUDIT_CMD)
    if not profile["skip_oracle_audit"]:
        run(ORACLE_BOUNDARY_AUDIT_CMD)
        run(EXTERNAL_ORACLE_SANITY_CLOSURE_CMD)
        run_oracle_collection_queue_and_validator()
    if not profile["skip_yoga_logic"]:
        run([PYTHON, "scripts/validate_logic_v2.py"], optional=True)
    if not profile["skip_local_accuracy_report"]:
        run([PYTHON, "scripts/local_accuracy_report.py", "--format", "json"])
    if not profile["skip_vedastro_live"]:
        run_vedastro_live_smoke()
    print("\nQuality gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
