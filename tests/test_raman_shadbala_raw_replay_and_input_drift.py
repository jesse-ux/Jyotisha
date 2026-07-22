from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/raman_shadbala_raw_replay_and_input_drift_2026_07_22.json"
ARTIFACT = ROOT / "references/oracle/artifacts/pyjhora_synthetic_north_china_shadbala_raman_stdout_20260722.txt"


def test_raman_shadbala_replay_records_raw_hash_and_blocks_promotion() -> None:
    subprocess.check_call(["python3", "scripts/pyjhora_raman_shadbala_replay.py"], cwd=ROOT)
    packet = json.loads(PACKET.read_text(encoding="utf-8"))
    assert packet["claim_status"] == "blocked"
    assert packet["summary"]["can_promote_raman_sample"] is False
    assert packet["summary"]["complete_match_count"] == 0
    assert packet["summary"]["pending_declared_artifact_found"] is False
    assert ARTIFACT.exists()
    assert packet["replay_artifact_sha256"]


def test_raman_shadbala_replay_proves_input_contract_drift() -> None:
    packet = json.loads(PACKET.read_text(encoding="utf-8"))
    comparisons = {row["case_label"]: row["pending_diff"] for row in packet["comparisons"]}
    declared = comparisons["declared_packet_coordinates"]["max_abs_diff"]
    handan = comparisons["handan_candidate_coordinates"]["max_abs_diff"]
    assert handan < declared
    assert packet["summary"]["best_case_label_by_max_diff"] == "handan_candidate_coordinates"
    assert "input-contract drift" in packet["boundary"]


def test_raman_shadbala_replay_captures_chesta_variant_boundary() -> None:
    packet = json.loads(PACKET.read_text(encoding="utf-8"))
    assert packet["chesta_variant_observation"]["new_api_present"] is True
    assert packet["chesta_variant_observation"]["legacy_api_status"] in {"ok", "error"}
    assert "does not choose a formula truth" in packet["chesta_variant_observation"]["boundary"]
