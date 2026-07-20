import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "references/oracle/prashna_sphuta_source_comparison_matrix_2026_07_20.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_prashna_sphuta_source_comparison_matrix_classifies_each_field():
    data = json.loads(subprocess.check_output(["python3", "scripts/prashna_sphuta_source_comparison_matrix.py", "--date", "2026-07-20"], cwd=ROOT, text=True))
    assert data["scope"] == "prashna_sphuta_source_comparison_matrix"
    assert data["claim_status"] == "open_queue"
    fields = {row["field"]: row for row in data["field_rows"]}
    assert fields["trisphuta"]["local_vs_vedastro_status"] == "match"
    assert fields["chatusphuta"]["local_vs_vedastro_status"] == "mismatch"
    assert fields["panchasphuta"]["local_vs_vedastro_status"] == "mismatch"
    assert fields["gulika"]["local_vs_vedastro_status"] == "input_value_only"
    assert data["summary"]["truth_upgrade_count"] == 0


def test_prashna_sphuta_source_comparison_matrix_links_ia_windows():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert data["ia_excerpt_window_count"] >= 1
    assert all(row["ia_excerpt_status"] in {"located_context", "not_field_specific"} for row in data["field_rows"])
    assert data["next_evidence"] == ["line-level transcription review", "complete Prashna input", "legal external replay"]


def test_prashna_sphuta_source_comparison_matrix_is_indexed():
    packets = {row["packet_id"]: row for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]}
    assert packets["prashna_sphuta_source_comparison_matrix_2026_07_20"]["claim_status"] == "open_queue"
