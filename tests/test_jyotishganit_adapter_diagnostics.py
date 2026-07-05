from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run_diag(env: dict[str, str] | None = None) -> dict:
    completed = subprocess.run(
        [sys.executable, "scripts/diagnose_jyotishganit_adapter.py", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
        env={**os.environ, **(env or {})},
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    return json.loads(completed.stdout)


def test_jyotishganit_adapter_diagnostics_reports_current_status() -> None:
    report = _run_diag()

    assert report["scope"] == "jyotishganit_adapter_diagnostics"
    assert report["adapter_path"] == "references/open_source_sources/jyotishganit"
    assert report["status"] in {"available", "missing_checkout", "runtime_error"}
    assert report["license"] == "MIT"


def test_jyotishganit_adapter_diagnostics_reports_missing_checkout() -> None:
    report = _run_diag({"JYOTISHGANIT_ADAPTER_PATH": "references/open_source_sources/__missing_jyotishganit__"})

    assert report["status"] == "missing_checkout"
