import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "references/oracle/kp_public_worked_example_candidate_queue_2026_07_21.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_kp_public_queue_has_sources_but_no_numeric_oracle_upgrade():
    data = json.loads(QUEUE.read_text(encoding="utf-8"))

    assert data["scope"] == "kp_public_worked_example_candidate_queue"
    assert data["claim_status"] == "open_queue"
    assert data["numeric_oracle_ready_count"] == 0
    assert data["truth_matrix_allowed"] is False
    assert data["boundary"] == "public_source_candidate_queue_only_no_kp_numeric_oracle"


def test_kp_public_queue_records_formula_and_runtime_cusp_candidates():
    data = json.loads(QUEUE.read_text(encoding="utf-8"))
    rows = {row["id"]: row for row in data["candidates"]}

    assert rows["astrosage_kp_chapter_2"]["candidate_type"] == "formula_and_text_worked_example"
    assert rows["astrosage_kp_chapter_2"]["has_numeric_cusp_table"] is False
    assert rows["astrosage_kp_sign_star_sub_table"]["candidate_type"] == "reference_table"
    assert rows["onlinejyotish_kp_horoscope"]["candidate_type"] == "runtime_form_candidate"
    assert rows["astrobix_kp_houses"]["candidate_type"] == "runtime_form_candidate"


def test_kp_public_queue_is_registered():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    entry = next(
        row for row in index["packets"]
        if row["packet_id"] == "kp_public_worked_example_candidate_queue_2026_07_21"
    )

    assert entry["domain"] == "kp_precision_timing"
    assert entry["claim_status"] == "open_queue"
