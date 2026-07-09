from __future__ import annotations

import json

from scripts.skill_release_manifest import build_report


def test_skill_release_manifest_defines_basic_and_premium_boundaries() -> None:
    report = build_report()
    editions = report["editions"]

    assert report["scope"] == "skill_release_manifest"
    assert set(editions) == {"basic_git", "premium_cloud_drive"}
    assert editions["basic_git"]["distribution"] == "public_git_repository"
    assert editions["premium_cloud_drive"]["distribution"] == "cloud_drive_zip"
    assert "https://github.com/732642856/yinduzhanxing" in editions["basic_git"]["source"]
    assert any("scripts/user_invocation_acceptance_check.py" in command for command in report["acceptance_commands"])
    assert any("scripts/public_release_privacy_scan.py" in command for command in report["acceptance_commands"])
    assert report["privacy_boundary"]["private_birth_data_allowed"] is False
    assert "personal_case_reports" in report["privacy_boundary"]["excluded_material"]
    assert report["external_engine_boundary"]["PyJHora/JHora"]["runtime_dependency"] is False
    assert report["external_engine_boundary"]["JHora desktop"]["runtime_dependency"] is False
    assert "official_raw_response" in report["external_engine_boundary"]["VedAstro"]["completion_gate"]


def test_skill_release_manifest_contains_no_private_birth_data() -> None:
    text = json.dumps(build_report(), ensure_ascii=False)

    for forbidden in ("REDACTED_DATE", "REDACTED_TIME", "REDACTED_HOSPITAL"):
        assert forbidden not in text
