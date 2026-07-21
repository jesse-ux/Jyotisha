import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/three_engine_d4_d9_d10_field_closure_packet_2026_07_21.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_d4_d9_d10_packet_closes_partial_consensus_only():
    data = json.loads(PACKET.read_text(encoding="utf-8"))

    assert data["scope"] == "three_engine_d4_d9_d10_field_closure_packet"
    assert data["claim_status"] == "partial"
    assert data["truth_matrix_allowed"] is False
    assert data["summary"]["rows_total"] == 3
    assert data["summary"]["local_pyjhora_jyotishganit_agree"] == 3
    assert data["summary"]["vedastro_endpoint_semantics_blocked"] == 3
    assert data["summary"]["truth_upgrades"] == 0


def test_d4_d9_d10_rows_preserve_exact_values_and_boundaries():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    rows = {(row["section"], row["field"]): row for row in data["rows"]}

    expected = {
        ("D4", "Moon.sign"): ("TEMCQ-008", "Gemini", "Pisces"),
        ("D9", "Moon.sign"): ("TEMCQ-009", "Scorpio", "Leo"),
        ("D10", "Moon.sign"): ("TEMCQ-010", "Pisces", "Sagittarius"),
    }
    assert set(rows) == set(expected)
    for key, (ticket, consensus, vedastro) in expected.items():
        row = rows[key]
        assert row["ticket_id"] == ticket
        assert row["local_value"] == consensus
        assert row["pyjhora_jhora_value"] == consensus
        assert row["jyotishganit_value"] == consensus
        assert row["vedastro_value"] == vedastro
        assert row["closure_status"] == "partial_consensus_vedastro_endpoint_blocked"
        assert row["claim_boundary"] == "three_engine_consensus_not_global_truth"


def test_d4_d9_d10_packet_is_registered():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    entry = next(
        row for row in index["packets"]
        if row["packet_id"] == "three_engine_d4_d9_d10_field_closure_packet_2026_07_21"
    )

    assert entry["domain"] == "three_engine_parity"
    assert entry["claim_status"] == "partial"
