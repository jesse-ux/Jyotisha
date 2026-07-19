import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "references/oracle/five_track_blocked_progress_dashboard_2026_07_20.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_five_track_dashboard_summarizes_requested_tracks():
    data = json.loads(
        subprocess.check_output(
            ["python3", "scripts/five_track_blocked_progress_dashboard.py", "--date", "2026-07-20"],
            cwd=ROOT,
            text=True,
        )
    )
    assert data["scope"] == "five_track_blocked_progress_dashboard"
    assert data["summary"]["track_count"] == 5
    assert data["summary"]["oracle_ready_count"] == 0
    assert data["production_tuning_allowed"] is False
    assert {row["domain"] for row in data["tracks"]} == {
        "three_engine_parity",
        "kp_precision_timing",
        "worked_example_collection",
        "horary_annual_sensitive_points",
        "varga_mapping",
    }


def test_five_track_dashboard_preserves_numeric_progress_counts():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    tracks = {row["domain"]: row for row in data["tracks"]}
    assert tracks["three_engine_parity"]["progress"]["remaining_ticket_count"] == 58
    assert tracks["worked_example_collection"]["progress"]["candidate_count"] == 5
    assert tracks["worked_example_collection"]["progress"]["oracle_ready_count"] == 0
    assert tracks["varga_mapping"]["progress"]["numeric_oracle_ready_count"] == 0
    assert all(row["claim_status"] in {"blocked", "open_queue", "partial"} for row in data["tracks"])


def test_five_track_dashboard_is_indexed():
    packets = {row["packet_id"]: row for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]}
    assert packets["five_track_blocked_progress_dashboard_2026_07_20"]["claim_status"] == "open_queue"
