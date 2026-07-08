#!/usr/bin/env python3
"""Regression tests for source-pack content contracts beyond visibility."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from mcp_server import _collect_strict_evidence, _existing_interpretation_source_pack


ROOT = Path(__file__).resolve().parents[1]

CORE5 = [
    "references/prediction-boundary-protocol.md",
    "references/event_judgment_skeleton.md",
    "references/planetary-dignity-complete-reference.md",
    "references/retrograde-combustion-war-guide.md",
    "references/transit-multi-reference-guide.md",
]

PROMOTE_BATCH2 = [
    "references/vimshottari_dasha_guide.md",
    "references/pratyantar-calculation-guide.md",
    "references/divisional-chart-deep-reading.md",
    "references/shadbala-complete-methodology.md",
    "references/ashtakavarga-complete-system.md",
    "references/tajika-yoga-complete-guide.md",
    "references/jaimini-complete-system.md",
    "references/kp-astrology-complete-system.md",
    "references/argala-complete-guide.md",
    "references/badhaka-obstacle-planet-guide.md",
    "references/condition-dasha-complete.md",
]

REFERENCE_ONLY = [
    "references/dasa-convergence-methodology.md",
    "references/multi-dasha-convergence-protocol.md",
    "references/yoga-strength-scoring-system.md",
]

NON_RUNTIME = [
    "references/varga-system-quick-reference.md",
    "references/yoga-list-chinese.md",
    "references/analysis-full-reading-v4.0.md",
    "references/analysis-full-reading-v1.8-review.md",
    "references/audit-skill-full-test-2026-05-04.md",
    "references/feature-gap-matrix-2026.md",
    "references/kp-practical-event-timing.md",
    "references/consultation-case-library.md",
]


def _base_modules() -> dict:
    return {
        "modules": {
            "chart": {
                "ascendant": {"sign": "Leo"},
                "planets": {
                    "Sun": {"status": "中性(Neutral)"},
                    "Moon": {"status": "中性(Neutral)"},
                    "Mercury": {"status": "中性(Neutral)"},
                    "Venus": {"status": "中性(Neutral)"},
                    "Jupiter": {"status": "中性(Neutral)"},
                    "Saturn": {"status": "中性(Neutral)"},
                },
            },
            "varga_full": {
                "D10_Dasamsa": {"summary": "career varga present"},
                "D9_Navamsha": {"summary": "relationship varga present"},
                "D2_Hora": {"summary": "wealth varga present"},
                "D11_Rudramsha": {"summary": "gains varga present"},
            },
            "special_lagnas": {
                "A10_Karma_Pada": {"sign": "Capricorn", "lord": "Saturn"},
                "Upapada_Lagna": {"sign": "Libra", "lord": "Venus"},
            },
            "jaimini": {
                "karakas": {
                    "Amatyakaraka": {"planet": "Mercury"},
                    "Atmakaraka": {"planet": "Sun"},
                    "Darakaraka": {"planet": "Venus"},
                },
                "karakamsha": {"karakamsha_sign": "Leo", "karakamsha_lord": "Sun"},
            },
            "dasha": {"current_dasha": {"mahadasha": "Mercury", "antardasha": "Sun"}},
            "narayana_dasha": {"current_dasha": {"sign": "Capricorn", "lord": "Saturn"}},
            "dasa_convergence": {
                "domain_activations": {
                    "career_status": {"convergence_level": "L2", "probability": "35-50%"},
                    "marriage_relationship": {"convergence_level": "L2", "probability": "35-50%"},
                    "wealth_income": {"convergence_level": "L2", "probability": "35-50%"},
                }
            },
        }
    }


def _run_engine(*args: str) -> dict:
    completed = subprocess.run(
        [sys.executable, "scripts/jyotish_engine.py", *args],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
        timeout=180,
    )
    assert completed.returncode == 0, completed.stderr[-2000:] or completed.stdout[-2000:]
    return json.loads(completed.stdout)


def test_core5_sources_drive_prediction_boundary_contract_for_all_strict_routes() -> None:
    for route in ["career", "relationship", "finance"]:
        strict = _collect_strict_evidence(route, _base_modules())
        contract = strict["prediction_boundary_contract"]

        assert contract["source_refs"] == CORE5
        assert contract["event_judgment_skeleton"]["required_sections"] == [
            "promise",
            "activation",
            "manifestation",
            "label",
        ]
        assert contract["promise"]["status"] == strict["adjudication_stages"]["promise"]["status"]
        assert contract["activation"]["status"] == strict["adjudication_stages"]["activation"]["status"]
        assert contract["manifestation"]["status"] == strict["adjudication_stages"]["manifestation"]["status"]
        assert contract["confidence_boundary"]["mevg_status"] == "blocked"
        assert contract["confidence_boundary"]["real_case_calibration_status"] == "blocked"
        assert contract["confidence_boundary"]["unverified_claim_policy"] == "downgrade_or_block"


def test_batch2_and_reference_only_layers_are_wired_without_polluting_truth_sources() -> None:
    source_pack = _existing_interpretation_source_pack()

    assert source_pack["promote_batch2_topic_layer"]["status"] == "available"
    assert source_pack["promote_batch2_topic_layer"]["source_refs"] == PROMOTE_BATCH2
    assert source_pack["reference_only_conflict_layer"]["status"] == "available"
    assert source_pack["reference_only_conflict_layer"]["source_refs"] == REFERENCE_ONLY
    assert source_pack["reference_only_conflict_layer"]["promotion_status"] == "reference_only"

    runtime_refs = set(source_pack["source_refs"])
    for path in PROMOTE_BATCH2 + REFERENCE_ONLY:
        assert path in runtime_refs
    for path in NON_RUNTIME:
        assert path not in runtime_refs

    inventory = source_pack["interpretation_source_inventory"]
    assert inventory["layers"]["promote_batch2_topic_sources"]["source_refs"] == PROMOTE_BATCH2
    assert inventory["layers"]["reference_only_conflict_sources"]["source_refs"] == REFERENCE_ONLY
    assert inventory["summary"]["blocked_non_runtime_count"] >= len(NON_RUNTIME)


def test_prompt_pack_and_real_reading_regression_expose_content_contracts() -> None:
    result = _run_engine(
        "full-reading",
        "--year",
        "1955",
        "--month",
        "2",
        "--day",
        "24",
        "--hour",
        "19",
        "--minute",
        "15",
        "--lat",
        "37.7749",
        "--lon",
        "-122.4194",
        "--tz",
        "8",
        "--today",
        "2026-07-02",
        "--transit-date",
        "2026-07-02",
    )
    prompt_pack = result["ai_prompt_pack"]
    snapshot = prompt_pack["evidence_snapshot"]

    assert snapshot["prediction_boundary_contract"]["source_refs"] == CORE5
    assert snapshot["interpretation_source_pack"]["core_rule_source_refs"] == CORE5
    assert snapshot["interpretation_source_pack"]["promote_batch2_source_refs"] == PROMOTE_BATCH2
    assert snapshot["interpretation_source_pack"]["reference_only_source_refs"] == REFERENCE_ONLY
    assert "必须按 promise → activation → manifestation → label 输出" in prompt_pack["prompt_zh"]
    assert "未完成 MEVG / Real Case Calibration 时必须降级或标 blocked" in prompt_pack["prompt_zh"]

    docs = prompt_pack["retrieval_plan"]["local_reference_docs"]
    for path in CORE5 + PROMOTE_BATCH2 + REFERENCE_ONLY:
        assert path in docs
    for path in NON_RUNTIME:
        assert path not in docs

    for route in ["career", "relationship", "finance"]:
        contract = snapshot["strict_workflow_contracts"][route]
        assert contract["prediction_boundary_contract"]["source_refs"] == CORE5
        audit = contract["technique_audit_summary"]
        assert audit["mevg_global_web_evidence"]["status"] == "blocked"
        assert audit["real_case_calibration"]["status"] == "blocked"
        assert audit["interpretation_source_pack"]["core_rule_source_refs"] == CORE5


def test_real_case_studies_batch1_is_exposed_as_local_retrieval_layer() -> None:
    source_pack = _existing_interpretation_source_pack()
    case_layer = source_pack["real_case_calibration_layer"]
    assert case_layer["batch_id"] == "real_case_studies_batch1"
    assert case_layer["index_status"] == "available"
    assert case_layer["status"] == "queued"
    assert "career" in case_layer["case_index_by_domain"]
    assert "finance" in case_layer["case_index_by_domain"]
    assert "relationship" in case_layer["case_index_by_domain"]
    assert (
        "references/real_case_studies/vedicka/career-success-poverty-prosperity.md"
        in case_layer["case_index_by_domain"]["career"]
    )
    assert (
        "docs/benchmark/legacy-marriage-v6.1/verify-results-v6.1.json"
        in case_layer["case_index_by_domain"]["relationship"]
    )
    assert (
        "references/real_case_studies/vedicka/career-success-poverty-prosperity.md"
        in source_pack["source_refs"]
    )
    assert source_pack["real_case_calibration"]["local_index_status"] == "available"
    assert source_pack["real_case_calibration"]["status"] == "blocked"


def test_open_source_batches_and_external_gaps_are_visible_without_polluting_truth() -> None:
    source_pack = _existing_interpretation_source_pack()

    rishi_layer = source_pack["rishi_ai_mcp_batch1_layer"]
    assert rishi_layer["status"] == "available"
    assert rishi_layer["promotion_status"] == "open_source_reference_layer"
    assert rishi_layer["runtime_truth_status"] == "not_primary_truth"
    assert "career" in rishi_layer["domain_map"]
    assert "relationship" in rishi_layer["domain_map"]
    assert "references/open_source_sources/rishi-ai-mcp/.agents/rules/rishi-ai.md" in rishi_layer["source_refs"]
    assert (
        "references/open_source_sources/rishi-ai-mcp/.agents/workflows/career-analysis.md"
        in rishi_layer["domain_map"]["career"]
    )

    vedic_layer = source_pack["vedic_astro_skills_batch1_layer"]
    assert vedic_layer["status"] == "available"
    assert vedic_layer["promotion_status"] == "external_skill_reference_layer"
    assert vedic_layer["runtime_truth_status"] == "not_primary_truth"
    assert "calculator" in vedic_layer["domain_map"]
    assert "references/open_source_sources/vedic-astro-skills/codex/skills/vedic-core/SKILL.md" in vedic_layer["source_refs"]
    assert (
        "references/open_source_sources/vedic-astro-skills/codex/skills/vedic-reader/resources/data_contract.md"
        in vedic_layer["domain_map"]["reader_validation"]
    )

    external_gaps = source_pack["external_closure_gap_layer"]
    assert external_gaps["vedastro_official"]["status"] == "blocked"
    assert external_gaps["oracle_parity"]["status"] == "blocked"
    assert external_gaps["install_usage_path"]["status"] == "needs_slimming"

    queue = source_pack["remaining_priority1_batch_queue"]
    assert queue["next_batches"] == [
        "references_batch2",
        "vedastro_official_default_closure",
        "external_oracle_parity_batch",
        "install_usage_path_slimming",
    ]
