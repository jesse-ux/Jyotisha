import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "references/oracle/commercial_startup_self_check_contract_2026_07_21.json"
GOLDEN = ROOT / "references/oracle/commercial_golden_oss_case_ci_contract_2026_07_21.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_commercial_startup_self_check_contract_requires_truth_source_identity():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    assert contract["scope"] == "commercial_startup_self_check_contract"
    required = set(contract["required_fields"])
    assert {
        "truth_source_path",
        "truth_source_git_commit",
        "skill_version",
        "evidence_packet_count",
        "artifact_gate_status",
        "privacy_artifact_status",
        "oracle_ready_summary",
    }.issubset(required)
    assert contract["reject_if"]["truth_source_path_contains"] == ["/WorkBuddy/", "/.workbuddy/"]
    assert contract["claim_boundary"] == "startup_identity_gate_only_not_business_runtime"


def test_commercial_golden_oss_ci_contract_uses_pyjhora_sphuta_probe():
    contract = json.loads(GOLDEN.read_text(encoding="utf-8"))

    assert contract["scope"] == "commercial_golden_oss_case_ci_contract"
    assert contract["golden_case"]["probe"] == "scripts/prashna_sphuta_oss_case_probe.py"
    assert contract["golden_case"]["expected_raw_hash"] == "f0705d205440ea8d7f39116042a0723d971f4ab79c94f7d448fc42d683d52326"
    assert contract["gate_policy"]["truth_upgrade_allowed"] is False
    assert contract["gate_policy"]["fail_if_probe_missing"] is True


def test_commercial_contracts_are_registered_in_evidence_index():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    ids = {row["packet_id"] for row in index["packets"]}

    assert "commercial_startup_self_check_contract_2026_07_21" in ids
    assert "commercial_golden_oss_case_ci_contract_2026_07_21" in ids
