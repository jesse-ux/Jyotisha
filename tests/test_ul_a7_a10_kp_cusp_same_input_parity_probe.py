from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/ul_a7_a10_kp_cusp_same_input_parity_probe_2026_07_22.json"


def test_same_input_parity_probe_generates_local_fields_and_blocks_parity() -> None:
    subprocess.check_call(["python3", "scripts/ul_a7_a10_kp_cusp_same_input_parity_probe.py"], cwd=ROOT)
    packet = json.loads(PACKET.read_text(encoding="utf-8"))
    assert packet["claim_status"] == "blocked"
    assert packet["summary"]["field_count"] == 4
    assert packet["summary"]["local_ready_count"] == 4
    assert packet["summary"]["three_engine_parity_ready_count"] == 0
    fields = {row["field"]: row for row in packet["field_rows"]}
    assert fields["UL"]["external_ready_count"] == 0
    assert fields["A7"]["external_ready_count"] == 0
    assert fields["A10"]["external_ready_count"] == 0
    assert fields["KP_cusps"]["three_engine_parity_status"] == "blocked"


def test_same_input_parity_probe_records_external_engine_boundaries() -> None:
    packet = json.loads(PACKET.read_text(encoding="utf-8"))
    observations = {row["engine"]: row for row in packet["observations"]}
    assert observations["local"]["status"] == "complete"
    assert observations["PyJHora"]["status"] == "not_captured"
    assert observations["jyotishganit"]["status"] == "no_field_contract"
    assert observations["VedicAstro"]["status"] in {"complete", "blocked_runtime_error"}
    assert "three-engine parity remains blocked" in packet["boundary"]
