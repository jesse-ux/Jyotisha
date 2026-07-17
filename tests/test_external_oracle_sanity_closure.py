from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run_closure(*args: str) -> dict:
    completed = subprocess.run(
        [sys.executable, "scripts/external_oracle_sanity_closure.py", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    return json.loads(completed.stdout)


def test_external_official_sanity_closure_reports_all_three_oracles() -> None:
    report = _run_closure("--format", "json")

    assert report["scope"] == "external_official_sanity_oracle_closure"
    assert report["summary"]["required_oracles"] == ["VedAstro", "PyJHora", "jyotishganit"]
    assert report["summary"]["live_official_full_snapshot"] is False
    assert set(report["oracle_ledger"]) == {"vedastro", "pyjhora", "jyotishganit"}

    vedastro = report["oracle_ledger"]["vedastro"]
    assert vedastro["role"] == "official_precision_sanity"
    assert "status" in vedastro
    assert "verdict" in vedastro
    assert vedastro["live_official_full_snapshot"] is False
    assert vedastro["snapshot_status"] == "not_run_default_non_blocking"
    assert "fine_calc_blocked" in vedastro

    pyjhora = report["oracle_ledger"]["pyjhora"]
    assert pyjhora["role"] == "black_box_external_oracle"
    assert pyjhora["artifact_count"] >= 8
    assert pyjhora["packet_count"] >= 6
    assert pyjhora["license_boundary"] == "black_box_artifacts_only_no_agpl_code_import"

    jyotishganit = report["oracle_ledger"]["jyotishganit"]
    assert jyotishganit["role"] == "mit_reference_layer"
    assert jyotishganit["license"] == "MIT"
    assert jyotishganit["status"] in {"ok", "partial", "blocked"}

    assert report["honesty_boundary"]["can_claim_fully_closed"] is False
    assert report["honesty_boundary"]["can_claim_high_rigor_with_blocks"] is True


def test_external_official_sanity_closure_marks_live_vedastro_blocked_when_sanity_fails() -> None:
    report = _run_closure("--format", "json")
    vedastro = report["oracle_ledger"]["vedastro"]

    if vedastro["status"] == "ok":
        assert vedastro["fine_calc_blocked"] is False
    else:
        assert vedastro["fine_calc_blocked"] is True
        assert report["summary"]["blocked_count"] >= 1


def test_external_official_sanity_closure_documents_live_snapshot_flag() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/external_oracle_sanity_closure.py", "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 0
    assert "--live-official-full-snapshot" in completed.stdout
