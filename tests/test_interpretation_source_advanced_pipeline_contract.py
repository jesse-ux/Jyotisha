#!/usr/bin/env python3
"""Contracts for the next interpretation-source pipeline stage."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from mcp_server import _collect_strict_evidence, _existing_interpretation_source_pack


ROOT = Path(__file__).resolve().parents[1]

DASHA_TIMING = [
    "references/vimshottari_dasha_guide.md",
    "references/pratyantar-calculation-guide.md",
    "references/condition-dasha-complete.md",
]
VARGA_STRENGTH = [
    "references/divisional-chart-deep-reading.md",
    "references/shadbala-complete-methodology.md",
    "references/ashtakavarga-complete-system.md",
]
ANNUAL_SPECIAL = [
    "references/tajika-yoga-complete-guide.md",
    "references/jaimini-complete-system.md",
    "references/kp-astrology-complete-system.md",
]
MODIFIER_OBSTACLE = [
    "references/argala-complete-guide.md",
    "references/badhaka-obstacle-planet-guide.md",
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
            "narayana_dasha": {
                "current_dasha": {
                    "md": {"sign": "Capricorn", "lord": "Saturn"},
                    "ad": {"sign": "Aquarius", "lord": "Saturn"},
                    "pd": {"sign": "Pisces", "lord": "Jupiter"},
                }
            },
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


def test_promote_batch2_is_split_into_domain_invocation_layers() -> None:
    source_pack = _existing_interpretation_source_pack()
    domain_layers = source_pack["domain_invocation_layers"]

    assert domain_layers["dasha_timing"]["source_refs"] == DASHA_TIMING
    assert domain_layers["varga_strength"]["source_refs"] == VARGA_STRENGTH
    assert domain_layers["annual_special"]["source_refs"] == ANNUAL_SPECIAL
    assert domain_layers["modifier_obstacle"]["source_refs"] == MODIFIER_OBSTACLE
    assert domain_layers["dasha_timing"]["required_in_routes"] == ["career", "relationship", "finance"]
    assert domain_layers["varga_strength"]["required_in_routes"] == ["career", "relationship", "finance"]

    for route in ["career", "relationship", "finance"]:
        strict = _collect_strict_evidence(route, _base_modules())
        invocation = strict["domain_invocation_contract"]
        assert invocation["dasha_timing"]["source_refs"] == DASHA_TIMING
        assert invocation["varga_strength"]["source_refs"] == VARGA_STRENGTH
        assert invocation["annual_special"]["source_refs"] == ANNUAL_SPECIAL
        assert invocation["modifier_obstacle"]["source_refs"] == MODIFIER_OBSTACLE


def test_output_template_mevg_case_and_technical_debt_contracts_are_present() -> None:
    strict = _collect_strict_evidence("career", _base_modules())

    template = strict["output_template_contract"]
    assert template["required_sections"] == ["promise", "activation", "manifestation", "label", "confidence_boundary"]
    assert template["language"] == "zh"
    assert template["golden_test_status"] == "required"

    mevg_queue = strict["mevg_collection_queue"]
    assert mevg_queue["status"] == "queued"
    assert mevg_queue["trigger"] == "fortune_question_strict_workflow"
    assert "global_web_evidence" in mevg_queue["required_jobs"]
    assert "source_grading" in mevg_queue["required_jobs"]
    assert "conflict_arbitration" in mevg_queue["required_jobs"]

    case_layer = strict["real_case_calibration_layer"]
    assert case_layer["status"] == "queued"
    assert case_layer["domain_buckets"] == ["career", "finance", "relationship", "health", "rectification", "timing"]
    assert case_layer["source_roots"] == ["references/real_case_studies", "docs/benchmark"]

    debt = strict["technical_debt_contract"]
    assert debt["narayana"]["status"] == "partial"
    assert "antardasha_pratyantar_oracle_parity" in debt["narayana"]["open_items"]
    assert debt["tajika"]["status"] == "partial"
    assert "solar_return_precision" in debt["tajika"]["open_items"]
    assert "muntha_placeholder_audit" in debt["tajika"]["open_items"]


def test_prompt_pack_frontend_and_remaining_batch_queue_expose_next_stage_contracts() -> None:
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
    snapshot = result["ai_prompt_pack"]["evidence_snapshot"]

    assert snapshot["domain_invocation_layers"]["dasha_timing"]["source_refs"] == DASHA_TIMING
    assert snapshot["output_template_contract"]["required_sections"][-1] == "confidence_boundary"
    assert snapshot["mevg_collection_queue"]["status"] == "queued"
    assert snapshot["real_case_calibration_layer"]["status"] == "queued"
    assert snapshot["technical_debt_contract"]["tajika"]["status"] == "partial"
    assert snapshot["remaining_priority1_batch_queue"]["next_batches"] == [
        "references_batch2",
        "vedastro_official_default_closure",
        "external_oracle_parity_batch",
        "install_usage_path_slimming",
    ]

    main_js = (ROOT / "jyotish-app" / "main.js").read_text(encoding="utf-8")
    assert "renderInterpretationSourceGovernancePanel" in main_js
    assert "Source Governance" in main_js
    assert "reference-only" in main_js
    assert "blocked non-runtime" in main_js
