import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/three_engine_d2_field_closure_packet_2026_07_21.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_d2_packet_closes_local_pyjhora_jyotishganit_agreement_only():
    data = json.loads(PACKET.read_text(encoding="utf-8"))

    assert data["scope"] == "three_engine_d2_field_closure_packet"
    assert data["claim_status"] == "partial"
    assert data["truth_matrix_allowed"] is False
    assert data["summary"]["rows_total"] == 7
    assert data["summary"]["local_pyjhora_jyotishganit_agree"] == 7
    assert data["summary"]["vedastro_endpoint_semantics_blocked"] == 7
    assert data["summary"]["truth_upgrades"] == 0


def test_d2_rows_keep_vedastro_as_endpoint_semantics_not_formula_error():
    data = json.loads(PACKET.read_text(encoding="utf-8"))

    expected = {
        "Sun.sign": ("Leo", "Gemini"),
        "Moon.sign": ("Cancer", "Pisces"),
        "Mars.sign": ("Leo", "Aries"),
        "Mercury.sign": ("Leo", "Virgo"),
        "Jupiter.sign": ("Cancer", "Aquarius"),
        "Venus.sign": ("Cancer", "Leo"),
        "Saturn.sign": ("Cancer", "Gemini"),
    }
    rows = {row["field"]: row for row in data["rows"]}
    assert set(rows) == set(expected)
    for field, (consensus, vedastro) in expected.items():
        row = rows[field]
        assert row["ticket_id"].startswith("TEMCQ-00")
        assert row["local_value"] == consensus
        assert row["pyjhora_jhora_value"] == consensus
        assert row["jyotishganit_value"] == consensus
        assert row["vedastro_value"] == vedastro
        assert row["closure_status"] == "partial_consensus_vedastro_endpoint_blocked"
        assert row["claim_boundary"] == "three_engine_consensus_not_global_truth"


def test_d2_packet_is_registered_in_evidence_index():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    entry = next(
        row for row in index["packets"]
        if row["packet_id"] == "three_engine_d2_field_closure_packet_2026_07_21"
    )

    assert entry["domain"] == "three_engine_parity"
    assert entry["claim_status"] == "partial"
