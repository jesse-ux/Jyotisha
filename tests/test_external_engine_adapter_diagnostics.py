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
    expected_contract_status = (
        "mismatch"
        if all(state["available"] for state in contract["engine_states"].values())
        else "blocked"
    )
    assert contract["status"] == expected_contract_status
    assert contract["required_outputs"] == ["D1", "D9", "D10", "D2", "D4", "Vimshottari", "Shadbala", "Ashtakavarga"]
    assert "official_raw_response" in contract["expected_oracle_fields"]["VedAstro"]
    assert "raw_output_path" in contract["expected_oracle_fields"]["PyJHora/JHora"]
    assert contract["engine_states"]["jyotishganit"]["available"] is True
    assert contract["engine_states"]["jyotishganit"]["tested"] is True
    assert contract["engine_states"]["VedAstro"]["tested"] is True
    assert contract["engine_states"]["PyJHora/JHora"]["tested"] is True
    pyjhora = contract["partial_verifications"]["PyJHora/JHora"]
    assert pyjhora["status"] == "partial_verified"
    assert pyjhora["missing_required_outputs"] == ["Shadbala"]
    assert {"D2", "D4", "Ashtakavarga"} <= set(pyjhora["covered_outputs"])
    assert pyjhora["output_sample_counts"]["D2"] == 1
    assert pyjhora["output_sample_counts"]["D4"] == 1
    assert pyjhora["output_sample_counts"]["Ashtakavarga"] == 1
    assert pyjhora["output_sample_counts"]["D1"] == 10
    assert pyjhora["supplemental_verifications"][0]["partial_outputs"] == ["Shadbala"]
    assert contract["replay_manifest"]["tested"] is True
    assert contract["replay_manifest"]["status"] == "mismatch"
    assert contract["replay_manifest"]["blocked_reason"] is None
    assert contract["replay_manifest"]["missing_high_rigor_sections"] == []
    assert report["status"] in {"complete", "partial"}
