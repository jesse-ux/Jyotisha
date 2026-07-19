from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_DIR = ROOT / "references/oracle"
REGISTRIES = [
    "kp_precision_timing_gap_registry_2026_07_19.json",
    "muhurta_full_system_gap_registry_2026_07_19.json",
    "ashtakavarga_advanced_usage_gap_registry_2026_07_19.json",
    "compatibility_full_system_gap_registry_2026_07_19.json",
]
REUSE_SWEEP = ROOT / "references/oracle/local_oss_reuse_sweep_kp_muhurta_av_compat_2026_07_19.json"
REQUIRED_FIELDS = {
    "technique_id",
    "local_code_status",
    "skill_invocation_status",
    "api_ui_entry_status",
    "external_oracle_status",
    "commercial_sync_status",
    "claim_boundary",
}


def _load(name: str) -> dict:
    return json.loads((REGISTRY_DIR / name).read_text(encoding="utf-8"))


def test_high_value_gap_registries_exist_and_keep_required_fields() -> None:
    for name in REGISTRIES:
        data = _load(name)
        assert data["status"] == "gap_registry_v1"
        assert data["production_tuning_allowed"] is False
        assert data["items"]
        for item in data["items"]:
            assert REQUIRED_FIELDS.issubset(item)
            assert item["claim_boundary"]
            assert item["commercial_sync_status"] in {
                "ready_after_guarded_contract",
                "research_only",
                "blocked_until_oracle",
                "not_for_commercial_runtime",
            }


def test_kp_registry_keeps_precision_timing_blocked_without_oracle() -> None:
    data = _load("kp_precision_timing_gap_registry_2026_07_19.json")
    ids = {item["technique_id"]: item for item in data["items"]}
    assert {"kp_cusps", "star_sub_lord", "ruling_planets", "kp_significators", "kp_horary"}.issubset(ids)
    assert ids["star_sub_lord"]["local_code_status"] == "minimal_probe_present"
    assert ids["star_sub_lord"]["external_oracle_status"] == "partial_sublord_csv_only"
    assert ids["ruling_planets"]["local_code_status"] == "minimal_probe_present"
    assert ids["kp_significators"]["local_code_status"] == "minimal_probe_present"
    assert ids["kp_significators"]["claim_boundary"].startswith("Reference/probe only")


def test_muhurta_registry_distinguishes_panchanga_from_full_muhurta() -> None:
    data = _load("muhurta_full_system_gap_registry_2026_07_19.json")
    ids = {item["technique_id"]: item for item in data["items"]}
    assert ids["panchanga_base"]["local_code_status"] == "present"
    assert ids["full_muhurta_scoring"]["local_code_status"] == "missing_runtime"
    assert ids["full_muhurta_scoring"]["claim_boundary"].startswith("Do not present")


def test_ashtakavarga_advanced_registry_keeps_advanced_usage_observation_only() -> None:
    data = _load("ashtakavarga_advanced_usage_gap_registry_2026_07_19.json")
    ids = {item["technique_id"]: item for item in data["items"]}
    assert ids["bav_sav_core"]["local_code_status"] == "present"
    assert ids["kakshya_transit"]["external_oracle_status"] == "missing"
    assert ids["annual_sav_timing_scan"]["commercial_sync_status"] == "blocked_until_oracle"


def test_compatibility_registry_separates_basic_koota_from_advanced_overlays() -> None:
    data = _load("compatibility_full_system_gap_registry_2026_07_19.json")
    ids = {item["technique_id"]: item for item in data["items"]}
    assert ids["ashtakoota_core"]["local_code_status"] == "present"
    assert ids["composite_davidson_charts"]["commercial_sync_status"] == "not_for_commercial_runtime"
    assert ids["relationship_av_overlay"]["external_oracle_status"] == "missing"


def test_local_oss_reuse_sweep_records_reusable_sources_without_truth_upgrade() -> None:
    data = json.loads(REUSE_SWEEP.read_text(encoding="utf-8"))
    assert data["status"] == "reuse_sweep_v1"
    assert data["production_tuning_allowed"] is False
    local_paths = {item["path"] for item in data["local_candidates"]}
    assert "scripts/kp_system.py" in local_paths
    assert "references/open_source_sources/VedicAstro" in local_paths
    assert "references/muhurta-complete-guide.md" in local_paths
    assert all(item["claim_boundary"] for item in data["local_candidates"])
    assert any(item["reuse_status"] == "AGPL oracle/reference only" for item in data["web_candidates"])
