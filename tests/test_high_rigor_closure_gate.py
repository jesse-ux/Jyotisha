from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts/high_rigor_closure_gate.py"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def _run_gate() -> dict:
    completed = subprocess.run(
        [sys.executable, str(GATE)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def test_high_rigor_closure_gate_blocks_production_tuning_until_oracle_holdout_cusp_and_scoring_close() -> None:
    report = _run_gate()

    assert report["scope"] == "high_rigor_closure_gate"
    assert report["production_tuning_allowed"] is False
    assert report["verified_day_month_timing_allowed"] is False
    assert report["birth_time_truth_allowed"] is False
    assert report["commercial_sync_allowed"] is False
    assert report["overall_status"] == "blocked"

    gates = {gate["gate_id"]: gate for gate in report["gates"]}
    assert gates["external_numeric_oracle"]["status"] == "blocked"
    assert gates["independent_negative_holdout"]["status"] == "blocked"
    assert gates["kp_exact_cusp"]["status"] == "blocked"
    assert gates["full_scoring_contracts"]["status"] == "partial"


def test_high_rigor_closure_gate_lists_full_scoring_domains_and_next_actions() -> None:
    report = _run_gate()
    gates = {gate["gate_id"]: gate for gate in report["gates"]}
    domains = {item["domain"] for item in gates["full_scoring_contracts"]["evidence"]}

    assert {"kp_precision_timing", "muhurta", "ashtakavarga_advanced_usage", "compatibility"}.issubset(domains)
    assert report["next_actions"]
    assert all(action["blocked_by"] for action in report["next_actions"])


def test_high_rigor_closure_gate_is_indexed_as_governance_packet() -> None:
    data = json.loads(INDEX.read_text(encoding="utf-8"))
    packets = {packet["packet_id"]: packet for packet in data["packets"]}

    assert packets["high_rigor_closure_gate"]["path"] == "scripts/high_rigor_closure_gate.py"
    assert packets["high_rigor_closure_gate"]["claim_status"] == "blocked"
