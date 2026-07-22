import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/panchanga_temcq_061_schema_packet_2026_07_21.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_panchanga_temcq_061_records_not_comparable_status():
    data = json.loads(PACKET.read_text(encoding="utf-8"))

    assert data["scope"] == "panchanga_temcq_061_schema_packet"
    assert data["ticket_id"] == "TEMCQ-061"
    assert data["claim_status"] == "open_queue"
    assert data["truth_matrix_allowed"] is False
    assert data["closure_status"] == "schema_mapping_required"
    assert data["summary"]["normalized_fields_ready"] == 0
    assert data["summary"]["truth_upgrades"] == 0


def test_panchanga_temcq_061_preserves_jyotishganit_raw_fields():
    data = json.loads(PACKET.read_text(encoding="utf-8"))

    assert data["jyotishganit_observed_raw"] == {
        "@type": "Panchanga",
        "karana": "Gara",
        "nakshatra": "Uttara Bhadrapada",
        "tithi": "Shukla Tritiya",
        "vaara": "Thursday",
        "yoga": "Shubha",
    }
    assert data["engine_field_status"]["local"] == "archived_panchanga_field_missing"
    assert data["engine_field_status"]["VedAstro"] == "shared_panchanga_endpoint_not_pinned"
    assert data["engine_field_status"]["PyJHora_JHora"] == "not_archived_as_normalized_panchanga"


def test_panchanga_temcq_061_requires_exact_schema_before_comparison():
    data = json.loads(PACKET.read_text(encoding="utf-8"))

    assert data["required_schema_fields"] == ["vaara", "tithi", "nakshatra", "yoga", "karana"]
    assert data["required_contract"] == [
        "weekday convention",
        "tithi naming and paksha convention",
        "nakshatra spelling/diacritic alias table",
        "yoga calculation convention",
        "karana naming convention",
        "sunrise-relative vs birth-moment rule"
    ]
    assert data["boundary"] == "panchanga_schema_mapping_only_no_numeric_truth"


def test_panchanga_temcq_061_is_registered():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    entry = next(
        row for row in index["packets"]
        if row["packet_id"] == "panchanga_temcq_061_schema_packet_2026_07_21"
    )

    assert entry["domain"] == "three_engine_parity"
    assert entry["claim_status"] == "open_queue"
