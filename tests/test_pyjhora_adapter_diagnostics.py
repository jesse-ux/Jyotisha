from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run_diag(env: dict[str, str] | None = None) -> dict:
    completed = subprocess.run(
        [sys.executable, "scripts/diagnose_pyjhora_adapter.py", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
        env={**os.environ, **(env or {})},
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    return json.loads(completed.stdout)


def test_pyjhora_adapter_diagnostics_reports_current_status() -> None:
    report = _run_diag()

    assert report["scope"] == "pyjhora_adapter_diagnostics"
    assert report["adapter_command"] == "python3 benchmarks/jyotish/scripts/run_pyjhora_compare.py"
    assert report["status"] in {"available", "missing_dependency", "dependency_import_failed"}
    if report["status"] == "available":
        assert report["dependency_import_error"] is None


def test_pyjhora_adapter_diagnostics_reports_missing_dependency() -> None:
    report = _run_diag({"PYJHORA_MODULE_NAME": "__definitely_missing_pyjhora_module__"})

    assert report["status"] == "missing_dependency"
    assert report["missing_dependency"] == "__definitely_missing_pyjhora_module__"


def test_pyjhora_adapter_diagnostics_reports_actionable_external_boundary() -> None:
    report = _run_diag({"PYJHORA_MODULE_NAME": "__definitely_missing_pyjhora_module__"})

    assert report["install_hint"]["package"] == "PyJHora"
    assert "requirements-reference-engines.txt" in report["install_hint"]["commands"][0]
    assert report["license_boundary"] == "AGPL external benchmark only; do not vendor or make it a runtime dependency."
    assert report["ephemeris_data_note"]
