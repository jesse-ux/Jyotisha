import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "references/oracle/prashna_marga_excerpt_locator_2026_07_20.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_prashna_marga_excerpt_locator_finds_keyword_windows_without_vendoring_text():
    data = json.loads(subprocess.check_output(["python3", "scripts/prashna_marga_excerpt_locator.py", "--date", "2026-07-20"], cwd=ROOT, text=True))
    assert data["scope"] == "prashna_marga_excerpt_locator"
    assert data["claim_status"] == "source_intake_only"
    assert data["summary"]["located_window_count"] >= 1
    assert data["summary"]["oracle_ready_count"] == 0
    row = data["located_windows"][0]
    assert row["window_hash"]
    assert row["line_start"] > 0
    assert row["line_end"] >= row["line_start"]
    assert len(row["short_context"]) < 260


def test_prashna_marga_excerpt_locator_keeps_mismatch_queue_open():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert data["upgrade_status"] == "candidate_not_oracle"
    assert "raw excerpt capture" in data["next_steps"][0]
    assert "complete_prashna_input" in data["missing_for_oracle"]


def test_prashna_marga_excerpt_locator_is_indexed():
    packets = {row["packet_id"]: row for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]}
    assert packets["prashna_marga_excerpt_locator_2026_07_20"]["claim_status"] == "source_intake_only"
