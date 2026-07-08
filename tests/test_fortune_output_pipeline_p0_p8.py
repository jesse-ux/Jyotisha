#!/usr/bin/env python3
"""Golden-output and executable-queue contracts for fortune workflows."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from mcp_server import _collect_strict_evidence


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_OUTPUT_SECTIONS = [
    "promise",
    "activation",
    "manifestation",
    "label",
    "confidence_boundary",
]


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


def test_p0_chinese_golden_narratives_expose_required_contract_sections() -> None:
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

    for key in ["career_narrative", "finance_narrative", "relationship_narrative"]:
        narrative = snapshot[key]
        markdown = narrative["markdown"]
        assert narrative["output_template_status"] == "used"
        assert narrative["required_sections"] == REQUIRED_OUTPUT_SECTIONS
        for section in REQUIRED_OUTPUT_SECTIONS:
            assert f"{section}:" in markdown
        assert "MEVG" in markdown
        assert "Real Case Calibration" in markdown

    for route in ["career", "relationship", "finance"]:
        contract = snapshot["strict_workflow_contracts"][route]
        assert contract["output_template_contract"]["required_sections"] == REQUIRED_OUTPUT_SECTIONS


def test_p1_p2_mevg_queue_and_real_case_index_are_executable_contracts() -> None:
    strict = _collect_strict_evidence("career", _base_modules())

    queue = strict["mevg_collection_queue"]
    assert queue["status"] in {"queued", "blocked"}
    assert queue["execution_mode"] == "cache_ttl_free_tier_queue"
    assert queue["cache_ttl_hours"] >= 24
    assert queue["evidence_packet"]["packet_type"] == "mevg_external_evidence_packet"
    assert queue["failure_record"]["status"] == "blocked_until_external_fetch"
    assert queue["failure_record"]["blocked_reason"]

    case_layer = strict["real_case_calibration_layer"]
    assert case_layer["batch_id"] == "real_case_studies_batch1"
    assert case_layer["index_status"] == "available"
    assert case_layer["fallback_policy"] == "downgrade_without_matching_cases"
    assert "relationship" in case_layer["case_index_by_domain"]
    assert "docs/benchmark/legacy-marriage-v6.1/verify-results-v6.1.json" in case_layer["case_index_by_domain"]["relationship"]


def test_p3_p4_domain_layers_affect_judgement_and_technical_debt_is_split() -> None:
    strict = _collect_strict_evidence("career", _base_modules())
    judgement = strict["event_judgement"]

    for marker in [
        "dasha_timing_layer_used",
        "varga_strength_layer_used",
        "annual_special_layer_context",
        "modifier_obstacle_layer_used",
    ]:
        assert marker in judgement["secondary_context"]

    debt = strict["technical_debt_contract"]
    assert debt["narayana"]["status_breakdown"]["closed"]
    assert debt["narayana"]["status_breakdown"]["blocked"]
    assert debt["tajika"]["status_breakdown"]["closed"]
    assert debt["tajika"]["status_breakdown"]["blocked"]
    assert debt["oracle_parity"]["status"] == "blocked"


def test_p5_p6_p7_p8_frontend_batches_oracle_and_hygiene_are_visible() -> None:
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

    assert snapshot["remaining_priority1_batch_queue"]["batch_statuses"]["real_case_studies_batch1"] == "next"
    assert snapshot["oracle_parity_queue"]["systems"] == ["VedAstro", "PyJHora", "jyotishganit"]
    assert snapshot["oracle_parity_queue"]["priority_domains"] == ["Dasha", "Shadbala", "Tajika", "Narayana"]
    assert snapshot["release_hygiene_plan"]["git_sync_required"] is True
    assert snapshot["release_hygiene_plan"]["gc_log_policy"] == "separate_safe_cleanup_plan_required"

    main_js = (ROOT / "jyotish-app" / "main.js").read_text(encoding="utf-8")
    assert "core source refs" in main_js
    assert "why confidence downgraded" in main_js
    assert "next batch queue" in main_js
    assert "oracle parity" in main_js
