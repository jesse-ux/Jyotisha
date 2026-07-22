import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "references/oracle/prashna_sphuta_mismatch_arbitration_2026_07_20.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_prashna_sphuta_mismatch_arbitration_records_formula_and_transcription_candidates():
    data = json.loads(subprocess.check_output(["python3", "scripts/prashna_sphuta_mismatch_arbitration.py", "--date", "2026-07-20"], cwd=ROOT, text=True))
    assert data["scope"] == "prashna_sphuta_mismatch_arbitration"
    assert data["claim_status"] == "open_queue"
    assert data["summary"]["mismatch_count"] >= 1
    row = data["rows"][0]
    assert row["trisphuta_status"] == "matches"
    assert row["chatusphuta_status"] == "mismatch"
    assert "formula_variant" in row["candidate_causes"]
    assert "source_transcription" in row["candidate_causes"]
    assert row["next_evidence_owner"] == "worked_example_collection"


def test_prashna_sphuta_mismatch_arbitration_adds_second_public_formula_candidate():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    sources = {row["source_id"] for row in data["source_candidates"]}
    assert "internet_archive_prasna_marga_bv_raman_sphuta_fragment" in sources
    assert all(row["upgrade_status"] == "candidate_not_oracle" for row in data["source_candidates"])


def test_prashna_sphuta_mismatch_arbitration_is_indexed():
    packets = {row["packet_id"]: row for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]}
    assert packets["prashna_sphuta_mismatch_arbitration_2026_07_20"]["claim_status"] == "open_queue"
