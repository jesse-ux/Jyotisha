import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "references/oracle/prashna_sphuta_line_review_queue_2026_07_20.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_prashna_sphuta_line_review_queue_creates_human_review_tasks():
    data = json.loads(subprocess.check_output(["python3", "scripts/prashna_sphuta_line_review_queue.py", "--date", "2026-07-20"], cwd=ROOT, text=True))
    assert data["scope"] == "prashna_sphuta_line_review_queue"
    assert data["claim_status"] == "open_queue"
    assert data["summary"]["review_task_count"] >= 2
    assert data["summary"]["truth_upgrade_count"] == 0
    task = data["review_tasks"][0]
    assert task["review_status"] == "needs_human_or_second_source_review"
    assert "chatusphuta" in task["fields_to_check"]
    assert task["window_hash"]


def test_prashna_sphuta_line_review_queue_has_explicit_acceptance_criteria():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    criteria = data["acceptance_criteria"]
    assert "do_not_copy_long_text" in criteria
    assert "record_line_coordinates" in criteria
    assert "classify_formula_variant_or_transcription" in criteria
    assert all(len(task["short_context"]) < 260 for task in data["review_tasks"])


def test_prashna_sphuta_line_review_queue_is_indexed():
    packets = {row["packet_id"]: row for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]}
    assert packets["prashna_sphuta_line_review_queue_2026_07_20"]["claim_status"] == "open_queue"
