import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "references/oracle/kp_observation_sync_contract_2026_07_22.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_kp_observation_sync_contract_is_calculable_displayable_not_predictive():
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert data["scope"] == "kp_observation_sync_contract"
    assert data["claim_status"] == "observation_only"
    assert data["runtime_status"] == "calculable"
    assert data["display_status"] == "displayable_with_warning"
    assert data["prediction_status"] == "not_verified_prediction"
    assert data["truth_matrix_allowed"] is False
    assert data["allowed_claim_level"] == "technical_observation"
    assert "verified event timing" in data["forbidden_claims"]


def test_kp_observation_sync_contract_links_required_evidence():
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert data["evidence_refs"] == [
        "references/oracle/kp_exact_cusp_invocation_closure_2026_07_21.json",
        "references/oracle/kp_archive_numeric_extraction_result_2026_07_21.json",
        "references/oracle/roxyapi_kp_surface_contract_2026_07_21.json"
    ]
    fields = data["display_fields"]
    assert {"cusp_longitude", "nakshatra_lord", "sub_lord", "sub_sub_lord"} <= set(fields)
    assert data["sync_targets"]["skill"] == "reference_only_with_boundary"
    assert data["sync_targets"]["api"] == "observation_endpoint_allowed"
    assert data["sync_targets"]["ui"] == "capability_center_badge_only"


def test_kp_observation_sync_contract_is_indexed():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    packet = packets["kp_observation_sync_contract_2026_07_22"]
    assert packet["claim_status"] == "observation_only"
    assert packet["consumer_policy"] == "research_observation_only"
