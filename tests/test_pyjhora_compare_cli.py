import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from benchmarks.jyotish.scripts.run_pyjhora_compare import write_report


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "benchmarks" / "jyotish" / "scripts" / "run_pyjhora_compare.py"


def test_pyjhora_compare_help_is_non_executing():
    result = subprocess.run(
        [sys.executable, str(RUNNER), "--help"], cwd=ROOT, capture_output=True, text=True, timeout=15
    )

    assert result.returncode == 0
    assert "--build-local" in result.stdout
    assert "--output-prefix" in result.stdout
    assert "FileNotFoundError" not in result.stderr


def test_pyjhora_report_uses_supplied_utc_generation_timestamp():
    report = write_report(
        [],
        [],
        generated_at=datetime(2026, 7, 15, 4, 30, tzinfo=timezone.utc),
    )

    assert "生成时间：2026-07-15T04:30:00+00:00" in report
    assert "生成时间：2026-06-03" not in report
