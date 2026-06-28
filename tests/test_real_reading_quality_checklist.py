#!/usr/bin/env python3
"""Guard the real-reading structural quality checklist."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKLIST = ROOT / "references" / "real-reading-quality-checklist.md"


def test_real_reading_quality_checklist_exists_and_covers_structural_gaps() -> None:
    assert CHECKLIST.exists()
    text = CHECKLIST.read_text(encoding="utf-8")
    for token in [
        "Ayanamsa",
        "Node mode",
        "strict-workflow-router.md",
        "covered",
        "complete",
        "Functional Benefic/Malefic",
        "Yogakaraka",
        "functional neutrals",
        "Vimshottari + Narayana",
        "production_tuning_allowed",
        "Technique Audit Table",
    ]:
        assert token in text


def test_real_reading_quality_checklist_covers_domain_varga_expansion() -> None:
    text = CHECKLIST.read_text(encoding="utf-8")
    for token in [
        "D9 / UL / DK",
        "D10 / A10 / AmK/Karakamsha",
        "D2/D11",
        "D30 / D60",
        "Tajika annual",
    ]:
        assert token in text
