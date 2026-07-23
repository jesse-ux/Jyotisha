import json
from pathlib import Path

from scripts.timing_rectification_reviewer_freeze_status_2026_07_23 import build_report


ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "references/real_case_calibration/timing_rectification_reviewer_freeze_status_2026_07_23.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_reviewer_1_confirmation_is_recorded_without_blind_replay_upgrade() -> None:
    data = json.loads(STATUS.read_text(encoding="utf-8"))

    assert data == build_report()
    assert data["claim_status"] == "one_reviewer_confirmed_second_required"
    assert data["truth_matrix_allowed"] is False
    assert data["production_tuning_allowed"] is False
    assert data["reviewer_1"]["confirmation_text"] == "我确认这 3 个候选案例可以作为第一轮 holdout。"
    assert data["reviewer_2_required"] is True
    assert data["summary"] == {
        "case_count": 3,
        "reviewer_1_confirmed_count": 3,
        "reviewer_2_confirmed_count": 0,
        "ready_for_blind_replay_count": 0,
    }
    assert "does not satisfy the two-reviewer freeze requirement" in data["boundary"]


def test_reviewer_freeze_status_is_indexed_as_human_review_required() -> None:
    packets = {packet["packet_id"]: packet for packet in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]}
    packet = packets["timing_rectification_reviewer_freeze_status_2026_07_23"]

    assert packet["claim_status"] == "one_reviewer_confirmed_second_required"
    assert packet["consumer_policy"] == "human_review_required"
    assert "reviewer 2 is still missing" in packet["claim_boundary"]
