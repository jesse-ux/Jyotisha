from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_external_engine_adapter_diagnostics_aggregates_three_engines() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/diagnose_external_engine_adapters.py", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
        env={**os.environ, "JYOTISH_SKIP_LOCAL_ENV": "1"},
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["scope"] == "external_engine_adapter_diagnostics"
    assert set(report["engines"]) == {"VedAstro", "PyJHora/JHora", "jyotishganit"}
    assert report["engines"]["VedAstro"]["official_closure_plan"]["raw_response_acceptance"].startswith("vedastro_official.raw_response")
    assert report["engines"]["PyJHora/JHora"]["status"] in {"available", "missing_dependency", "missing_adapter"}
    assert report["engines"]["PyJHora/JHora"]["install_hint"]["package"] == "PyJHora"
    assert report["engines"]["PyJHora/JHora"]["license_boundary"].startswith("AGPL external benchmark")
    assert report["engines"]["jyotishganit"]["license"] == "MIT"
    contract = report["same_chart_parity_contract"]
    assert contract["status"] in {"ready", "blocked"}
    assert contract["required_outputs"] == ["D1", "D9", "D10", "D2", "D4", "Vimshottari", "Shadbala", "Ashtakavarga"]
    assert "official_raw_response" in contract["expected_oracle_fields"]["VedAstro"]
    assert "raw_output_path" in contract["expected_oracle_fields"]["PyJHora/JHora"]
    assert contract["engine_states"]["jyotishganit"]["available"] is True
    assert contract["engine_states"]["PyJHora/JHora"]["tested"] is False
    assert report["status"] in {"complete", "partial"}
