import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "references/oracle/prashna_sphuta_candidate_replay_readiness_2026_07_20.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_prashna_sphuta_candidate_replay_parses_expected_values_without_truth_upgrade():
    data = json.loads(subprocess.check_output(["python3", "scripts/prashna_sphuta_candidate_replay.py", "--date", "2026-07-20"], cwd=ROOT, text=True))
    assert data["scope"] == "prashna_sphuta_candidate_replay_readiness"
    assert data["claim_status"] == "tooling_observation_only"
    assert data["summary"]["candidate_count"] == 1
    assert data["summary"]["local_formula_check_pass_count"] == 0
    assert data["summary"]["oracle_ready_count"] == 0
    row = data["rows"][0]
    assert row["replay_status"] == "blocked_missing_complete_input"
    assert row["local_formula_consistency"] == "mismatch"
    assert abs(row["computed_from_expected_degrees"]["trisphuta"] - row["expected_degrees"]["trisphuta"]) < 0.01
    assert abs(row["computed_from_expected_degrees"]["chatusphuta"] - row["expected_degrees"]["chatusphuta"]) > 1


def test_prashna_sphuta_candidate_replay_keeps_missing_inputs_visible():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    row = data["rows"][0]
    assert "question_datetime_local" in row["missing_for_true_replay"]
    assert "location" in row["missing_for_true_replay"]
    assert "ayanamsa" in row["missing_for_true_replay"]
    assert row["upgrade_status"] == "not_oracle_ready"


def test_prashna_sphuta_candidate_replay_is_indexed():
    packets = {row["packet_id"]: row for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]}
    packet = packets["prashna_sphuta_candidate_replay_readiness_2026_07_20"]
    assert packet["claim_status"] == "tooling_observation_only"
