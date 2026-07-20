import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "references/oracle/oss_worked_example_source_matrix_2026_07_20.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_oss_worked_example_source_matrix_tracks_reusable_sources_and_boundaries():
    data = json.loads(MATRIX.read_text(encoding="utf-8"))
    assert data["scope"] == "oss_worked_example_source_matrix"
    assert data["claim_status"] == "source_intake_only"
    assert data["production_tuning_allowed"] is False
    assert data["truth_matrix_allowed"] is False

    rows = {row["source_id"]: row for row in data["sources"]}
    for source_id in [
        "pyjhora_pvr_tests",
        "jyotishganit_github",
        "vedicastro_kp_runtime",
        "fusionstrings_panchangam",
        "bidyashish_panchang",
        "kp_sub_lord_boundary_tables",
    ]:
        assert source_id in rows
        assert rows[source_id]["license_status"]
        assert rows[source_id]["case_usefulness"]
        assert rows[source_id]["promotion_boundary"]

    assert rows["pyjhora_pvr_tests"]["reuse_policy"] == "black_box_observation_only"
    assert rows["vedicastro_kp_runtime"]["candidate_domains"] == ["kp_precision_timing"]
    assert rows["fusionstrings_panchangam"]["license_status"] == "permissive_candidate_verify_repo_license"
    assert rows["kp_sub_lord_boundary_tables"]["numeric_packet_status"] == "candidate_requires_raw_capture_hash"


def test_oss_worked_example_source_matrix_is_indexed_without_truth_upgrade():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    packet = {
        row["packet_id"]: row for row in index["packets"]
    }["oss_worked_example_source_matrix_2026_07_20"]
    assert packet["claim_status"] == "source_intake_only"
    assert packet["consumer_policy"] == "research_observation_only"
