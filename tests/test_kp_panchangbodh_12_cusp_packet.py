import json
from pathlib import Path

from scripts.kp_panchangbodh_replay_delta import build_delta
from scripts.numeric_oracle_packet_intake_validator import validate_document


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/cases/kp_12_cusp_panchangbodh_steve_jobs_2026_07_23.json"
VALIDATION = ROOT / "references/oracle/cases/kp_12_cusp_panchangbodh_steve_jobs_2026_07_23.validation.json"
DELTA = ROOT / "references/oracle/cases/kp_12_cusp_panchangbodh_steve_jobs_2026_07_23.local_replay_delta.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_panchangbodh_kp_12_cusp_packet_is_ready_for_replay_not_truth() -> None:
    packet_doc = json.loads(PACKET.read_text(encoding="utf-8"))
    validation = validate_document(packet_doc)
    packet = packet_doc["packets"][0]

    assert packet_doc["claim_status"] == "ready_for_replay_packet"
    assert packet_doc["truth_matrix_allowed"] is False
    assert packet_doc["production_tuning_allowed"] is False
    assert validation["rows"][0]["validation_status"] == "ready_for_replay_packet"
    assert len(packet["twelve_exact_cusp_longitudes"]) == 12
    assert len(packet["twelve_star_lords"]) == 12
    assert len(packet["twelve_sub_lords"]) == 12
    assert len(packet["twelve_sub_sub_lords"]) == 12
    assert packet["house_system"] == "Placidus explicitly visible"
    assert "not explicitly visible" in packet["ayanamsa"]
    assert "not_page_visible" in packet["timezone"]
    assert "not final truth" in packet["claim_boundary"]


def test_panchangbodh_kp_local_replay_delta_records_one_sub_sub_boundary_mismatch() -> None:
    delta = json.loads(DELTA.read_text(encoding="utf-8"))

    assert build_delta() == delta
    assert delta["claim_status"] == "replay_delta_observation_only"
    assert delta["truth_matrix_allowed"] is False
    assert delta["production_tuning_allowed"] is False
    assert delta["status"] == "mismatch_explained"
    assert delta["summary"]["row_count"] == 12
    assert delta["summary"]["max_abs_arcsec_delta"] <= 18
    assert delta["summary"]["lord_mismatch_count"] == 1
    assert delta["lord_mismatches"] == [
        {
            "cusp": 1,
            "field": "sub_sub_lord",
            "panchangbodh": {
                "star_lord": "Sun",
                "sub_lord": "Mars",
                "sub_sub_lord": "Moon",
            },
            "local_vedicastro": {
                "star_lord": "Sun",
                "sub_lord": "Mars",
                "sub_sub_lord": "Sun",
            },
        }
    ]


def test_panchangbodh_kp_packet_is_indexed_with_no_truth_upgrade_policy() -> None:
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    packets = {packet["packet_id"]: packet for packet in index["packets"]}
    packet = packets["kp_12_cusp_panchangbodh_steve_jobs_2026_07_23"]

    assert packet["path"] == "references/oracle/cases/kp_12_cusp_panchangbodh_steve_jobs_2026_07_23.json"
    assert packet["claim_status"] == "ready_for_replay_packet"
    assert packet["consumer_policy"] == "numeric_replay_packet_no_truth_upgrade"
    assert "not final truth" in packet["claim_boundary"]
    assert json.loads(VALIDATION.read_text(encoding="utf-8"))["summary"]["ready_packet_count"] == 1
