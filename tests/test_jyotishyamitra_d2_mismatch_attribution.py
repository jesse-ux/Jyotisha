from __future__ import annotations

from scripts.jyotishyamitra_d2_mismatch_attribution import build_report


def test_d2_only_mismatch_is_kept_as_mapping_variant_observation() -> None:
    report = build_report({
        "scope": "jyotishyamitra_pinned_adapter_probe",
        "raw_sha256": "raw",
        "wheel_sha256": "wheel",
        "comparison": {"rows": [
            {"section": "D2", "field": "Sun", "local_status": "mismatch", "xalen_status": "mismatch"},
            {"section": "D9", "field": "Sun", "local_status": "match", "xalen_status": "match"},
        ]},
    })

    assert report["status"] == "d2_source_rule_attributed_external_truth_open"
    assert report["summary"]["joint_disagreement_count"] == 1
    assert report["summary"]["non_d2_local_disagreement_count"] == 0
    assert report["truth_matrix_allowed"] is False
    assert report["source_rule_attribution"]["source_member"] == "support/mod_divisional.py::hora_from_long"
    assert len(report["external_method_references"]) == 2
