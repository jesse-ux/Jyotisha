#!/usr/bin/env python3
"""Tests for skill-level high-granularity interpretation templates."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "references" / "interpretation_template_registry.json"


def test_interpretation_template_registry_covers_article_level_hard_topics() -> None:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))

    assert data["scope"] == "jyotish_interpretation_template_registry"
    templates = data["templates"]
    required = {
        "yogi_asc_tight_orb_wealth",
        "ashwini_talent_profile",
        "rtn_high_order_d9",
        "bhrigu_pada_all_event",
        "tithi_lord_relationship",
        "pancha_pakshi_swara_boundary",
        "lakshmi_dhana_activation_chain",
        "darakaraka_ul_spouse_depth",
    }
    assert required <= set(templates)

    for template_id in required:
        template = templates[template_id]
        assert template["status"] in {"frozen_template", "covered_template"}
        assert template["authority_level"] in {"A/B/C layered", "B/C guarded"}
        assert template["source_refs"]
        assert template["required_cross_checks"]
        assert template["confidence_ceiling"]
        assert template["forbidden_claims"]
        assert template["safe_output_patterns"]


def test_interpretation_template_validator_reports_skill_readiness() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/validate_interpretation_templates.py", "--format", "json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["scope"] == "jyotish_interpretation_template_validation"
    assert report["valid"] is True
    assert report["summary"]["template_count"] >= 8
    assert report["summary"]["problem_count"] == 0
    assert "yogi_asc_tight_orb_wealth" in report["summary"]["template_ids"]
    assert "lakshmi_dhana_activation_chain" in report["summary"]["template_ids"]
    assert "darakaraka_ul_spouse_depth" in report["summary"]["template_ids"]
