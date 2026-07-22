import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/prashna_tajika_numeric_source_hunt_2026_07_22.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_prashna_tajika_source_hunt_records_candidates_without_oracle_upgrade():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    assert data["scope"] == "prashna_tajika_numeric_source_hunt"
    assert data["claim_status"] == "open_queue"
    assert data["truth_matrix_allowed"] is False
    assert data["production_tuning_allowed"] is False
    assert data["summary"]["candidate_count"] == 5
    assert "Source hunt only" in data["boundary"]
    assert "not oracle packets" in data["next_action"]


def test_prashna_tajika_source_hunt_covers_requested_domains():
    rows = {row["source_id"]: row for row in json.loads(PACKET.read_text(encoding="utf-8"))["candidate_sources"]}
    assert rows["prasna_marga_archive_text"]["domain"] == "Prashna/Sphuta"
    assert rows["eastrovedica_lesson49_sphuta_definitions"]["domain"] == "Sphuta"
    assert rows["scribd_gulika_mandi_numeric_candidate"]["domain"] == "Gulika"
    assert rows["astrogle_saham_formula_reference"]["domain"] == "Saham/Tajika"
    assert rows["varshaphala_ms_mehta_pdf_candidate"]["domain"] == "Tajika/Varshaphala"
    for row in rows.values():
        assert row["missing_for_numeric_packet"]


def test_prashna_tajika_source_hunt_is_indexed():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    packet = packets["prashna_tajika_numeric_source_hunt_2026_07_22"]
    assert packet["claim_status"] == "open_queue"
    assert packet["consumer_policy"] == "research_observation_only"
