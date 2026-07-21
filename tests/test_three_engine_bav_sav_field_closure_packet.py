import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/three_engine_bav_sav_field_closure_packet_2026_07_21.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_bav_sav_packet_classifies_without_truth_upgrade():
    data = json.loads(PACKET.read_text(encoding="utf-8"))

    assert data["scope"] == "three_engine_bav_sav_field_closure_packet"
    assert data["claim_status"] == "partial"
    assert data["truth_matrix_allowed"] is False
    assert data["summary"]["rows_total"] == 8
    assert data["summary"]["local_pyjhora_jyotishganit_agree"] == 5
    assert data["summary"]["multi_engine_variant"] == 3
    assert data["summary"]["truth_upgrades"] == 0


def test_bav_sav_rows_require_worked_examples_and_method_metadata():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    rows = {row["ticket_id"]: row for row in data["rows"]}

    assert rows["TEMCQ-011"]["closure_status"] == "partial_consensus_vedastro_variant_blocked"
    assert rows["TEMCQ-012"]["closure_status"] == "multi_engine_variant_worked_example_required"
    assert rows["TEMCQ-016"]["closure_status"] == "multi_engine_variant_worked_example_required"
    assert rows["TEMCQ-018"]["closure_status"] == "multi_engine_variant_worked_example_required"
    for row in rows.values():
        assert row["required_evidence"] == [
            "public worked BAV/SAV table",
            "contributor set",
            "Lagna inclusion policy",
            "shodhana state",
            "rashi order/orientation"
        ]
        assert row["claim_boundary"] == "ashtakavarga_table_comparison_only_no_formula_truth"


def test_bav_sav_packet_is_registered():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    entry = next(
        row for row in index["packets"]
        if row["packet_id"] == "three_engine_bav_sav_field_closure_packet_2026_07_21"
    )

    assert entry["domain"] == "three_engine_parity"
    assert entry["claim_status"] == "partial"
