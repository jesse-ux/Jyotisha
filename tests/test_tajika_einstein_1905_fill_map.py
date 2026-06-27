#!/usr/bin/env python3
"""Tests for the Einstein 1905 Tajika annual human fill map."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "benchmark" / "tajika_einstein_1905_fill_map.md"


def test_tajika_einstein_1905_fill_map_is_field_level_and_actionable() -> None:
    text = DOC.read_text(encoding="utf-8")

    assert "# Tajika Einstein 1905 Fill Map" in text
    assert "template_einstein_varshaphala_1905_lahiri" in text
    assert "metadata.tool_name" in text
    assert "metadata.source_artifact" in text
    assert "target.solar_return_datetime" in text
    assert "target.varsha_lagna_deg" in text
    assert "target.muntha_sign" in text
    assert "target.year_lord" in text
    assert "target.mudda_dasha_first_lord" in text
    assert "target.sahams.punya_saham" in text
    assert "target.sahams.rajya_saham" in text
    assert "target.sahams.vivah_saham" in text
    assert "target.tajika_yogas" in text
    assert "JHora" in text
    assert "PyJHora" in text
    assert "solar-return convention" in text
