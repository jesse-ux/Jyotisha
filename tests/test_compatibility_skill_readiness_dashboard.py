import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "references" / "oracle" / "compatibility_skill_readiness_dashboard_2026_07_20.json"
INDEX = ROOT / "references" / "oracle" / "evidence_packet_index_2026_07_19.json"


def test_compatibility_skill_dashboard_generator_creates_bounded_layers():
    subprocess.run(
        ["python3", "scripts/compatibility_skill_readiness_dashboard.py"],
        cwd=ROOT,
        check=True,
    )

    data = json.loads(ARTIFACT.read_text())
    assert data["scope"] == "compatibility_skill_readiness_dashboard"
    assert data["claim_status"] == "partial"
    assert data["production_tuning_allowed"] is False
    assert data["truth_matrix_allowed"] is False

    layers = {layer["layer_id"]: layer for layer in data["layers"]}
    for layer_id in [
        "ashtakoota_guna_milan",
        "mangal_dosha",
        "d9_navamsa_relationship",
        "darakaraka",
        "upapada_lagna",
        "relationship_combinations",
        "relationship_ashtakavarga_overlay",
        "planet_lagna_kuta",
        "western_composite_davidson_boundary",
    ]:
        assert layer_id in layers

    assert layers["ashtakoota_guna_milan"]["runtime_status"] == "available"
    assert layers["ashtakoota_guna_milan"]["external_oracle_status"] == "partial"
    assert layers["relationship_ashtakavarga_overlay"]["runtime_status"] in {
        "missing_runtime",
        "registry_only",
    }
    assert layers["western_composite_davidson_boundary"]["commercial_sync_status"] == "out_of_scope_for_vedic_core"
    assert all("claim_boundary" in layer and layer["claim_boundary"] for layer in data["layers"])


def test_compatibility_dashboard_is_indexed_as_partial_contract_only_packet():
    index = json.loads(INDEX.read_text())
    packets = {packet["packet_id"]: packet for packet in index["packets"]}
    packet = packets["compatibility_skill_readiness_dashboard"]
    assert packet["path"] == "references/oracle/compatibility_skill_readiness_dashboard_2026_07_20.json"
    assert packet["domain"] == "compatibility"
    assert packet["claim_status"] == "partial"
    assert packet["consumer_policy"] == "research_to_commercial_contract_only"
