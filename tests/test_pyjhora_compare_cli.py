import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "benchmarks" / "jyotish" / "scripts" / "run_pyjhora_compare.py"


def test_pyjhora_compare_help_is_non_executing():
    result = subprocess.run(
        [sys.executable, str(RUNNER), "--help"], cwd=ROOT, capture_output=True, text=True, timeout=15
    )

    assert result.returncode == 0
    assert "--build-local" in result.stdout
    assert "FileNotFoundError" not in result.stderr
