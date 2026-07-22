import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/panchanga_local_jyotishganit_comparison_2026_07_21.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_panchanga_local_jyotishganit_packet_scope_and_boundary():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    assert data["scope"] == "panchanga_local_jyotishganit_comparison"
    assert data["ticket_id"] == "TEMCQ-061"
    assert data["claim_status"] == "partial"
    assert data["truth_matrix_allowed"] is False
    assert data["production_tuning_allowed"] is False
    assert data["algorithm_reuse_policy"] == "reuse_existing_local_muhurta_calc_panchanga_no_new_algorithm"
    assert data["boundary"] == "local_jyotishganit_panchanga_field_observation_not_global_truth"


def test_panchanga_local_values_reuse_existing_muhurta_engine():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    assert data["source_local_method"] == "scripts/muhurta.py::calc_panchanga"
    assert data["local_normalized_raw"] == {
        "vaara": "Thursday",
        "tithi": "Shukla Tritiya",
        "nakshatra": "Uttara Bhadrapada",
        "yoga": "Shubha",
        "karana": "Garija",
    }
    assert data["jyotishganit_observed_raw"] == {
        "@type": "Panchanga",
        "karana": "Gara",
        "nakshatra": "Uttara Bhadrapada",
        "tithi": "Shukla Tritiya",
        "vaara": "Thursday",
        "yoga": "Shubha",
    }


def test_panchanga_field_comparison_distinguishes_alias_from_truth():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    rows = {row["field"]: row for row in data["field_comparison"]}
    assert set(rows) == {"vaara", "tithi", "nakshatra", "yoga", "karana"}
    assert [row["status"] for row in rows.values()].count("within_tolerance") == 4
    assert rows["karana"]["status"] == "alias_match"
    assert rows["karana"]["alias_rule"] == "Gara == Garija"
    assert data["summary"] == {
        "fields_total": 5,
        "within_tolerance": 4,
        "alias_match": 1,
        "formula_mismatch": 0,
        "unit_mismatch": 0,
        "truth_upgrades": 0,
    }


def test_panchanga_local_comparison_registered_in_evidence_index():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    entry = next(
        row for row in index["packets"]
        if row["packet_id"] == "panchanga_local_jyotishganit_comparison_2026_07_21"
    )
    assert entry["domain"] == "three_engine_parity"
    assert entry["claim_status"] == "partial"
    assert entry["consumer_policy"] == "research_observation_only"
