#!/usr/bin/env python3
"""Acceptance tests for the long-report book root and its failure-discipline docs."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_ROOT = ROOT / "docs" / "reports" / "chart_research_REDACTED_DATE_REDACTED_TIME"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_report_book_root_has_required_navigation_and_seed_boundary() -> None:
    readme = _read(REPORT_ROOT / "README.md")
    book = _read(REPORT_ROOT / "book.md")

    assert "Source Priority" in readme
    assert "Seed Draft Mapping" in readme
    assert "current `Raman/Mean` run" in readme
    assert "PDF export: blocked" in readme

    assert "## Front Matter" in book
    assert "## Core Interpretation" in book
    assert "## Varga Layers" in book
    assert "## Appendices" in book


def test_high_value_chapters_expose_current_runtime_conflicts_and_not_old_draft_as_truth() -> None:
    chapter_01 = _read(REPORT_ROOT / "chapters" / "01_methodology_and_honesty_boundary.md")
    chapter_04 = _read(REPORT_ROOT / "chapters" / "04_d1_rasi_foundation.md")
    chapter_08 = _read(REPORT_ROOT / "chapters" / "08_varga_framework_overview.md")
    chapter_16 = _read(REPORT_ROOT / "chapters" / "16_parashara_vimshottari_yogini_kalachakra.md")
    appendix_f = _read(REPORT_ROOT / "appendices" / "F_technique_audit_table.md")

    assert "current raw JSON wins" in chapter_01
    assert "Numeric values there may differ" in chapter_04
    assert "seed draft's divisional table contains some values from an older calculation mouthpiece" in chapter_08
    assert "does **not** match older draft sections" in chapter_16
    assert "current run says Saturn/Venus active" in appendix_f


def test_error_ledger_exists_and_tracks_real_migration_failures() -> None:
    ledger = _read(REPORT_ROOT / "appendices" / "H_error_ledger_and_preflight.md")
    readme = _read(REPORT_ROOT / "README.md")

    assert "Read this before the next editing pass" in ledger
    assert "old draft vs current runtime conflict" in ledger
    assert "D9" in ledger
    assert "Saturn/Ketu" in ledger
    assert "Saturn/Venus" in ledger
    assert "before editing chapters" in readme
    assert "H_error_ledger_and_preflight.md" in readme


def test_report_book_counts_and_cross_links_stay_complete() -> None:
    chapters = sorted((REPORT_ROOT / "chapters").glob("*.md"))
    appendices = sorted((REPORT_ROOT / "appendices").glob("*.md"))
    book = _read(REPORT_ROOT / "book.md")
    readme = _read(REPORT_ROOT / "README.md")
    appendix_h = _read(REPORT_ROOT / "appendices" / "H_error_ledger_and_preflight.md")

    assert len(chapters) == 22
    assert len(appendices) == 8
    assert "current runtime wins" in appendix_h
    assert "Appendix H: error ledger and preflight" in readme
    assert "[H. Error Ledger and Preflight]" in book
    assert "D9 Leo 10.7493" in appendix_h


def test_runtime_truth_markers_exist_in_key_chapters() -> None:
    chapter_08 = _read(REPORT_ROOT / "chapters" / "08_varga_framework_overview.md")
    chapter_15 = _read(REPORT_ROOT / "chapters" / "15_jaimini_chara_karaka_arudha_narayana.md")
    chapter_20 = _read(REPORT_ROOT / "chapters" / "20_future_period_windows_2026_2063.md")

    assert "D9 | Leo 10.7493" in chapter_08
    assert "A10 / Karma Pada = `Capricorn`" in chapter_15
    assert "Saturn/Venus" in chapter_20


def test_varga_topic_chapters_are_no_longer_skeleton_only() -> None:
    chapter_09 = _read(REPORT_ROOT / "chapters" / "09_d2_d11_wealth_structure.md")
    chapter_10 = _read(REPORT_ROOT / "chapters" / "10_d3_d4_d7_d12_family_property_lineage.md")
    chapter_11 = _read(REPORT_ROOT / "chapters" / "11_d9_marriage_dharma_and_relationship_pattern.md")
    chapter_12 = _read(REPORT_ROOT / "chapters" / "12_d10_career_status_and_public_work.md")
    chapter_13 = _read(REPORT_ROOT / "chapters" / "13_d16_d20_d24_d27_d30_special_topics.md")
    chapter_14 = _read(REPORT_ROOT / "chapters" / "14_d40_d45_d60_karmic_layers.md")

    assert "Skeleton only." not in chapter_09
    assert "finance_strict_evidence" in chapter_09
    assert "D2 Hora" in chapter_09

    assert "Skeleton only." not in chapter_10
    assert "D4 Chaturthamsa" in chapter_10
    assert "D12 Dwadasamsa" in chapter_10

    assert "Skeleton only." not in chapter_11
    assert "relationship_strict_evidence" in chapter_11
    assert "D9" in chapter_11

    assert "Skeleton only." not in chapter_12
    assert "career_strict_evidence" in chapter_12
    assert "A10 Karma Pada" in chapter_12

    assert "Skeleton only." not in chapter_13
    assert "Vimsopaka" in chapter_13
    assert "D30" in chapter_13

    assert "Skeleton only." not in chapter_14
    assert "D60" in chapter_14
    assert "birth-time sensitive" in chapter_14


def test_remaining_high_value_chapters_are_grounded_and_not_skeletons() -> None:
    chapter_17 = _read(REPORT_ROOT / "chapters" / "17_transit_tajika_varshaphala_2026_2063.md")
    chapter_19 = _read(REPORT_ROOT / "chapters" / "19_past_event_validation_and_conflict_notes.md")
    chapter_21 = _read(REPORT_ROOT / "chapters" / "21_remedies_practice_and_limits.md")

    assert "Skeleton only." not in chapter_17
    assert "solar_return" in chapter_17
    assert "tajika" in chapter_17
    assert "dasha convergence" in chapter_17.lower()

    assert "Skeleton only." not in chapter_19
    assert "historical_event_backtest.py" in chapter_19
    assert "strong_hit / weak_hit / miss / blocked" in chapter_19
    assert "Appendix H" in chapter_19

    assert "Skeleton only." not in chapter_21
    assert "BPHS补救系统 v1.0" in chapter_21
    assert "low-risk measures first" in chapter_21
    assert "gemstones" in chapter_21


def test_front_matter_and_appendix_tables_are_no_longer_placeholders() -> None:
    chapter_02 = _read(REPORT_ROOT / "chapters" / "02_birth_data_chart_core_and_engine_contract.md")
    chapter_03 = _read(REPORT_ROOT / "chapters" / "03_executive_synthesis.md")
    appendix_a = _read(REPORT_ROOT / "appendices" / "A_raw_chart_tables.md")
    appendix_b = _read(REPORT_ROOT / "appendices" / "B_dasha_boundaries_full.md")
    appendix_c = _read(REPORT_ROOT / "appendices" / "C_varga_positions_full.md")
    appendix_d = _read(REPORT_ROOT / "appendices" / "D_shadbala_ashtakavarga_tables.md")

    assert "What belongs here" not in chapter_02
    assert "local_engine_fallback" in chapter_02
    assert "official_evidence" in chapter_02

    assert "Skeleton only." not in chapter_03
    assert "high-structure, late-ripening chart" in chapter_03

    assert "Ready to expand" not in appendix_a
    assert "Core chart table" in appendix_a
    assert "Sun | Aries" in appendix_a

    assert "Ready to expand" not in appendix_b
    assert "Current Vimshottari" in appendix_b
    assert "Current Narayana" in appendix_b

    assert "Ready to expand" not in appendix_c
    assert "Key ascendants" in appendix_c
    assert "D10 | Sagittarius 25.277" in appendix_c

    assert "Ready to expand" not in appendix_d
    assert "Shadbala ranking" in appendix_d
    assert "SAV summary" in appendix_d
