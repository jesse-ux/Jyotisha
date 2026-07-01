from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run_diag(env: dict[str, str]) -> dict:
    completed = subprocess.run(
        [sys.executable, "scripts/diagnose_vedastro_mode.py", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
        env={**os.environ, **env, "JYOTISH_SKIP_LOCAL_ENV": "1"},
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    return json.loads(completed.stdout)


def test_vedastro_diagnostics_reports_fast_fallback_mode_without_endpoint() -> None:
    report = _run_diag({
        "VEDASTRO_API_ENDPOINT": "",
        "VEDASTRO_ENABLE_NETWORK": "",
        "VEDASTRO_TIMEOUT_SECONDS": "",
        "VEDASTRO_API_KEY": "",
    })

    assert report["mode"] == "fast_local_fallback"
    assert report["official_ready"] is False
    assert "VEDASTRO_API_ENDPOINT" in report["missing"]
    assert report["expected_fallback_status"] == "official_snapshot_budget_exhausted_or_endpoint_blocked"


def test_vedastro_diagnostics_reports_official_mode_when_configured() -> None:
    report = _run_diag({
        "VEDASTRO_API_ENDPOINT": "https://api.vedastro.org/api",
        "VEDASTRO_ENABLE_NETWORK": "1",
        "VEDASTRO_TIMEOUT_SECONDS": "20",
        "VEDASTRO_API_KEY": "sample-key",
    })

    assert report["mode"] == "official_extended"
    assert report["official_ready"] is True
    assert report["timeout_seconds"] == 20.0
    assert report["network_enabled"] is True
    assert report["has_api_key"] is True

