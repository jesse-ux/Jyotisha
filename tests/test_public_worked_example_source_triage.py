import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "references" / "oracle" / "public_worked_example_source_triage_2026_07_20.json"
INDEX = ROOT / "references" / "oracle" / "evidence_packet_index_2026_07_19.json"


def test_public_worked_example_source_triage_classifies_web_sources():
    data = json.loads(
        subprocess.check_output(
            ["python3", "scripts/public_worked_example_source_triage.py", "--date", "2026-07-20"],
            cwd=ROOT,
            text=True,
        )
    )
    assert data["scope"] == "public_worked_example_source_triage"
    assert data["claim_status"] == "source_intake_only"
    assert data["summary"]["source_count"] >= 5
    assert data["summary"]["numeric_candidate_count"] >= 2
    assert data["summary"]["oracle_ready_count"] == 0
    by_id = {row["source_id"]: row for row in data["sources"]}
    assert by_id["mypanchang_edison_2025_panchangam"]["numeric_fields_present"] is True
    assert by_id["drikpanchang_mumbai_rahu_2026_07_20"]["numeric_fields_present"] is True
    assert by_id["mypanchang_tarabalam_chakra"]["source_role"] == "formula_reference"


def test_public_worked_example_source_triage_preserves_boundaries_and_hashes():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert all(row["observation_hash"] for row in data["sources"])
    assert all(row["upgrade_status"] != "oracle_ready" for row in data["sources"])
    rahu = next(row for row in data["sources"] if row["source_id"] == "drikpanchang_mumbai_rahu_2026_07_20")
    assert "sunrise" in rahu["missing_for_oracle"]
    assert "raw_capture_hash" in rahu["missing_for_oracle"]


def test_public_worked_example_source_triage_is_indexed():
    packets = {row["packet_id"]: row for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]}
    packet = packets["public_worked_example_source_triage_2026_07_20"]
    assert packet["domain"] == "worked_example_collection"
    assert packet["claim_status"] == "source_intake_only"
