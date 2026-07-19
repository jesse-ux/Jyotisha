import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "references/oracle/worked_example_numeric_packet_eligibility_2026_07_20.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_worked_example_numeric_packet_eligibility_summarizes_candidate_rows():
    data = json.loads(
        subprocess.check_output(
            ["python3", "scripts/worked_example_numeric_packet_eligibility.py", "--date", "2026-07-20"],
            cwd=ROOT,
            text=True,
        )
    )
    assert data["scope"] == "worked_example_numeric_packet_eligibility"
    assert data["summary"]["candidate_count"] == 5
    assert data["summary"]["oracle_ready_count"] == 0
    assert data["summary"]["runtime_only_count"] >= 1
    assert data["production_tuning_allowed"] is False


def test_worked_example_numeric_packet_eligibility_keeps_required_fields_visible():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    by_topic = {row["topic"]: row for row in data["rows"]}
    assert by_topic["KP cusp"]["eligibility_status"] == "runtime_only_public_oracle_missing"
    assert "raw_capture_hash" in by_topic["KP cusp"]["missing_for_oracle"]
    assert by_topic["KP sub-lord table"]["eligibility_status"] == "reference_table_hash_needed"
    assert all(row["claim_boundary"].startswith("Not oracle-ready") for row in data["rows"])


def test_worked_example_numeric_packet_eligibility_is_indexed():
    packets = {row["packet_id"]: row for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]}
    assert packets["worked_example_numeric_packet_eligibility_2026_07_20"]["claim_status"] == "open_queue"
