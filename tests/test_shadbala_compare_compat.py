from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_shadbala_compare_supports_installed_pyjhora_api() -> None:
    completed = subprocess.run(
        [sys.executable, "benchmarks/jyotish/scripts/run_shadbala_compare.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=90,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert "Shadbala Benchmark" in completed.stdout
    assert "Total planets: 35" in completed.stdout
