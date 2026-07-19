from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )


def test_ashtakavarga_compare_uses_repository_scripts_and_public_baselines() -> None:
    baseline = run("benchmarks/jyotish/scripts/run_pyjhora_compare.py", "--build-local", "--output-prefix", "ashtakavarga_contract")
    assert baseline.returncode == 0, baseline.stderr or baseline.stdout

    comparison = run("benchmarks/jyotish/scripts/run_ashtakavarga_compare.py")
    assert comparison.returncode == 0, comparison.stderr or comparison.stdout

    report = ROOT / "benchmarks/jyotish/outputs/jyotish_benchmark_round6_ashtakavarga_compare.md"
    assert report.exists()
    assert "BAV" in report.read_text(encoding="utf-8")
