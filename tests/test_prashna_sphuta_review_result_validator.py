import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "references/oracle/prashna_sphuta_review_result_validation_2026_07_20.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_prashna_sphuta_review_result_validator_blocks_blank_templates():
    data = json.loads(subprocess.check_output(["python3", "scripts/prashna_sphuta_review_result_validator.py", "--date", "2026-07-20"], cwd=ROOT, text=True))
    assert data["scope"] == "prashna_sphuta_review_result_validation"
    assert data["claim_status"] == "blocked_until_human_labels"
    assert data["summary"]["template_count"] >= 2
    assert data["summary"]["valid_completed_review_count"] == 0
    assert data["summary"]["replay_gate_ready_count"] == 0
    row = data["validation_rows"][0]
    assert row["validation_status"] == "blocked_missing_human_review"
    assert "review_result" in row["missing_fields"]


def test_prashna_sphuta_review_result_validator_preserves_allowed_result_contract():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert data["allowed_results"] == ["formula_variant", "source_transcription", "naming_variant", "insufficient_evidence"]
    assert data["replay_gate_policy"] == "requires_valid_completed_review_and_complete_prashna_input"
    assert data["truth_matrix_allowed"] is False


def test_prashna_sphuta_review_result_validator_is_indexed():
    packets = {row["packet_id"]: row for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]}
    assert packets["prashna_sphuta_review_result_validation_2026_07_20"]["claim_status"] == "blocked_until_human_labels"
