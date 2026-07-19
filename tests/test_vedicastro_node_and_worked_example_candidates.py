import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_d10_node_attribution_keeps_rahu_ketu_partial():
    data = json.loads((ROOT / "references/oracle/d10_rahu_ketu_node_mode_attribution_2026_07_19.json").read_text(encoding="utf-8"))
    assert data["claim_status"] == "partial"
    assert data["production_tuning_allowed"] is False
    assert data["truth_matrix_allowed"] is False
    assert {row["body"] for row in data["remaining_rows"]} == {"Rahu", "Ketu"}
    assert data["status"] == "attributed_to_node_longitude_boundary"
    assert data["formula_observation"]["formula_delta_status"] == "same_observed_formula_shape"
    assert data["raw_node_boundary"]["local"]["Rahu"]["d10_part_index_zero_based"] == 3
    assert data["raw_node_boundary"]["jyotishganit"]["Rahu"]["d10_part_index_zero_based"] == 2
    assert all(row["probable_reason"] == "node_longitude_boundary_crossing" for row in data["remaining_rows"])


def test_vedicastro_flatlib_polars_probe_records_next_dependency_blocker():
    data = json.loads((ROOT / "references/oracle/vedicastro_kp_api_probe_flatlib_polars_tmp_2026_07_19.json").read_text(encoding="utf-8"))
    assert data["claim_status"] == "observation_only"
    assert data["dependency_probe"]["project_runtime_dependency_allowed"] is False
    assert "flatlib.const" in data["runtime_probe"]["error"]
    assert data["truth_matrix_allowed"] is False


def test_vedicastro_sidereal_flatlib_install_probe_records_timeout_blocker():
    data = json.loads((ROOT / "references/oracle/vedicastro_flatlib_sidereal_install_probe_2026_07_19.json").read_text(encoding="utf-8"))
    assert data["claim_status"] == "observation_only"
    assert data["production_tuning_allowed"] is False
    assert data["attempted_package"] == "git+https://github.com/diliprk/flatlib.git@sidereal"
    assert data["status"] == "partial_runtime_surface_available"
    assert data["runtime_artifact"] == "references/oracle/vedicastro_kp_runtime_surface_probe_2026_07_19.json"
    assert data["truth_matrix_allowed"] is False


def test_vedicastro_kp_runtime_surface_probe_is_callable_but_not_truth():
    data = json.loads((ROOT / "references/oracle/vedicastro_kp_runtime_surface_probe_2026_07_19.json").read_text(encoding="utf-8"))
    assert data["claim_status"] == "observation_only"
    assert data["status"] == "partial_runtime_surface_available"
    assert data["runtime_probe"]["import_status"] == "success"
    assert data["runtime_probe"]["sample_rl_nl_sl"]["SubLord"] == "Ketu"
    assert "AY_KRISHNAMURTI" in data["runtime_probe"]["sidereal_ayanamsa_constants_present"]


def test_public_worked_example_numeric_audit_has_no_oracle_ready_rows():
    data = json.loads((ROOT / "references/oracle/public_worked_example_candidate_numeric_audit_2026_07_19.json").read_text(encoding="utf-8"))
    assert data["claim_status"] == "open_queue"
    assert data["production_tuning_allowed"] is False
    assert all(row["numeric_packet_status"] != "oracle_ready" for row in data["candidates"])
    assert {row["topic"] for row in data["candidates"]} >= {"KP cusp star/sub/sub-sub", "Tarabala/Chandrabala", "Shadbala Virupa"}


def test_evidence_index_registers_current_blocker_artifacts():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    packets = {row["packet_id"]: row for row in index["packets"]}
    for packet_id in [
        "d10_rahu_ketu_node_mode_attribution",
        "vedicastro_kp_api_probe_flatlib_polars_tmp",
        "vedicastro_kp_runtime_surface_probe",
        "public_worked_example_candidate_numeric_audit",
    ]:
        assert packet_id in packets
