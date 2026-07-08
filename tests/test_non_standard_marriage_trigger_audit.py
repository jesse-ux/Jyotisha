from __future__ import annotations

from scripts.non_standard_marriage_trigger_audit import audit_cases


def test_non_standard_marriage_trigger_audit_classifies_public_cases() -> None:
    report = audit_cases()

    assert report["scope"] == "non_standard_marriage_trigger_audit"
    assert report["case_count"] >= 5
    assert report["summary"]["non_standard_proxy_cases"] == report["case_count"]

    top_lords = {lord for lord, _count in report["summary"]["top_non_standard_lords"]}
    assert {"Rahu", "Mercury", "Moon", "Ketu"} <= top_lords

    links = {link for link, _count in report["summary"]["top_marriage_network_links"]}
    assert {"7L", "D9", "Jaimini"} <= links

    assert all(row["classification"] == "non_standard_proxy" for row in report["rows"])
