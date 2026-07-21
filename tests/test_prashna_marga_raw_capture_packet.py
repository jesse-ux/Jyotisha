import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "references/oracle/prashna_marga_raw_capture_packet_2026_07_20.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_prashna_marga_raw_capture_packet_pins_internet_archive_files():
    data = json.loads(subprocess.check_output(["python3", "scripts/prashna_marga_raw_capture_packet.py", "--date", "2026-07-20"], cwd=ROOT, text=True))
    assert data["scope"] == "prashna_marga_raw_capture_packet"
    assert data["claim_status"] == "source_intake_only"
    assert data["summary"]["ia_item_count"] >= 2
    assert data["summary"]["oracle_ready_count"] == 0
    ids = {row["identifier"] for row in data["internet_archive_items"]}
    assert "PrasnaMargaBVR" in ids
    bvr = next(row for row in data["internet_archive_items"] if row["identifier"] == "PrasnaMargaBVR")
    assert any(file["format"] == "DjVuTXT" and file["sha1"] for file in bvr["files"])


def test_prashna_marga_raw_capture_packet_preserves_no_truth_upgrade_boundary():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert all(row["upgrade_status"] == "candidate_not_oracle" for row in data["internet_archive_items"])
    assert "Trisphuta" in data["field_locator_terms"]
    assert "raw excerpt capture" in data["next_steps"][0]


def test_prashna_marga_raw_capture_packet_is_indexed():
    packets = {row["packet_id"]: row for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]}
    assert packets["prashna_marga_raw_capture_packet_2026_07_20"]["claim_status"] == "source_intake_only"
