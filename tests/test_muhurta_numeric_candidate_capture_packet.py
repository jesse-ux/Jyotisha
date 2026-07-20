import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "references" / "oracle" / "muhurta_numeric_candidate_capture_packet_2026_07_20.json"
INDEX = ROOT / "references" / "oracle" / "evidence_packet_index_2026_07_19.json"


def test_muhurta_numeric_candidate_capture_packet_selects_only_numeric_muhurta_sources():
    data = json.loads(
        subprocess.check_output(
            ["python3", "scripts/muhurta_numeric_candidate_capture_packet.py", "--date", "2026-07-20"],
            cwd=ROOT,
            text=True,
        )
    )
    assert data["scope"] == "muhurta_numeric_candidate_capture_packet"
    assert data["claim_status"] == "source_intake_only"
    assert data["summary"]["candidate_count"] == 2
    assert data["summary"]["oracle_ready_count"] == 0
    assert data["production_tuning_allowed"] is False
    ids = {row["source_id"] for row in data["capture_rows"]}
    assert ids == {"mypanchang_edison_2025_panchangam", "drikpanchang_mumbai_rahu_2026_07_20"}


def test_muhurta_numeric_candidate_capture_packet_has_hashes_and_replay_blockers():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    for row in data["capture_rows"]:
        assert row["source_observation_hash"]
        assert row["canonical_request_hash"]
        assert row["raw_capture_status"] == "pending_raw_page_capture"
        assert row["upgrade_status"] == "not_oracle_ready"
        assert "raw_capture_hash" in row["missing_for_oracle"]
        assert "replay_comparison" in row["missing_for_oracle"]
        assert row["next_artifact_path"].startswith("references/oracle/artifacts/")


def test_muhurta_numeric_candidate_capture_packet_is_indexed():
    packets = {row["packet_id"]: row for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]}
    packet = packets["muhurta_numeric_candidate_capture_packet_2026_07_20"]
    assert packet["domain"] == "muhurta_factor_scoring"
    assert packet["claim_status"] == "source_intake_only"
