from __future__ import annotations

from pathlib import Path

from scripts.public_release_privacy_scan import build_report, scan_text


def test_public_release_privacy_scan_finds_private_birth_tuple() -> None:
    findings = scan_text(
        Path("sample.py"),
        '{"year": REDACTED_YEAR, "month": 4, "day": 17, "hour": 14, "minute": 49}',
    )

    assert {item["rule_id"] for item in findings} >= {"private_birth_dict_tuple"}


def test_public_release_privacy_scan_has_no_release_findings() -> None:
    report = build_report()

    assert report["status"] == "pass", report["findings"][:20]
    assert report["finding_count"] == 0
