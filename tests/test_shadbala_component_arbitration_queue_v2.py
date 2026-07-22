from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/shadbala_component_arbitration_queue_v2_2026_07_22.json"


def test_shadbala_component_arbitration_queue_v2_is_stable_and_guarded() -> None:
    subprocess.check_call(["python3", "scripts/shadbala_component_arbitration_queue_v2.py"], cwd=ROOT)
    packet = json.loads(PACKET.read_text(encoding="utf-8"))
    assert packet["scope"] == "shadbala_component_arbitration_queue_v2"
    assert packet["claim_status"] == "partial"
    assert packet["truth_matrix_allowed"] is False
    assert packet["production_tuning_allowed"] is False
    assert packet["summary"]["same_unit_row_count"] == 42
    assert packet["summary"]["absolute_truth_upgrade_count"] == 0


def test_shadbala_component_arbitration_queue_v2_closes_only_naisargika() -> None:
    packet = json.loads(PACKET.read_text(encoding="utf-8"))
    rows = {row["component"]: row for row in packet["component_rows"]}
    assert rows["naisargika"]["arbitration_status"] == "component_closed_same_unit"
    assert rows["naisargika"]["unresolved_row_count"] == 0
    for component in ["dig", "drik", "kala", "sthana", "chesta"]:
        assert rows[component]["arbitration_status"] != "component_closed_same_unit"
        assert rows[component]["unresolved_row_count"] > 0
    assert "Seeghrochcha" in rows["chesta"]["next_evidence"]
    assert "raw-backed third case" in rows["sthana"]["next_evidence"]
