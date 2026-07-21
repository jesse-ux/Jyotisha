import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "references/oracle/prashna_sphuta_review_result_template_2026_07_20.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_prashna_sphuta_review_result_template_is_blank_and_schema_complete():
    data = json.loads(subprocess.check_output(["python3", "scripts/prashna_sphuta_review_result_template.py", "--date", "2026-07-20"], cwd=ROOT, text=True))
    assert data["scope"] == "prashna_sphuta_review_result_template"
    assert data["claim_status"] == "blocked_until_human_labels"
    assert data["summary"]["template_count"] >= 2
    assert data["summary"]["completed_review_count"] == 0
    row = data["templates"][0]
    assert row["review_result"] is None
    assert row["allowed_results"] == ["formula_variant", "source_transcription", "naming_variant", "insufficient_evidence"]
    assert "reviewer_id" in row["required_human_fields"]


def test_prashna_sphuta_review_result_template_has_no_truth_upgrade():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert data["production_tuning_allowed"] is False
    assert data["truth_matrix_allowed"] is False
    assert data["upgrade_policy"] == "no_upgrade_until_completed_review_and_replay"


def test_prashna_sphuta_review_result_template_is_indexed():
    packets = {row["packet_id"]: row for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]}
    assert packets["prashna_sphuta_review_result_template_2026_07_20"]["claim_status"] == "blocked_until_human_labels"
