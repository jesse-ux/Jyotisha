#!/usr/bin/env python3
"""Run the Jyotish skill quality gate used by local development and CI."""

from __future__ import annotations

import argparse
import json
import os
import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "jyotish-app"
PYTHON = sys.executable

COMPILE_DIRS = [
    ROOT / "scripts",
    ROOT / "jyotish_vedic",
]

EXTRA_COMPILE_TARGETS = [
    ROOT / "mcp_server.py",
    ROOT / "scripts" / "audit_fragments.py",
    ROOT / "tests" / "run_golden_cases.py",
    ROOT / "tests" / "run_frontend_runtime_smoke.py",
]

CORE_PYTEST_TARGETS = [
    "tests/test_frontend_productization.py",
    "tests/test_cli_smoke.py",
    "tests/test_api_server_security.py",
    "tests/test_jaimini.py",
    "tests/test_shadbala_complete.py",
    "tests/test_transit_trigger.py",
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
    "jyotish-app/import-chart.js",
    "jyotish-app/mevg-audit.js",
    "jyotish-app/public/manifest.webmanifest",
    "jyotish-app/public/pwa-icon.svg",
    "jyotish-app/public/sw.js",
    "jyotish-app/security.js",
    "jyotish-app/skill-map.js",
    "progress.md",
    "scripts/audit_fragments.py",
    "scripts/deep_varga_avastha.py",
    "scripts/desktop_packaging_preflight.py",
    "scripts/ephemeris_adapter_contract.py",
    "scripts/ephemeris_backend_probe.py",
    "scripts/ephemeris_candidate_adapter_spike.py",
    "task_plan.md",
    "tests/run_frontend_click_smoke.py",
    "tests/run_frontend_runtime_smoke.py",
    "tests/test_api_server_security.py",
    "tests/test_deep_varga_avastha.py",
    "tests/test_frontend_productization.py",
]

QUALITY_GATE_PROFILES = {
    "quick": {
        "skip_slow": True,
        "skip_yoga_logic": True,
        "skip_frontend_runtime": False,
        "skip_frontend_click": True,
        "frontend_click_mode": "core",
        "check_release_hygiene": False,
    },
    "browser": {
        "skip_slow": True,
        "skip_yoga_logic": True,
        "skip_frontend_runtime": False,
        "skip_frontend_click": False,
        "frontend_click_mode": "all",
        "check_release_hygiene": False,
    },
    "release": {
        "skip_slow": False,
        "skip_yoga_logic": False,
        "skip_frontend_runtime": False,
        "skip_frontend_click": False,
        "frontend_click_mode": "all",
        "check_release_hygiene": True,
    },
}


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
        "1. 网页服务：cd jyotish-app && npm run dev -- --host 127.0.0.1 --port 5173",
        "2. 本地 API 服务：python3 scripts/jyotish_api_server.py --host 127.0.0.1 --port 5200",
        "3. Open http://127.0.0.1:5173, then open Trust Center and run the health check.",
        "4. PWA 安装壳只包装网页服务，本地 API 服务仍需单独启动。",
        "Next action: Run the focused command above, add --keep-logs for browser click smoke, then compare the app state with the startup path above.",
        "",
    ])
    return "\n".join(lines)


def run(cmd: list[str], *, optional: bool = False, step: str | None = None, cwd: Path = ROOT) -> bool:
    label = step or " ".join(cmd[:2])
    print(f"\n$ {' '.join(cmd)}")
    completed = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if completed.stdout:
        print(completed.stdout, end="" if completed.stdout.endswith("\n") else "\n")
    if completed.stderr:
        print(completed.stderr, end="" if completed.stderr.endswith("\n") else "\n", file=sys.stderr)
    if completed.returncode == 0:
        return True
    if optional:
        print(f"Optional step failed with exit code {completed.returncode}; continuing.")
        return False
    print(
        format_failure_summary(label, cmd, completed.returncode, stdout=completed.stdout, stderr=completed.stderr, cwd=cwd),
        file=sys.stderr,
    )
    raise SystemExit(completed.returncode)


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


def release_hygiene_check() -> None:
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
    print("release_hygiene_check ok: no release-critical product files are untracked")


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
    for key in ["skip_slow", "skip_yoga_logic", "skip_frontend_runtime", "skip_frontend_click"]:
        if getattr(args, key):
            profile[key] = True
    if args.frontend_click_mode:
        profile["frontend_click_mode"] = args.frontend_click_mode
    return profile


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Jyotish skill quality gate")
    parser.add_argument("--profile", choices=["quick", "browser", "release"], default="browser", help="Quality gate profile: quick, browser, or release")
    parser.add_argument("--skip-slow", action="store_true", help="Skip slow golden-case regressions")
    parser.add_argument("--skip-yoga-logic", action="store_true", help="Skip Yoga logic comparison report refresh")
    parser.add_argument("--skip-frontend-runtime", action="store_true", help="Skip frontend build and runtime smoke")
    parser.add_argument("--skip-frontend-click", action="store_true", help="Skip browser click smoke")
    parser.add_argument("--frontend-click-mode", choices=["core", "mobile", "offline", "pdf", "workspace", "mobile-trust", "import-files", "all"], default=None, help="Browser click smoke mode for browser/release profiles")
    parser.add_argument("--frontend-click-timeout", type=int, default=240, help="Timeout seconds for browser click smoke")
    parser.add_argument("--all-tests", action="store_true", help="Run every pytest file, including optional-dependency suites")
    args = parser.parse_args()
    profile = run_profile(args)

    os.environ.setdefault("PYTHONPATH", str(ROOT / "scripts"))
    print(f"\n== Quality gate profile: {args.profile} ==")
    print(json.dumps(profile, ensure_ascii=False, indent=2))
    compile_targets()
    validate_json_files()
    run([PYTHON, "scripts/audit_capabilities.py", "--mode", "validate"])
    run([PYTHON, "scripts/audit_fragments.py", "--strict"])
    if profile["check_release_hygiene"]:
        release_hygiene_check()
    run([PYTHON, "scripts/validate_bphs_invariants.py"])
    pytest_targets = ["tests"] if args.all_tests else CORE_PYTEST_TARGETS
    run([PYTHON, "-m", "pytest", *pytest_targets])
    if not profile["skip_frontend_runtime"]:
        run(["npm", "run", "build"], optional=False, cwd=APP)
        run([PYTHON, "tests/run_frontend_runtime_smoke.py", "--start-if-needed"])
    if not profile["skip_frontend_click"]:
        run([
            PYTHON,
            "tests/run_frontend_click_smoke.py",
            "--mode",
            profile["frontend_click_mode"],
            "--timeout",
            str(args.frontend_click_timeout),
        ])
    if not profile["skip_slow"]:
        run([PYTHON, "tests/run_golden_cases.py", "--python", PYTHON])
    if not profile["skip_yoga_logic"]:
        run([PYTHON, "scripts/validate_logic_v2.py"], optional=True)
    print("\nQuality gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
