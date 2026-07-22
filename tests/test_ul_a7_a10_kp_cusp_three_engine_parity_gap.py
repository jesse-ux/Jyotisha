from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/ul_a7_a10_kp_cusp_three_engine_parity_gap_2026_07_22.json"


def test_ul_a7_a10_kp_cusp_gap_blocks_three_engine_parity() -> None:
    packet = json.loads(PACKET.read_text(encoding="utf-8"))
    assert packet["claim_status"] == "blocked"
    assert packet["truth_matrix_allowed"] is False
    assert packet["summary"]["three_engine_parity_ready_count"] == 0
    assert packet["summary"]["blocked_field_count"] == 4
    assert "birth_time_truth" in packet["blocked_runtime_use"]


def test_ul_a7_a10_kp_cusp_gap_lists_all_required_fields() -> None:
    packet = json.loads(PACKET.read_text(encoding="utf-8"))
    rows = {row["field"]: row for row in packet["field_rows"]}
    for field in ["UL", "A7", "A10", "KP cusp star/sub/sub-sub"]:
        assert field in rows
        assert rows[field]["local_status"] == "runtime_ready"
        assert "claim_boundary" in rows[field]
    assert rows["KP cusp star/sub/sub-sub"]["external_engine_status"]["VedicAstro"] == "single_external_raw_observation_ready"
    assert rows["UL"]["external_engine_status"]["PyJHora"] == "not_yet_captured_for_same_input"
