from __future__ import annotations

from pathlib import Path

from scripts.vedastro_identity_evidence_audit import build_audit

ROOT = Path(__file__).resolve().parents[1]


def test_vedastro_identity_evidence_audit_splits_runtime_and_hosted_identity() -> None:
    audit = build_audit(
        ROOT / "references/oracle/vedastro_identity_archive_2026_07_19.json",
        ROOT / "references/oracle/artifacts/vedastro_nuget_1_2_0_runtime_contract.json",
    )

    assert audit["scope"] == "vedastro_identity_evidence_audit"
    assert audit["package"] == "VedAstro.Library"
    assert audit["version"] == "1.2.0"
    assert audit["runtime_candidate_status"] == "complete"
    assert audit["hosted_identity_status"] == "blocked"
    assert audit["truth_upgrade_allowed"] is False
    assert audit["production_tuning_allowed"] is False


def test_vedastro_identity_evidence_audit_records_required_fields() -> None:
    audit = build_audit(
        ROOT / "references/oracle/vedastro_identity_archive_2026_07_19.json",
        ROOT / "references/oracle/artifacts/vedastro_nuget_1_2_0_runtime_contract.json",
    )

    evidence = {row["field"]: row for row in audit["evidence"]}
    for field in [
        "package_sha256",
        "library_dll_sha256",
        "assembly_version",
        "assembly_informational_version",
        "public_method_contracts",
        "runtime_image_digest",
    ]:
        assert evidence[field]["status"] == "complete"
        assert evidence[field]["value"]

    assert evidence["source_commit"]["status"] == "blocked"
    assert "not present" in evidence["source_commit"]["blocker"]
    assert audit["summary"] == {
        "required_field_count": 7,
        "complete_count": 6,
        "blocked_count": 1,
        "method_contract_count": 14,
    }
