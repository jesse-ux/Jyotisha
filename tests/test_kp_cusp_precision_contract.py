from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "references/oracle/kp_cusp_precision_contract_2026_07_19.json"
PROBE = ROOT / "scripts/kp_precision_timing_probe.py"


def test_kp_cusp_precision_contract_blocks_exact_timing_truth() -> None:
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))

    assert data["scope"] == "kp_cusp_precision_contract"
    assert data["status"] == "contract_v1"
    assert data["production_tuning_allowed"] is False
    assert data["exact_cusp_status"] == "blocked_missing_oracle"
    assert data["current_runtime_cusp_mode"] == "whole_sign_house_center_probe"
    assert data["kp_significator_runtime_policy"] == "supporting_probe_only"
    assert "cannot drive precise event timing" in data["claim_boundary"]


def test_kp_cusp_precision_contract_declares_required_inputs_and_oracles() -> None:
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))

    required_inputs = {item["field"] for item in data["required_exact_cusp_inputs"]}
    assert {"birth_or_question_datetime", "latitude", "longitude", "timezone", "ayanamsa", "house_system"}.issubset(required_inputs)
    required_oracles = {item["oracle_id"] for item in data["required_oracles"]}
    assert {"kp_cusp_numeric_worked_example", "kp_significator_field_example", "negative_holdout_timing_set"}.issubset(required_oracles)


def test_kp_precision_probe_surfaces_cusp_contract_boundary() -> None:
    completed = subprocess.run(
        [sys.executable, str(PROBE)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout)

    contract = report["kp_cusp_contract"]
    assert contract["exact_cusp_status"] == "blocked_missing_oracle"
    assert contract["current_runtime_cusp_mode"] == "whole_sign_house_center_probe"
    assert contract["significator_policy"] == "supporting_probe_only"
