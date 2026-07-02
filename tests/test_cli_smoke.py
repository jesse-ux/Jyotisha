#!/usr/bin/env python3
"""CLI smoke tests for critical Jyotish engine commands."""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path

from tests.run_golden_cases import run_cases

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "scripts" / "jyotish_engine.py"
GOLDEN_CASES = ROOT / "tests" / "golden" / "golden_cases.json"
BASE_BIRTH_ARGS = [
    "--year", "1990",
    "--month", "1",
    "--day", "1",
    "--hour", "12",
    "--minute", "0",
    "--lat", "39.9",
    "--lon", "116.4",
    "--tz", "8",
]


def run_engine(*args: str) -> dict:
    completed = subprocess.run(
        [sys.executable, str(ENGINE), *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def run_engine_text(*args: str) -> str:
    completed = subprocess.run(
        [sys.executable, str(ENGINE), *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def test_dignity_helper_uses_planet_attitude_to_sign_lord() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    import jyotish_engine

    assert jyotish_engine._get_dignity_level("Jupiter", "Virgo") == "ENEMY"
    assert jyotish_engine._get_dignity_level("Sun", "Sagittarius") == "FRIEND"


def test_dasha_accepts_birth_datetime_without_explicit_nakshatra() -> None:
    result = run_engine("dasha", *BASE_BIRTH_ARGS, "--today", "2026-01-01")
    assert "moon_nakshatra" in result
    assert len(result.get("timeline", [])) == 9
    assert result["timeline"][0]["is_balance"] is True


def test_dasha_accepts_second_for_auto_nakshatra_birth_datetime() -> None:
    birth_args = [
        "--year", "REDACTED_YEAR",
        "--month", "4",
        "--day", "17",
        "--hour", "14",
        "--minute", "45",
        "--second", "20",
        "--lat", "36.466667",
        "--lon", "114.2",
        "--tz", "8",
    ]

    result = run_engine("dasha", *birth_args, "--today", "2026-06-24")

    assert result["birth_date"] == "REDACTED_DATE"
    assert result["birth_time"] == "14:45:20"
    assert result["birth_datetime"] == "REDACTED_DATE 14:45:20"


def test_dasha_timeline_uses_full_birth_clock_for_audit_datetimes() -> None:
    moon_lon = "311.77867371832434"
    base_args = [
        "dasha",
        "--moon-lon", moon_lon,
        "--year", "REDACTED_YEAR",
        "--month", "4",
        "--day", "17",
        "--lat", "36.466667",
        "--lon", "114.2",
        "--tz", "8",
        "--today", "2026-06-24",
    ]

    midnight = run_engine(*base_args, "--hour", "0", "--minute", "0", "--second", "0")
    late = run_engine(*base_args, "--hour", "23", "--minute", "59", "--second", "59")

    assert midnight["timeline"][0]["start_datetime"].startswith("1986-05-23T07:59:50")
    assert late["timeline"][0]["start_datetime"].startswith("1986-05-24T07:59:49")
    assert midnight["timeline"][0]["start_datetime"] != late["timeline"][0]["start_datetime"]
    assert late["birth_datetime"] == "REDACTED_DATE 23:59:59"


def test_chart_accepts_second_and_preserves_birth_time_precision() -> None:
    birth_args = [
        "--year", "REDACTED_YEAR",
        "--month", "4",
        "--day", "17",
        "--hour", "14",
        "--minute", "45",
        "--lat", "36.466667",
        "--lon", "114.2",
        "--tz", "8",
    ]

    without_seconds = run_engine("chart", *birth_args)
    with_seconds = run_engine("chart", *birth_args, "--second", "20")

    assert with_seconds["birth_info"]["time"] == "14:45:20"
    assert with_seconds["birth_info"]["second"] == 20
    assert with_seconds["birth_info"]["julian_day"] > without_seconds["birth_info"]["julian_day"]


def test_chart_reports_richer_d1_dignity_labels_for_user_case() -> None:
    result = run_engine(
        "chart",
        "--year", "REDACTED_YEAR",
        "--month", "4",
        "--day", "17",
        "--hour", "14",
        "--minute", "45",
        "--second", "20",
        "--lat", "36.466667",
        "--lon", "114.2",
        "--tz", "8",
    )

    assert result["planets"]["Jupiter"]["sign"] == "Virgo"
    assert result["planets"]["Jupiter"]["status"] == "极敌(Great Enemy)"


def test_chart_table_mode_prints_readable_ascii_table() -> None:
    output = run_engine_text("chart", *BASE_BIRTH_ARGS, "--table")

    assert "Planet" in output
    assert "Sign" in output
    assert "House" in output
    assert "Ascendant" in output
    assert "Sun" in output
    assert "Moon" in output


def test_dasha_table_mode_prints_readable_ascii_table() -> None:
    output = run_engine_text(
        "dasha",
        *BASE_BIRTH_ARGS,
        "--today", "2026-01-01",
        "--table",
    )

    assert "Moon Nakshatra" in output
    assert "Reference Date" in output
    assert "Mahadasha" in output
    assert "Start" in output
    assert "End" in output
    assert "Current" in output
    assert "Rahu" in output or "Mars" in output


def test_shadbala_table_mode_prints_readable_ascii_table() -> None:
    output = run_engine_text("shadbala", *BASE_BIRTH_ARGS, "--table")

    assert "Shadbala Method" in output
    assert "Planet" in output
    assert "Rupas" in output
    assert "Strength" in output
    assert "Rank" in output
    assert "Sun" in output
    assert "Saturn" in output


def test_ashtakoot_table_mode_prints_readable_ascii_table() -> None:
    output = run_engine_text(
        "ashtakoot",
        "--m_year", "1990",
        "--m_month", "1",
        "--m_day", "1",
        "--m_hour", "12",
        "--m_minute", "0",
        "--m_lat", "39.9",
        "--m_lon", "116.4",
        "--m_tz", "8",
        "--f_year", "1992",
        "--f_month", "5",
        "--f_day", "10",
        "--f_hour", "9",
        "--f_minute", "30",
        "--f_lat", "31.2",
        "--f_lon", "121.5",
        "--f_tz", "8",
        "--table",
    )

    assert "Ashtakoot Method" in output
    assert "Kuta" in output
    assert "Score" in output
    assert "Total Score" in output
    assert "Match Approved" in output
    assert "Varna" in output
    assert "Nadi" in output


def test_full_reading_accepts_second_and_preserves_birth_time_precision() -> None:
    result = run_engine(
        "full-reading",
        "--year", "REDACTED_YEAR",
        "--month", "4",
        "--day", "17",
        "--hour", "14",
        "--minute", "45",
        "--second", "20",
        "--lat", "36.466667",
        "--lon", "114.2",
        "--tz", "8",
        "--today", "2026-06-24",
        "--transit-date", "2026-06-24",
    )

    assert result["birth_info"]["time"] == "14:45:20"
    assert result["birth_info"]["second"] == 20
    assert result["modules"]["chart"]["birth_info"]["time"] == "14:45:20"
    assert result["modules"]["dasha"]["birth_time"] == "14:45:20"
    assert result["modules"]["dasha"]["timeline"][0]["start_datetime"].startswith("1986-05-23T22:45:10")


def test_full_reading_reports_ayanamsa_metadata_and_ai_prompt_pack() -> None:
    result = run_engine(
        "full-reading",
        "--year", "REDACTED_YEAR",
        "--month", "4",
        "--day", "17",
        "--hour", "14",
        "--minute", "45",
        "--second", "20",
        "--lat", "36.466667",
        "--lon", "114.2",
        "--tz", "8",
        "--ayanamsa", "raman",
        "--today", "2026-06-24",
        "--transit-date", "2026-06-24",
    )

    chart_birth = result["modules"]["chart"]["birth_info"]
    assert chart_birth["ayanamsa_name"] == "raman"
    assert chart_birth["ayanamsa_display"] == "Raman"
    assert chart_birth["ayanamsa"] < 23

    prompt_pack = result["ai_prompt_pack"]
    assert prompt_pack["schema_version"] == 1
    assert prompt_pack["mode"] == "jyotish_structured_prompt_pack"
    assert "Raman" in prompt_pack["prompt_zh"]
    assert "不要仅凭单一配置下结论" in prompt_pack["prompt_zh"]
    assert "references/ai-reading-workflow-prompt.md" in prompt_pack["retrieval_plan"]["local_reference_docs"]
    assert "references/interpretation_template_registry.json" in prompt_pack["retrieval_plan"]["local_reference_docs"]
    assert "references/open_source_sources/vedic-astro-skills/codex/skills/vedic-core/resources/p1_p12.md" in prompt_pack["retrieval_plan"]["local_reference_docs"]
    assert "references/open_source_sources/vedic-astro-skills/codex/skills/vedic-core/resources/house_framework.md" in prompt_pack["retrieval_plan"]["local_reference_docs"]
    assert "references/mandatory-verification-gate-protocol.md" in prompt_pack["retrieval_plan"]["local_reference_docs"]
    assert prompt_pack["evidence_snapshot"]["ayanamsa"]["name"] == "raman"
    assert prompt_pack["evidence_snapshot"]["core"]["ascendant"]["sign"] == result["chart"]["ascendant"]["sign"]
    timing = prompt_pack["evidence_snapshot"]["timing"]
    assert timing["vimshottari"]["mahadasha"]
    assert "narayana" in timing
    assert isinstance(timing["convergence_top_domains"], list)
    functional = prompt_pack["evidence_snapshot"]["functional_benefic_malefic"]
    assert functional["status"] == "used"
    assert functional["ascendant"] == result["chart"]["ascendant"]["sign"]
    assert isinstance(functional["functional_benefics"], list)
    assert isinstance(functional["functional_malefics"], list)
    audit_table = prompt_pack["evidence_snapshot"]["technique_audit_table"]
    assert isinstance(audit_table, list)
    assert any(row["technique"] == "MEVG / Global Web Evidence" for row in audit_table)
    assert any(row["technique"] == "Real Case Calibration" for row in audit_table)
    assert any(row["technique"] == "Interpretation Source Pack" for row in audit_table)
    functional_rows = [row for row in audit_table if row["technique"] == "Functional Benefic/Malefic"]
    assert functional_rows
    assert functional_rows[0]["status"] == "used"
    assert "高严谨" in functional_rows[0]["note"]
    assert "关键功能吉星=" in functional_rows[0]["note"]
    assert "关键功能凶星=" in functional_rows[0]["note"]
    assert "功能中性星=" in functional_rows[0]["note"]
    assert "Yogakaraka=" in functional_rows[0]["note"]
    dasha_rows = [row for row in audit_table if row["technique"] == "Vimshottari + Narayana Cross-check"]
    assert dasha_rows
    assert dasha_rows[0]["status"] == "used"
    assert "Narayana" in dasha_rows[0]["note"]
    varga_rows = [row for row in audit_table if row["technique"] == "Relevant Vargas"]
    assert varga_rows
    assert varga_rows[0]["status"] == "used"
    assert "D9" in varga_rows[0]["note"]
    strength_rows = [row for row in audit_table if row["technique"] == "Strength Layers"]
    assert strength_rows
    assert strength_rows[0]["status"] == "used"
    assert "Shadbala" in strength_rows[0]["note"]
    relationship_synastry_rows = [row for row in audit_table if row["technique"] == "Relationship Synastry Taxonomy"]
    assert relationship_synastry_rows
    assert relationship_synastry_rows[0]["status"] in {"used", "blocked"}
    assert "relationship secondary_context" in relationship_synastry_rows[0]["note"]
    assert "compatibility support" in relationship_synastry_rows[0]["note"]
    assert "protective kuta support" in relationship_synastry_rows[0]["note"]
    relationship_narrative = prompt_pack["evidence_snapshot"]["relationship_narrative"]
    assert relationship_narrative["headline"]
    assert isinstance(relationship_narrative["strengths"], list)
    assert isinstance(relationship_narrative["risks"], list)
    assert isinstance(relationship_narrative["boundaries"], list)
    assert relationship_narrative["monthly_frame"]["primary_state"]["value"]
    assert relationship_narrative["monthly_frame"]["manifestation_mode"]["value"]
    assert relationship_narrative["monthly_frame"]["friction_source"]["value"]
    assert relationship_narrative["monthly_frame"]["time_confidence"]["value"]
    assert relationship_narrative["markdown"]
    assert "D9" in "".join(relationship_narrative["boundaries"])
    assert "dual dasha" in relationship_narrative["markdown"]
    career_narrative = prompt_pack["evidence_snapshot"]["career_narrative"]
    finance_narrative = prompt_pack["evidence_snapshot"]["finance_narrative"]
    assert career_narrative["headline"]
    assert finance_narrative["headline"]
    assert career_narrative["monthly_frame"]["primary_state"]["value"]
    assert finance_narrative["monthly_frame"]["primary_state"]["value"]
    vimsopaka_summary = prompt_pack["evidence_snapshot"]["vimsopaka_semantic_summary"]
    assert vimsopaka_summary["status"] == "used"
    assert isinstance(vimsopaka_summary["highlights"], list)
    assert isinstance(vimsopaka_summary["warnings"], list)
    oracle_progress = prompt_pack["evidence_snapshot"]["oracle_progress"]
    assert oracle_progress["scope"] == "external_oracle_evidence_validation"
    assert oracle_progress["valid_packets"] >= 4
    assert oracle_progress["ready_for_calibration"] >= 4
    assert oracle_progress["production_tuning_allowed"] is False
    assert oracle_progress["artifact_policy"] == "references/oracle/artifacts/"
    assert "external_verified" in oracle_progress["promotion_rule"]
    vedastro_overview = prompt_pack["evidence_snapshot"]["vedastro_overview"]
    assert vedastro_overview["status"] in {"ok", "network_execution_disabled", "service_endpoint_not_configured"}
    assert vedastro_overview["source"] == "vedastro_service_adapter_candidate"
    assert vedastro_overview["ingestion_profile"] == "main_entry_overview"
    assert vedastro_overview["visibility"] == "user_visible_overview_only"
    vedastro_official_snapshot = prompt_pack["evidence_snapshot"]["vedastro_official_full_snapshot"]
    assert "official_primary_evidence" in vedastro_official_snapshot
    assert "local_supplemental_evidence" in vedastro_official_snapshot
    assert "fallback_used" in vedastro_official_snapshot
    assert "blocked_items" in vedastro_official_snapshot
    assert "conflicts" in vedastro_official_snapshot
    assert "strict_workflow_contracts" in vedastro_official_snapshot
    assert "strict_workflow_routes_available" in vedastro_official_snapshot
    assert "relationship" in vedastro_official_snapshot["strict_workflow_contracts"]
    assert "career" in vedastro_official_snapshot["strict_workflow_contracts"]
    assert "finance" in vedastro_official_snapshot["strict_workflow_contracts"]
    career_contract = vedastro_official_snapshot["strict_workflow_contracts"]["career"]
    assert "adjudication_stages" in career_contract
    assert "multi_reference_reading_summary" in career_contract
    assert "modifier_frame" in career_contract["multi_reference_reading_summary"]
    assert vedastro_official_snapshot["strict_workflow_primary_route"] in {"relationship", "career", "finance", None}
    vedastro_rows = [row for row in audit_table if row["technique"] == "VedAstro Main Entry Overview"]
    assert vedastro_rows
    assert vedastro_rows[0]["status"] in {"used", "blocked"}
    assert "overview only" in vedastro_rows[0]["note"]
    assert "domain_statuses" in vedastro_rows[0]["note"]
    capability_pool = prompt_pack["evidence_snapshot"]["capability_evidence_pool"]
    assert capability_pool["scope"] == "backend_capability_evidence_pool"
    assert capability_pool["total_entries"] == 89
    assert capability_pool["conclusion_policy"]["all_89_entries_must_not_be_flattened_into_conclusions"] is True
    assert "后台备选证据池" in prompt_pack["prompt_zh"]


def test_full_reading_summary_exposes_stage_timing_contract() -> None:
    result = run_engine(
        "full-reading",
        "--year", "1990",
        "--month", "1",
        "--day", "1",
        "--hour", "12",
        "--minute", "0",
        "--lat", "39.9",
        "--lon", "116.4",
        "--tz", "8",
        "--today", "2026-01-01",
        "--transit-date", "2026-01-01",
    )

    summary = result["summary"]
    assert "stage_timings" in summary
    assert isinstance(summary["stage_timings"], list)
    assert summary["stage_timings"]
    first = summary["stage_timings"][0]
    assert "stage" in first
    assert "elapsed_seconds" in first
    assert "status" in first
    assert isinstance(first["elapsed_seconds"], (int, float))
    assert "slowest_stages" in summary
    assert isinstance(summary["slowest_stages"], list)
    assert summary["stage_timing_enabled"] is True


def test_full_reading_summary_exposes_unified_stage_groups() -> None:
    result = run_engine(
        "full-reading",
        "--year", "1990",
        "--month", "1",
        "--day", "1",
        "--hour", "12",
        "--minute", "0",
        "--lat", "39.9",
        "--lon", "116.4",
        "--tz", "8",
        "--today", "2026-01-01",
        "--transit-date", "2026-01-01",
    )

    summary = result["summary"]
    assert summary["stage_contract_version"] == 1
    assert isinstance(summary["stage_groups"], list)
    assert any(group["group"] == "official_evidence" for group in summary["stage_groups"])
    assert summary["cache_recommendations"]["api_chart_response"] == "recommended"
    assert summary["async_recommendations"]["chart_async_optional"] is True


def test_full_reading_prompt_pack_carries_compact_technique_audit_summary() -> None:
    result = run_engine(
        "full-reading",
        "--year", "REDACTED_YEAR",
        "--month", "4",
        "--day", "17",
        "--hour", "14",
        "--minute", "49",
        "--lat", "36.42",
        "--lon", "114.2",
        "--tz", "8",
        "--today", "2026-06-09",
        "--transit-date", "2026-06-09",
    )

    career = result["ai_prompt_pack"]["evidence_snapshot"]["strict_workflow_contracts"]["career"]
    assert "technique_audit_summary" in career
    assert career["technique_audit_summary"]["functional_benefic_malefic"]["gate"] == "hard"
    assert career["technique_audit_summary"]["interpretation_source_pack"]["used"] is True
    assert career["technique_audit_summary"]["mevg_global_web_evidence"]["status"] == "blocked"
    assert career["technique_audit_summary"]["real_case_calibration"]["status"] == "blocked"
    assert "audit_gate_frame" in career["multi_reference_reading_summary"]


def test_full_reading_generates_guided_topics_from_real_evidence() -> None:
    result = run_engine(
        "full-reading",
        "--year", "REDACTED_YEAR",
        "--month", "4",
        "--day", "17",
        "--hour", "14",
        "--minute", "49",
        "--lat", "36.42",
        "--lon", "114.2",
        "--tz", "8",
        "--today", "2026-06-09",
        "--transit-date", "2026-06-09",
    )

    topics = result["modules"]["guided_topics"]
    assert len(topics) >= 3
    assert result["summary"]["guided_topics"] == topics
    assert result["ai_prompt_pack"]["evidence_snapshot"]["guided_topics"] == topics

    for topic in topics[:3]:
        assert topic["id"]
        assert topic["title"]
        assert topic["reality_value"]
        assert topic["why_worth_exploring"]
        assert topic["evidence"]
        assert "strict_audit_gate" in topic
        assert topic["strict_audit_gate"]["functional_benefic_malefic"]["gate"] == "hard"
        assert topic["strict_audit_gate"]["relevant_vargas"]["gate"] == "hard"
        assert topic["strict_audit_gate"]["vimshottari_narayana_crosscheck"]["gate"] == "hard"
        assert topic["confidence"] in {"high", "medium", "low"}
        assert topic["vedastro"]["status"] in {"used", "blocked", "not_available"}
        assert topic["suggested_questions"]
        assert topic["answer_mode"] in {"tap_or_ask", "yes_no_or_free_text"}

    assert any(topic["id"] == "relationship_partnership" for topic in topics)
    assert any(topic["id"] == "career_direction" for topic in topics)
    assert any(topic["id"] == "birth_time_rectification" for topic in topics)


def test_full_reading_guided_topics_can_carry_official_day_signal_summary() -> None:
    result = {
        "modules": {
            "dasha": {
                "current_dasha": {
                    "lord": "Mercury",
                    "antardasha": {"lord": "Sun"},
                    "start": "2026-01-01",
                    "end": "2026-12-31",
                }
            },
            "dasa_convergence": {
                "domain_activations": {
                    "career_status": {"convergence_level": "L2"},
                    "marriage_partnership": {"convergence_level": "L1"},
                }
            },
            "chart": {"planets": {"Ketu": {"house": 10}}},
            "functional_benefic_malefic": {
                "status": "used",
                "functional_benefics": ["Mars", "Jupiter", "Sun"],
                "functional_malefics": ["Venus", "Mercury", "Saturn"],
            },
            "career_strict_evidence": {
                "technique_audit_summary": {
                    "functional_benefic_malefic": {"gate": "hard", "used": True},
                    "relevant_vargas": {"gate": "hard", "present_keys": ["d10_dasamsa", "a10_karma_pada"]},
                    "vimshottari_narayana_crosscheck": {"gate": "hard", "used": True},
                    "source_priority_boundary": {"gate": "boundary", "official": {}, "local": {}, "fallback_used": [], "blocked_items": [], "conflicts": []},
                },
                "monthly_adjudication_summary": {
                    "route": "career",
                    "primary_state": {"value": "推进"},
                    "manifestation_mode": {"value": "项目/合作推进"},
                    "friction_source": {"value": "结构调整"},
                    "time_confidence": {"value": "day_supported"},
                    "supporting_days": [
                        {"date": "2026-07-18", "summary": "事业机会进入日", "confidence": "high"}
                    ],
                },
                "present_evidence": {
                    "external_activation": {
                        "official_day_signals": [
                            {"date": "2026-07-18", "day_type": "opportunity_entry", "summary": "事业机会进入日", "confidence": "high"}
                        ]
                    }
                },
            },
            "relationship_strict_evidence": {
                "technique_audit_summary": {
                    "functional_benefic_malefic": {"gate": "hard", "used": True},
                    "relevant_vargas": {"gate": "hard", "present_keys": ["d9_navamsa", "upapada_lagna"]},
                    "vimshottari_narayana_crosscheck": {"gate": "hard", "used": True},
                    "source_priority_boundary": {"gate": "boundary", "official": {}, "local": {}, "fallback_used": [], "blocked_items": [], "conflicts": []},
                },
            },
            "finance_strict_evidence": {
                "technique_audit_summary": {
                    "functional_benefic_malefic": {"gate": "hard", "used": True},
                    "relevant_vargas": {"gate": "hard", "present_keys": ["d2_hora"]},
                    "vimshottari_narayana_crosscheck": {"gate": "hard", "used": True},
                    "source_priority_boundary": {"gate": "boundary", "official": {}, "local": {}, "fallback_used": [], "blocked_items": [], "conflicts": []},
                },
            },
            "vedastro_range_scan_result": {
                "status": "ok",
                "source_metadata": {"domain_statuses": {"career": "ok", "marriage": "blocked", "wealth": "blocked"}, "domain_event_counts": {"career": 1}},
                "top_events_by_domain": {},
            },
        },
        "chart": {"planets": {"Ketu": {"house": 10}}},
        "ai_prompt_pack": {"evidence_snapshot": {"strict_workflow_contracts": {}}},
        "birth_info": {"time": "REDACTED_TIME"},
    }

    from guided_topic_discovery import build_guided_topics

    topics = build_guided_topics(result)
    career = next(topic for topic in topics if topic["id"] == "career_direction")
    assert career["official_day_signal_summary"]["top_day"]["date"] == "2026-07-18"
    assert career["official_day_signal_summary"]["top_day"]["summary"] == "事业机会进入日"
    assert career["monthly_adjudication_summary"]["primary_state"]["value"] == "推进"
    assert career["monthly_adjudication_summary"]["supporting_days"][0]["date"] == "2026-07-18"
    assert career["strict_adjudication_bundle"]["monthly_adjudication_summary"] == career["monthly_adjudication_summary"]
    assert career["strict_adjudication_bundle"]["strict_audit_gate"] == career["strict_audit_gate"]


def test_full_reading_preserves_official_daily_window_fields_in_range_scan_result() -> None:
    result = run_engine(
        "full-reading",
        "--year", "REDACTED_YEAR",
        "--month", "4",
        "--day", "17",
        "--hour", "14",
        "--minute", "49",
        "--lat", "36.42",
        "--lon", "114.2",
        "--tz", "8",
        "--today", "2026-06-30",
        "--transit-date", "2026-06-30",
    )

    vedastro = result["modules"]["vedastro_range_scan_result"]
    assert "daily_windows" in vedastro
    assert "top_daily_window" in vedastro


def test_full_reading_auto_attaches_vedastro_main_entry_boundary() -> None:
    env = dict(**__import__("os").environ)
    env["VEDASTRO_API_ENDPOINT"] = "https://example.invalid/api"
    env["VEDASTRO_ENABLE_NETWORK"] = "0"
    env["JYOTISH_SKIP_LOCAL_ENV"] = "1"

    completed = subprocess.run(
        [
            sys.executable,
            str(ENGINE),
            "full-reading",
            *BASE_BIRTH_ARGS,
            "--today",
            "2026-06-29",
            "--transit-date",
            "2026-06-29",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    result = json.loads(completed.stdout)

    vedastro = result["modules"]["vedastro_range_scan_result"]
    assert vedastro["backend"] == "vedastro_service_adapter_candidate"
    assert vedastro["status"] == "network_execution_disabled"
    assert vedastro["source_metadata"]["ingestion_profile"] == "main_entry_overview"
    assert vedastro["source_metadata"]["reference_date"] == "2026-06-29"
    assert sorted(vedastro["source_metadata"]["domain_statuses"]) == ["career", "marriage", "wealth"]


def test_full_reading_exposes_sensitive_point_modules() -> None:
    result = run_engine(
        "full-reading",
        "--year", "REDACTED_YEAR",
        "--month", "4",
        "--day", "17",
        "--hour", "14",
        "--minute", "45",
        "--second", "20",
        "--lat", "36.466667",
        "--lon", "114.2",
        "--tz", "8",
        "--today", "2026-06-24",
        "--transit-date", "2026-06-24",
    )

    sensitive = result["modules"]["sensitive_points"]
    assert "bhrigu_bindu" in sensitive
    assert "sarpa_drekkana" in sensitive
    assert sensitive["bhrigu_bindu"]["sign"]
    assert isinstance(sensitive["sarpa_drekkana"], dict)
    for payload in sensitive["sarpa_drekkana"].values():
        assert payload["definition"] == "Cancer-2, Scorpio-1, Pisces-3"
        assert payload["is_sarpa_drekkana"] is True


def test_full_reading_uses_d9_context_for_navamsa_dignity() -> None:
    result = run_engine("full-reading", *BASE_BIRTH_ARGS)

    d9_jupiter = result["modules"]["d9_navamsa_expanded"]["Jupiter"]
    assert d9_jupiter["sign"] == "Capricorn"
    assert d9_jupiter["dignity"] == "NEECHA_BHANGA"


def test_full_reading_uses_d9_context_for_darakaraka_dignity() -> None:
    result = run_engine(
        "full-reading",
        "--year", "1992",
        "--month", "8",
        "--day", "25",
        "--hour", "23",
        "--minute", "10",
        "--lat", "35.6895",
        "--lon", "139.6917",
        "--tz", "9",
    )

    darakaraka = result["modules"]["jaimini"]["darakaraka"]
    assert darakaraka["dk_planet"] == "Sun"
    assert darakaraka["d9_sign"] == "Gemini"
    assert darakaraka["d9_dignity"] == "ENEMY"


def test_full_reading_uses_d9_context_for_vimsopaka_navamsa_dignity() -> None:
    result = run_engine(
        "full-reading",
        "--year", "1992",
        "--month", "8",
        "--day", "25",
        "--hour", "23",
        "--minute", "10",
        "--lat", "35.6895",
        "--lon", "139.6917",
        "--tz", "9",
    )

    navamsa = result["modules"]["vimsopaka"]["Sun"]["varga_scores"]["Navamsa"]
    assert navamsa["dignity"] == "Enemy"


def test_full_reading_maps_advanced_dignity_labels_into_vimsopaka_scores() -> None:
    result = run_engine("full-reading", *BASE_BIRTH_ARGS)

    jupiter_d9 = result["modules"]["d9_navamsa_expanded"]["Jupiter"]
    assert jupiter_d9["dignity"] == "NEECHA_BHANGA"

    jupiter_navamsa = result["modules"]["vimsopaka"]["Jupiter"]["varga_scores"]["Navamsa"]
    assert jupiter_navamsa["dignity"] == "Neecha Bhanga"
    assert isinstance(jupiter_navamsa["virupas"], (int, float))
    assert jupiter_navamsa["virupas"] > 2.0


def test_varga_cli_outputs_d9_and_d10() -> None:
    result = run_engine("varga", *BASE_BIRTH_ARGS, "--d9", "--d10")
    charts = result.get("divisional_charts", {})
    assert "D9_Navamsa" in charts
    assert "D10_Dasamsa" in charts
    assert "Moon" in charts["D9_Navamsa"]


def test_varga_full_cli_divisions_supports_high_vargas() -> None:
    result = run_engine(
        "varga-full",
        *BASE_BIRTH_ARGS,
        "--divisions",
        "D9,D60,D81,D108,D144",
    )

    assert "D81_Navamsa-Navamsa" in result
    assert "D108_Dwadasamsa-Navamsa" in result
    assert "D144_Dwadasamsa-Dwadasamsa" in result
    assert result["D144_Dwadasamsa-Dwadasamsa"]["planets"]["Moon"]["house"] in range(1, 13)


def test_full_reading_exposes_d11_for_wealth_strict_workflow() -> None:
    result = run_engine(
        "full-reading",
        *BASE_BIRTH_ARGS,
        "--today",
        "2026-07-01",
        "--target-year",
        "2026",
    )

    varga_full = result["modules"]["varga_full"]
    assert "D11_Rudramsa" in varga_full
    assert varga_full["D11_Rudramsa"]["planets"]["Moon"]["house"] in range(1, 13)


def test_muhurta_cli_scan_days_outputs_panchanga_without_tuple_crash() -> None:
    output = run_engine_text(
        "muhurta",
        "--date",
        "2026-06-28",
        "--activity",
        "business",
        "--scan-days",
        "2",
    )

    assert "Muhurta" in output
    assert "Panchanga" in output
    assert "2026-06-28" in output
    assert "unsupported operand type" not in output


def test_ashtakavarga_cli_keeps_sav_invariant() -> None:
    result = run_engine("ashtakavarga", *BASE_BIRTH_ARGS)
    assert result["sav"]["total"] == 337
    assert result["sav"]["valid"] is True
    assert result["all_bav_valid"] is True


def test_ashtakavarga_table_mode_prints_readable_ascii_table() -> None:
    output = run_engine_text("ashtakavarga", *BASE_BIRTH_ARGS, "--table")

    assert "Ashtakavarga Method" in output
    assert "SAV Total" in output
    assert "Strongest Signs" in output
    assert "Sign" in output
    assert "Score" in output
    assert "Level" in output
    assert "Sagittarius" in output
    assert "Aquarius" in output


def test_audit_capabilities_cli_validates_registry() -> None:
    result = run_engine("audit-capabilities", "--mode", "validate")
    assert result.get("valid") is True


def test_full_reading_golden_cases_cover_user_ready_output() -> None:
    result = run_cases(sys.executable, str(GOLDEN_CASES))
    assert result["valid"] is True, result
    assert result["total"] >= 3


def test_yoga_logic_validation_tolerates_algorithmic_yogas_without_rule_id() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    import validate_logic_v2

    results = [
        {"rule_id": "bvr_vosi_precise", "name": "Vosi Yoga"},
        {"id": "bvr_sunaphaa_precise", "name": "Sunapha Yoga"},
        {"name": "Algorithmic Solar Yoga"},
    ]

    assert validate_logic_v2.extract_skill_rule_ids(results) == {
        "bvr_vosi_precise",
        "bvr_sunaphaa_precise",
    }


def test_yoga_logic_validation_import_does_not_shadow_project_modules() -> None:
    before = list(sys.path)
    sys.path.insert(0, str(ROOT / "scripts"))
    import validate_logic_v2  # noqa: F401

    assert not sys.path[0].endswith(".workbuddy/skills/jyotish-vedic-astrology/scripts")
    sys.path[:] = before


def test_pytest_import_guard_restores_project_scripts_first() -> None:
    before = list(sys.path)
    try:
        sys.path.insert(0, str(ROOT / ".workbuddy" / "skills" / "jyotish-vedic-astrology" / "scripts"))

        import tests.conftest as conftest

        importlib.reload(conftest)
        assert sys.path[0] == str(ROOT / "scripts")
        assert str(ROOT / "scripts") == conftest.SCRIPTS
        assert conftest.WORKBUDDY_SKILL_SCRIPTS == ".workbuddy/skills/jyotish-vedic-astrology/scripts"
    finally:
        sys.path[:] = before
