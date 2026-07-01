#!/usr/bin/env python3
"""Regression tests for research governance and main-chain documentation."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_local_drafts_disposition_table_covers_all_june_drafts() -> None:
    draft_dir = ROOT / "docs" / "research" / "local_drafts" / "2026-06"
    disposition_doc = ROOT / "docs" / "research" / "local_drafts_2026_06_disposition.md"

    text = disposition_doc.read_text(encoding="utf-8")
    draft_names = sorted(path.name for path in draft_dir.glob("*.md"))

    assert len(draft_names) == 93
    missing = [name for name in draft_names if name not in text]
    assert missing == []
    assert text.count("| promote |") >= 20
    assert "| archive |" in text
    assert "| reference-only |" in text
    assert ".workbuddy" in text
    assert "Do not move or delete files in this pass" in text


def test_unique_main_chain_map_names_runtime_entrypoints_and_boundaries() -> None:
    doc = ROOT / "docs" / "research" / "unique_main_chain_map_2026_07_01.md"
    text = doc.read_text(encoding="utf-8")

    required_tokens = [
        "mcp_server.py",
        "scripts/jyotish_api_server.py",
        "scripts/unified_consultation_orchestrator.py",
        "scripts/vedastro_service_adapter.py",
        "scripts/historical_event_backtest.py",
        "SKILL.md",
        "references/strict-workflow-router.md",
        "VedAstro official snapshot",
        "rectification gate",
        "historical event backtest",
        ".workbuddy",
    ]
    for token in required_tokens:
        assert token in text

    assert "source of truth" in text.lower()
    assert "must not import from `.workbuddy`" in text


def test_repo_cleanup_promotion_map_records_three_cleanup_layers() -> None:
    doc = ROOT / "docs" / "research" / "repo_cleanup_promotion_map_2026_07_01.md"
    text = doc.read_text(encoding="utf-8")

    required_tokens = [
        "docs/research/local_drafts/2026-06",
        "/Users/wuyongnaren/.gemini/antigravity-ide/brain",
        "/Users/wuyongnaren/.workbuddy/skills/jyotish-vedic-astrology",
        "recovery-only",
        "distribution mirror",
        "not runtime truth",
        "Promote First",
        "promote_third_repo_truth_pack_2026_07_01.md",
    ]
    for token in required_tokens:
        assert token in text


def test_promote_first_repo_truth_pack_reanchors_first_five_drafts() -> None:
    doc = ROOT / "docs" / "research" / "promote_first_repo_truth_pack_2026_07_01.md"
    text = doc.read_text(encoding="utf-8")

    required_tokens = [
        "antigravity_round36_tajika_sahams_external_closure_pack_2026_06_26.md",
        "antigravity_round37_dasha_external_oracle_shortest_closure_board_2026_06_26.md",
        "antigravity_round37_shadbala_absolute_value_frontier_board_2026_06_26.md",
        "antigravity_round39_yogi_wealth_bridge_audit_2026_06_28.md",
        "three_fronts_skill_depth_audit_2026_06_26.md",
        "oracle_closure_master_dashboard_latest.md",
        "public_benchmark_dashboard_latest.md",
        "skill_gap_truth_audit_latest.md",
        "half-finished canonical targets",
        "current code and regression truth",
    ]
    for token in required_tokens:
        assert token in text


def test_promote_second_repo_truth_pack_reanchors_second_batch_drafts() -> None:
    doc = ROOT / "docs" / "research" / "promote_second_repo_truth_pack_2026_07_01.md"
    text = doc.read_text(encoding="utf-8")

    required_tokens = [
        "antigravity_round31_single_source_of_truth_enforcement_2026_06_26.md",
        "antigravity_round31_whole_machine_fragment_reuse_fourth_pass_2026_06_26.md",
        "antigravity_round32_whole_machine_fragment_reuse_fifth_pass_2026_06_26.md",
        "antigravity_round37_public_benchmark_moat_board_2026_06_26.md",
        "antigravity_round38_public_benchmark_board_v2_2026_06_26.md",
        "antigravity_round38_dasha_external_oracle_packet_factory_2026_06_26.md",
        "antigravity_round38_shadbala_absolute_value_capture_matrix_2026_06_26.md",
        "antigravity_round40_article_technique_truth_arbitration_2026_06_27.md",
        "antigravity_round40_dasha_second_wave_closure_pack_2026_06_27.md",
        "first_oracle_packet_assistant.py",
        "packet assistant",
        "article-derived techniques must be source-graded",
    ]
    for token in required_tokens:
        assert token in text


def test_promote_third_repo_truth_pack_reanchors_third_batch_drafts() -> None:
    doc = ROOT / "docs" / "research" / "promote_third_repo_truth_pack_2026_07_01.md"
    text = doc.read_text(encoding="utf-8")

    required_tokens = [
        "antigravity_round36_asc_degree_yogi_tight_orb_wealth_pack_2026_06_26.md",
        "antigravity_round37_tajika_sahams_annual_closure_board_2026_06_26.md",
        "antigravity_round38_whole_machine_fragment_reuse_sixth_pass_2026_06_26.md",
        "antigravity_round40_shadbala_absolute_authority_ladder_2026_06_27.md",
        "antigravity_round40_tajika_annual_second_wave_board_2026_06_27.md",
        "yogi-asc-tight-orb-wealth-freeze-guide.md",
        "tajika_annual_benchmark_dashboard.py",
        "tithi-lord-freeze-execution-guide.md",
        "component-first",
        "half-finished canonical asset",
    ]
    for token in required_tokens:
        assert token in text


def test_promote_fourth_repo_truth_pack_reanchors_fourth_batch_drafts() -> None:
    doc = ROOT / "docs" / "research" / "promote_fourth_repo_truth_pack_2026_07_01.md"
    text = doc.read_text(encoding="utf-8")

    required_tokens = [
        "antigravity_round40_whole_machine_fragment_reuse_shortlist_2026_06_27.md",
        "dasha_accuracy_closure_status_2026_06_26.md",
        "dasha_code_only_priority_rerank_2026_06_26.md",
        "skill_fragment_map_and_source_of_truth_2026_06_26.md",
        "skill_truth_conflict_matrix_2026_06_26.md",
        "preflight_fragment_scan.py",
        "external_oracle_sanity_closure.py",
        "dasha_reference_audit.py",
        "narayana_dasha.py",
        "unique_main_chain_map_2026_07_01.md",
        "WorkBuddy",
        "主仓真源",
    ]
    for token in required_tokens:
        assert token in text
