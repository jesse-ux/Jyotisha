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
PYTHON = sys.executable

COMPILE_TARGETS = [
    ROOT / "scripts" / "jyotish_engine.py",
    ROOT / "scripts" / "varga.py",
    ROOT / "scripts" / "ashtakavarga.py",
    ROOT / "scripts" / "yoga_engine.py",
    ROOT / "scripts" / "audit_capabilities.py",
    ROOT / "scripts" / "validate_bphs_invariants.py",
    ROOT / "scripts" / "_compute_one_chart.py",
    ROOT / "scripts" / "build_standard_test_charts.py",
    ROOT / "scripts" / "build_planet_positions_60.py",
    ROOT / "tests" / "run_golden_cases.py",
]


def run(cmd: list[str], *, optional: bool = False) -> bool:
    print(f"\n$ {' '.join(cmd)}")
    completed = subprocess.run(cmd, cwd=ROOT, text=True)
    if completed.returncode == 0:
        return True
    if optional:
        print(f"Optional step failed with exit code {completed.returncode}; continuing.")
        return False
    raise SystemExit(completed.returncode)


def compile_targets() -> None:
    print("\n== Compile core Python files ==")
    for target in COMPILE_TARGETS:
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Jyotish skill quality gate")
    parser.add_argument("--skip-slow", action="store_true", help="Skip slow golden-case regressions")
    parser.add_argument("--skip-yoga-logic", action="store_true", help="Skip Yoga logic comparison report refresh")
    args = parser.parse_args()

    os.environ.setdefault("PYTHONPATH", str(ROOT / "scripts"))
    compile_targets()
    validate_json_files()
    run([PYTHON, "scripts/audit_capabilities.py", "--mode", "validate"])
    run([PYTHON, "scripts/validate_bphs_invariants.py"])
    run([PYTHON, "-m", "pytest", "tests"])
    if not args.skip_slow:
        run([PYTHON, "tests/run_golden_cases.py", "--python", PYTHON])
    if not args.skip_yoga_logic:
        run([PYTHON, "scripts/validate_logic_v2.py"], optional=True)
    print("\nQuality gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
