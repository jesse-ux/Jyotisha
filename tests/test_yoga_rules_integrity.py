#!/usr/bin/env python3
"""Integrity checks for the data-driven Yoga rules registry."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
YOGA_RULES = ROOT / "references" / "yoga_rules.json"
LOGIC_REPORT = ROOT / "references" / "validation_logic_report.json"


def test_yoga_rule_ids_are_unique_and_counted() -> None:
    data = json.loads(YOGA_RULES.read_text(encoding="utf-8"))
    rules = data.get("rules", [])
    rule_ids = [rule.get("id") for rule in rules]

    assert len(rule_ids) == len(set(rule_ids))
    assert data.get("total_rules") == len(rules)
    assert data.get("total_enabled_rules") == sum(1 for rule in rules if rule.get("enabled", True))


def test_new_low_frequency_yogas_exist_and_are_enabled() -> None:
    data = json.loads(YOGA_RULES.read_text(encoding="utf-8"))
    rules_by_id = {rule.get("id"): rule for rule in data.get("rules", [])}

    for rule_id in [
        "bvr_106_indra_yoga",
        "bvr_107_makuta_yoga",
        "bvr_108_jaya_yoga",
        "bvr_109_putra_malika_yoga",
    ]:
        assert rule_id in rules_by_id
        assert rules_by_id[rule_id].get("enabled", True) is True


def test_logic_validation_report_contract() -> None:
    report = json.loads(LOGIC_REPORT.read_text(encoding="utf-8"))

    assert report["summary"]["charts_tested"] >= 60
    assert report["summary"]["comparable_rules"] >= 70
    assert "precision" in report["summary"]
    assert "recall" in report["summary"]
    assert "f1" in report["summary"]
