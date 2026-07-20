#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared orchestration contract for skill/MCP and web/API surfaces."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from diagnose_pyjhora_adapter import build_report as build_pyjhora_adapter_report
except Exception:  # pragma: no cover - import path varies in tests/CLI
    from scripts.diagnose_pyjhora_adapter import build_report as build_pyjhora_adapter_report

try:
    from diagnose_jyotishganit_adapter import build_report as build_jyotishganit_adapter_report
except Exception:  # pragma: no cover - import path varies in tests/CLI
    from scripts.diagnose_jyotishganit_adapter import build_report as build_jyotishganit_adapter_report

try:
    from cross_system_arbitrator import build_cross_system_arbitration
except Exception:  # pragma: no cover - import path varies in tests/CLI
    from scripts.cross_system_arbitrator import build_cross_system_arbitration

try:
    from functional_benefics import derive_functional_benefic_malefic
except Exception:  # pragma: no cover - import path varies in tests/CLI
    from scripts.functional_benefics import derive_functional_benefic_malefic

try:
    from real_case_replay_validator import validate_manifest as validate_real_case_replay_manifest
except Exception:  # pragma: no cover - import path varies in tests/CLI
    from scripts.real_case_replay_validator import validate_manifest as validate_real_case_replay_manifest


@dataclass(frozen=True)
class RouteDefinition:
    question_type: str
    primary_theme: str
    focus_techniques: list[str]
    display_label: str


class UnifiedConsultationOrchestrator:
    """Normalizes user intent and exposes a surface-agnostic workflow contract."""

    NAME = "UnifiedConsultationOrchestrator"
    SOURCE_PRIORITY = {
        "mode": "vedastro_official_snapshot_first",
        "priority": [
            "vedastro_official_snapshot",
            "local_supplemental_modules",
            "local_fallback_only_when_official_blocked",
        ],
        "boundary": (
            "Official VedAstro raw evidence is preferred; local modules supplement, "
            "cross-check, and fallback when official calls are blocked."
        ),
    }
    EVIDENCE_PACKET_REQUIRED_SECTIONS = [
        "D1",
        "D9",
        "D10",
        "D2",
        "D4",
        "planet_degrees",
        "house_degrees",
        "dasha_boundaries",
        "shadbala",
        "ashtakavarga",
        "yogas",
        "UL",
        "A7",
        "A10",
        "KP_cusp",
        "external_oracle_status",
        "vedastro_official_raw_response",
        "vedastro_official_raw_archive_manifest",
    ]
    _THEME_ALIASES = {
        "relationship": "marriage",
        "marriage": "marriage",
        "finance": "wealth",
        "money": "wealth",
        "wealth": "wealth",
        "career": "career",
        "health": "health",
        "spirituality": "spirituality",
        "事业": "career",
        "婚恋": "marriage",
        "婚姻": "marriage",
        "感情": "marriage",
        "财富": "wealth",
        "财运": "wealth",
        "健康": "health",
        "灵性": "spirituality",
    }
    _DEFAULT_THEMES = ["career", "marriage", "wealth"]
    _ALLOWED_THEMES = {"career", "marriage", "wealth", "health", "spirituality"}
    _ROUTE_DEFINITIONS = {
        "career": RouteDefinition(
            question_type="career",
            primary_theme="career",
            focus_techniques=["D10", "Dasha", "Shadbala", "Transit", "Narayana Dasha"],
            display_label="career",
        ),
        "relationship": RouteDefinition(
            question_type="relationship",
            primary_theme="marriage",
            focus_techniques=["D9", "UL Upapada", "Dasha", "Nakshatra", "Vivah Saham"],
            display_label="relationship",
        ),
        "finance": RouteDefinition(
            question_type="finance",
            primary_theme="wealth",
            focus_techniques=["D2", "D11", "Dasha", "Shadbala", "Ashtakavarga"],
            display_label="finance",
        ),
        "health": RouteDefinition(
            question_type="health",
            primary_theme="health",
            focus_techniques=["D1", "D6", "D8", "Dasha", "Shadbala", "non-medical boundary"],
            display_label="health",
        ),
        "timing": RouteDefinition(
            question_type="timing",
            primary_theme="career",
            focus_techniques=["Dasha", "Transit", "Double Transit", "Gochara"],
            display_label="timing",
        ),
        "general": RouteDefinition(
            question_type="general",
            primary_theme="career",
            focus_techniques=["D1", "D9", "Dasha", "Yoga", "Shadbala", "Ashtakavarga"],
            display_label="general",
        ),
    }
    _SYNC_STEPS_BY_ROUTE = {
        "career": ["compute_chart", "run_rectification_gate", "run_thematic_report"],
        "relationship": ["compute_chart", "run_rectification_gate", "run_thematic_report"],
        "finance": ["compute_chart", "run_rectification_gate", "run_thematic_report"],
        "health": ["compute_chart", "run_rectification_gate", "run_thematic_report"],
        "timing": ["compute_chart", "run_rectification_gate", "run_muhurta_panchanga", "run_thematic_report"],
        "general": ["compute_chart", "run_rectification_gate", "run_thematic_report"],
    }
    _ASYNC_CANDIDATES = [
        "historical_event_backtest",
        "official_event_radar_expansion",
        "extended_prompt_pack_refresh",
    ]

    def normalize_themes(self, raw: Any) -> list[str]:
        if raw in (None, "", "all"):
            values = list(self._DEFAULT_THEMES)
        elif isinstance(raw, str):
            values = [raw]
        elif isinstance(raw, list):
            values = raw
        else:
            raise ValueError("theme/themes must be a string, list, or all")

        normalized: list[str] = []
        for value in values:
            key = self._THEME_ALIASES.get(str(value).strip().lower(), str(value).strip().lower())
            if key not in self._ALLOWED_THEMES:
                raise ValueError(f"Unknown theme: {value}")
            if key not in normalized:
                normalized.append(key)
        return normalized or list(self._DEFAULT_THEMES)

    def resolve_route(self, question: str, themes: list[str] | None = None) -> dict[str, Any]:
        text = (question or "").lower()
        normalized_themes = themes or list(self._DEFAULT_THEMES)
        explicit_timing_tokens = ("when", "timing", "何时", "什么时候", "应期", "几月", "哪月", "哪天", "日期")

        domain_tokens = {
            "career": ("career", "job", "work", "promotion", "business", "profession", "事业", "工作", "升职", "生意"),
            "relationship": ("marriage", "married", "wedding", "relationship", "love", "spouse", "partner", "divorce", "婚恋", "婚姻", "感情", "配偶", "恋爱", "结婚", "marry"),
            "finance": ("money", "wealth", "finance", "investment", "property", "income", "财务", "财富", "投资", "房产", "收入"),
            "health": ("health", "illness", "medical", "disease", "vitality", "健康", "疾病", "病", "体力", "医疗"),
        }
        first_hits: list[tuple[int, str]] = []
        for route_name, tokens in domain_tokens.items():
            indexes = [text.find(token) for token in tokens if token in text]
            indexes = [idx for idx in indexes if idx >= 0]
            if indexes:
                first_hits.append((min(indexes), route_name))

        if text.strip() and any(token in text for token in explicit_timing_tokens) and "marriage" not in normalized_themes:
            route = self._ROUTE_DEFINITIONS["timing"]
        elif first_hits:
            route_name = sorted(first_hits, key=lambda item: item[0])[0][1]
            route = self._ROUTE_DEFINITIONS[route_name]
        elif not text.strip():
            route = self._ROUTE_DEFINITIONS["general"]
        elif any(token in text for token in ("when", "timing", "event", "prediction", "future", "应期", "预测", "何时", "将来")):
            route = self._ROUTE_DEFINITIONS["timing"]
        elif "career" in normalized_themes:
            route = self._ROUTE_DEFINITIONS["career"]
        elif "marriage" in normalized_themes:
            route = self._ROUTE_DEFINITIONS["relationship"]
        elif "wealth" in normalized_themes:
            route = self._ROUTE_DEFINITIONS["finance"]
        elif "health" in normalized_themes:
            route = self._ROUTE_DEFINITIONS["health"]
        else:
            route = self._ROUTE_DEFINITIONS["general"]

        return {
            "question_type": route.question_type,
            "primary_theme": route.primary_theme,
            "focus_techniques": list(route.focus_techniques),
            "display_label": route.display_label,
        }

    def shared_contract(
        self,
        *,
        entry_mode: str,
        question: str,
        themes: list[str],
        route_packet: dict[str, Any],
        surface: str,
    ) -> dict[str, Any]:
        return {
            "name": self.NAME,
            "surface": surface,
            "entry_mode": entry_mode,
            "question": question or "",
            "themes": list(themes),
            "route": dict(route_packet),
            "source_priority": {
                "mode": self.SOURCE_PRIORITY["mode"],
                "priority": list(self.SOURCE_PRIORITY["priority"]),
                "boundary": self.SOURCE_PRIORITY["boundary"],
            },
            "shared_capabilities": [
                "theme_normalization",
                "question_routing",
                "vedastro_official_priority",
                "rectification_gate_reuse",
                "thematic_report_reuse",
            ],
        }

    def runtime_planner(
        self,
        *,
        entry_mode: str,
        question: str,
        themes: list[str],
        route_packet: dict[str, Any],
        events: list[dict[str, Any]] | None,
        surface: str,
        high_rigor: bool,
    ) -> dict[str, Any]:
        route_name = route_packet.get("question_type") or "general"
        sync_steps = list(self._SYNC_STEPS_BY_ROUTE.get(route_name, self._SYNC_STEPS_BY_ROUTE["general"]))
        if entry_mode == "rectification":
            sync_steps = [step for step in sync_steps if step != "run_rectification_gate"]
            sync_steps.insert(0, "run_rectification_gate")
        elif entry_mode == "prashna":
            sync_steps = [step for step in sync_steps if step not in {"compute_chart", "run_rectification_gate"}]
            sync_steps.insert(0, "run_prashna")
        if high_rigor and "run_historical_event_backtest" not in sync_steps and events:
            sync_steps.append("run_historical_event_backtest")

        async_candidates = list(self._ASYNC_CANDIDATES)
        if not events:
            async_candidates = [step for step in async_candidates if step != "historical_event_backtest"]

        return {
            "planner_name": "UnifiedConsultationRuntimePlanner",
            "surface": surface,
            "entry_mode": entry_mode,
            "high_rigor": bool(high_rigor),
            "route": dict(route_packet),
            "question_context": {
                "question": question or "",
                "themes": list(themes),
                "event_count": len(events or []),
            },
            "sync_steps": sync_steps,
            "async_candidates": async_candidates,
            "source_priority": {
                "mode": self.SOURCE_PRIORITY["mode"],
                "priority": list(self.SOURCE_PRIORITY["priority"]),
                "boundary": self.SOURCE_PRIORITY["boundary"],
            },
            "reuse_contract": {
                "chart": "compute_chart",
                "rectification": "rectification_gate",
                "thematic_report": "thematic_report",
                "historical_backtest": "historical_event_backtest",
            },
            "boundary": (
                "This runtime planner unifies entry routing and module reuse. It does not imply that every VedAstro "
                "catalog method executes on every request; route-relevant official evidence is still subject to live "
                "availability, cache policy, and async limits."
            ),
        }

    @staticmethod
    def _vedastro_cloud_state(vedastro_official: dict[str, Any] | None) -> str:
        official = vedastro_official if isinstance(vedastro_official, dict) else {}
        runtime_truth = official.get("runtime_truth") if isinstance(official.get("runtime_truth"), dict) else {}
        layers = runtime_truth.get("official_execution_layers") if isinstance(runtime_truth.get("official_execution_layers"), dict) else {}
        status = str(runtime_truth.get("status") or official.get("status") or "blocked")
        fallback_active = bool(runtime_truth.get("fallback_active") or official.get("fallback_used"))
        if fallback_active:
            return "local_fallback"
        if layers.get("chart_core") == "ok" and status in {"ok", "partial", "available"}:
            return "official_verified"
        return "official_blocked"

    @staticmethod
    def _section(value: Any, source_path: str) -> dict[str, Any]:
        present = bool(value)
        return {
            "status": "used" if present else "missing",
            "source_path": source_path,
        }

    @staticmethod
    def _external_engine_cross_validation(vedastro_state: str) -> dict[str, Any]:
        repo_root = Path(__file__).resolve().parents[1]
        pyjhora_refs = [
            repo_root / "docs/benchmark/jyotish_external_oracle_closure_master_dashboard.json",
            repo_root / "references/oracle/artifacts/pyjhora_oracle_artifact_manifest.json",
        ]
        pyjhora_adapter = repo_root / "benchmarks/jyotish/scripts/run_pyjhora_compare.py"
        pyjhora_adapter_report = build_pyjhora_adapter_report()
        pyjhora_adapter_status = {
            "available": "available",
            "missing_dependency": f"blocked_missing_python_module:{pyjhora_adapter_report.get('missing_dependency') or 'jhora'}",
            "missing_adapter": "blocked_missing_adapter_script",
        }.get(str(pyjhora_adapter_report.get("status")), "runtime_error")
        jyotishganit_ref = repo_root / "references/open_source_sources/jyotishganit"
        jyotishganit_adapter_report = build_jyotishganit_adapter_report()

        engines = {
            "VedAstro": {
                "status": vedastro_state,
                "runtime_invoked": vedastro_state == "official_verified",
                "source_path": "vedastro_official.runtime_truth",
            },
            "PyJHora/JHora": {
                "status": (
                    "reference_available_not_runtime_invoked"
                    if any(path.exists() for path in pyjhora_refs)
                    else "blocked_no_reference_artifact"
                ),
                "runtime_invoked": False,
                "adapter_command": (
                    "python3 benchmarks/jyotish/scripts/run_pyjhora_compare.py"
                    if pyjhora_adapter.exists()
                    else None
                ),
                "adapter_status": pyjhora_adapter_status,
                "source_path": "docs/benchmark + references/oracle/artifacts",
            },
            "jyotishganit": {
                "status": (
                    "reference_available_not_runtime_invoked"
                    if jyotishganit_ref.exists()
                    else "blocked_no_reference_checkout"
                ),
                "runtime_invoked": False,
                "adapter_path": "references/open_source_sources/jyotishganit" if jyotishganit_ref.exists() else None,
                "adapter_status": jyotishganit_adapter_report.get("status"),
                "license": jyotishganit_adapter_report.get("license"),
                "source_path": "references/open_source_sources/jyotishganit",
            },
        }
        status = "complete" if all(item["runtime_invoked"] for item in engines.values()) else "partial"
        return {
            "status": status,
            "engines": engines,
            "boundary": (
                "This records runtime/reference closure state only. Reference artifacts do not mean the engine was "
                "invoked for the current consultation."
            ),
        }

    def machine_evidence_packet(
        self,
        *,
        chart: dict[str, Any] | None,
        route_packet: dict[str, Any],
        vedastro_official: dict[str, Any] | None = None,
        vedastro_archive_manifest: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        chart_data = chart if isinstance(chart, dict) else {}
        modules = chart_data.get("modules") if isinstance(chart_data.get("modules"), dict) else {}
        nested_chart = chart_data.get("chart") if isinstance(chart_data.get("chart"), dict) else {}
        base_chart = modules.get("chart") if isinstance(modules.get("chart"), dict) else nested_chart or chart_data
        varga = modules.get("varga_full") if isinstance(modules.get("varga_full"), dict) else {}
        special_lagnas = (
            chart_data.get("special_lagnas")
            if isinstance(chart_data.get("special_lagnas"), dict)
            else modules.get("special_lagnas") if isinstance(modules.get("special_lagnas"), dict) else {}
        )
        arudha_padas = (
            chart_data.get("arudha_padas")
            if isinstance(chart_data.get("arudha_padas"), dict)
            else modules.get("arudha_padas") if isinstance(modules.get("arudha_padas"), dict) else {}
        )
        if not arudha_padas and isinstance(modules.get("jaimini"), dict):
            jaimini_arudha = modules["jaimini"].get("arudha_padas")
            arudha_padas = jaimini_arudha if isinstance(jaimini_arudha, dict) else {}
        pada_map = arudha_padas.get("padas") if isinstance(arudha_padas.get("padas"), dict) else arudha_padas
        ascendant = base_chart.get("ascendant") if isinstance(base_chart.get("ascendant"), dict) else {}
        ascendant_sign = ascendant.get("sign") if isinstance(ascendant, dict) else None
        functional_layer = derive_functional_benefic_malefic(ascendant_sign)
        official = vedastro_official if isinstance(vedastro_official, dict) else {}
        archive_manifest = vedastro_archive_manifest if isinstance(vedastro_archive_manifest, dict) else {}
        raw_response = (
            official.get("raw_response")
            or official.get("official_raw_response")
            or official.get("raw_payload")
            or official.get("raw")
        )
        official_state = self._vedastro_cloud_state(vedastro_official)
        raw_response_section = (
            self._section(raw_response, "vedastro_official.raw_response")
            if official_state == "official_verified"
            else {
                "status": "received_unverified" if raw_response else "missing",
                "source_path": "vedastro_official.raw_response",
            }
        )
        sections = {
            "D1": self._section(
                base_chart.get("planets") and base_chart.get("ascendant"),
                "chart.planets+chart.ascendant",
            ),
            "D9": self._section(varga.get("D9_Navamsa") or varga.get("D9"), "modules.varga_full.D9"),
            "D10": self._section(varga.get("D10_Dasamsa") or varga.get("D10"), "modules.varga_full.D10"),
            "D2": self._section(varga.get("D2_Hora") or varga.get("D2"), "modules.varga_full.D2"),
            "D4": self._section(varga.get("D4_Chaturthamsa") or varga.get("D4"), "modules.varga_full.D4"),
            "planet_degrees": self._section(base_chart.get("planets"), "chart.planets"),
            "house_degrees": self._section(base_chart.get("houses") or chart_data.get("houses"), "chart.houses"),
            "dasha_boundaries": self._section(modules.get("dasha") or chart_data.get("dasha"), "modules.dasha"),
            "narayana_dasha": self._section(modules.get("narayana_dasha"), "modules.narayana_dasha"),
            "shadbala": self._section(modules.get("shadbala") or chart_data.get("shadbala"), "modules.shadbala"),
            "ashtakavarga": self._section(modules.get("ashtakavarga") or chart_data.get("ashtakavarga"), "modules.ashtakavarga"),
            "yogas": self._section(modules.get("yogas") or chart_data.get("yogas"), "modules.yogas"),
            "UL": self._section(
                pada_map.get("UL")
                or arudha_padas.get("upapada")
                or special_lagnas.get("UL")
                or special_lagnas.get("Upapada_Lagna"),
                "modules.arudha_padas.UL",
            ),
            "A7": self._section(
                pada_map.get("A7") or special_lagnas.get("A7") or special_lagnas.get("Darapada"),
                "modules.arudha_padas.A7",
            ),
            "A10": self._section(
                pada_map.get("A10") or special_lagnas.get("A10") or special_lagnas.get("A10_Karma_Pada"),
                "modules.arudha_padas.A10",
            ),
            "KP_cusp": self._section(modules.get("kp") or modules.get("kp_cusps") or chart_data.get("kp_cusps"), "modules.kp_cusps"),
            "functional_benefic_malefic": self._section(
                functional_layer if functional_layer.get("status") == "used" else None,
                "chart.ascendant.sign -> scripts.functional_benefics",
            ),
            "external_oracle_status": {
                "status": official_state,
                "source_path": "vedastro_official.runtime_truth",
            },
            "vedastro_official_raw_response": raw_response_section,
            "vedastro_official_raw_archive_manifest": self._section(
                archive_manifest if archive_manifest.get("archive_count") else None,
                "vedastro_gateway.archives",
            ),
        }
        missing = [name for name, section in sections.items() if section.get("status") == "missing"]
        signals = chart_data.get("cross_system_signals")
        if not isinstance(signals, list):
            signals = modules.get("cross_system_signals") if isinstance(modules.get("cross_system_signals"), list) else []
        return {
            "status": "complete" if not missing else "partial",
            "route": dict(route_packet),
            "required_sections": list(self.EVIDENCE_PACKET_REQUIRED_SECTIONS),
            "sections": sections,
            "functional_benefic_malefic": functional_layer,
            "signals": [item for item in signals if isinstance(item, dict)],
            "missing_sections": missing,
        }

    def real_case_calibration_catalog(
        self,
        *,
        route_packet: dict[str, Any],
        machine_evidence_packet: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        route = route_packet.get("question_type") or route_packet.get("primary_theme") or "general"
        if route == "marriage":
            route = "relationship"
        case_index_by_domain = {
            "career": ["references/real_case_studies/vedicka/career-success-poverty-prosperity.md"],
            "finance": ["references/real_case_studies/vedicka/career-success-poverty-prosperity.md"],
            "relationship": ["docs/benchmark/legacy-marriage-v6.1/verify-results-v6.1.json"],
        }
        case_profiles = {
            "references/real_case_studies/vedicka/career-success-poverty-prosperity.md": {
                "domains": ["career", "finance"],
                "evidence_sections": ["D1", "D10", "dasha_boundaries", "yogas"],
                "recorded_outcome": "poverty_to_prosperity_global_recognition",
                "event_trigger_keywords": ["Saturn dasha poverty", "Mercury dasha breakthrough", "Ketu dasha consolidation"],
            },
            "docs/benchmark/legacy-marriage-v6.1/verify-results-v6.1.json": {
                "domains": ["relationship"],
                "evidence_sections": ["D1", "D9", "UL", "dasha_boundaries"],
                "recorded_outcome": "relationship_structure_validation_dataset",
                "event_trigger_keywords": ["UL", "Darapada", "7th lord", "DK"],
            },
        }
        replay_manifest_path = Path(__file__).resolve().parents[1] / "references/real_case_calibration/replay_manifest.json"
        replay_manifest = validate_real_case_replay_manifest(replay_manifest_path)
        holdout_manifest_path = Path(__file__).resolve().parents[1] / "references/real_case_calibration/replay_manifest_holdout_v2.json"
        holdout_manifest = (
            validate_real_case_replay_manifest(holdout_manifest_path)
            if holdout_manifest_path.exists()
            else {
                "status": "blocked",
                "case_count": 0,
                "replay_ready_count": 0,
                "blocked_reason": "holdout_replay_manifest_missing",
                "path": "references/real_case_calibration/replay_manifest_holdout_v2.json",
            }
        )
        benchmark_path = Path(__file__).resolve().parents[1] / "docs/benchmark/public_real_case_20_case_closure_2026_07_11.json"
        if benchmark_path.exists():
            benchmark_payload = json.loads(benchmark_path.read_text(encoding="utf-8"))
            public_outcome_benchmark = {
                "status": "used",
                "path": "docs/benchmark/public_real_case_20_case_closure_2026_07_11.json",
                "summary": benchmark_payload.get("summary") or {},
                "method": benchmark_payload.get("method") or {},
                "strict_workflow_batch": benchmark_payload.get("strict_workflow_batch") or {},
                "holdout_promotion": benchmark_payload.get("holdout_promotion") or {},
                "technique_debt": benchmark_payload.get("technique_debt") or {},
            }
        else:
            public_outcome_benchmark = {
                "status": "blocked",
                "path": "docs/benchmark/public_real_case_20_case_closure_2026_07_11.json",
                "blocked_reason": "public_outcome_benchmark_missing",
            }
        supplemental_path = Path(__file__).resolve().parents[1] / "docs/benchmark/public_real_case_probe3_v2_2026_07_11.json"
        combined_observation_path = Path(__file__).resolve().parents[1] / "docs/benchmark/public_real_case_23_case_observation_2026_07_11.json"
        if supplemental_path.exists() and combined_observation_path.exists():
            supplemental_payload = json.loads(supplemental_path.read_text(encoding="utf-8"))
            combined_payload = json.loads(combined_observation_path.read_text(encoding="utf-8"))
            supplemental_public_probe = {
                "status": "used",
                "path": "docs/benchmark/public_real_case_probe3_v2_2026_07_11.json",
                "summary": supplemental_payload.get("summary") or {},
                "combined_observation": combined_payload.get("summary") or {},
                "boundary": "Three-case independent probe is contradictory generalization evidence, not a promotion or accuracy estimate.",
            }
        else:
            supplemental_public_probe = {
                "status": "blocked",
                "blocked_reason": "supplemental_public_probe_missing",
            }
        corrected_v21_path = Path(__file__).resolve().parents[1] / "docs/benchmark/public_real_case_23_case_v21_corrected_observation_2026_07_11.json"
        if corrected_v21_path.exists():
            corrected_payload = json.loads(corrected_v21_path.read_text(encoding="utf-8"))
            corrected_v21_observation = {
                "status": "used",
                "path": "docs/benchmark/public_real_case_23_case_v21_corrected_observation_2026_07_11.json",
                "summary": corrected_payload.get("summary") or {},
                "domain_summaries": corrected_payload.get("domain_summaries") or {},
                "ashtakavarga_audit_status": corrected_payload.get("ashtakavarga_audit_status"),
                "ashtakavarga_descriptive": corrected_payload.get("ashtakavarga_descriptive") or {},
                "boundary": corrected_payload.get("boundary"),
            }
        else:
            corrected_v21_observation = {
                "status": "blocked",
                "blocked_reason": "corrected_v21_observation_missing",
            }
        negative_control_path = Path(__file__).resolve().parents[1] / "docs/benchmark/public_real_case_negative_control_pilot_2026_07_11.json"
        if negative_control_path.exists():
            negative_payload = json.loads(negative_control_path.read_text(encoding="utf-8"))
            negative_summary = negative_payload.get("summary") or {}
            negative_control_pilot = {
                "status": "used",
                "path": "docs/benchmark/public_real_case_negative_control_pilot_2026_07_11.json",
                "summary": negative_summary,
                "boundary": negative_payload.get("boundary"),
            }
        else:
            negative_control_pilot = {
                "status": "blocked",
                "blocked_reason": "negative_control_pilot_missing",
            }
            negative_summary = {}
        annual_control_path = Path(__file__).resolve().parents[1] / "docs/benchmark/public_real_case_annual_control_pilot_2026_07_11.json"
        if annual_control_path.exists():
            annual_payload = json.loads(annual_control_path.read_text(encoding="utf-8"))
            annual_control_pilot = {
                "status": "used",
                "path": "docs/benchmark/public_real_case_annual_control_pilot_2026_07_11.json",
                "summary": annual_payload.get("summary") or {},
                "boundary": annual_payload.get("boundary"),
            }
        else:
            annual_control_pilot = {
                "status": "blocked",
                "blocked_reason": "annual_control_pilot_missing",
            }
        if negative_control_pilot.get("status") == "used" and annual_control_pilot.get("status") == "used":
            timing_precision_gate = {
                "status": "blocked",
                "maximum_supported_precision": "unvalidated_broad_window",
                "blocked_claims": ["exact_day", "exact_month_from_current_replay_score"],
                "domain_support": {"career": "blocked", "marriage": "partial_candidate"},
                "reason": "near_and_annual_control_rankings_below_gate",
                "observed_positive_top_1_rate": negative_summary.get("positive_top_1_rate"),
                "observed_positive_top_3_rate": negative_summary.get("positive_top_3_rate"),
                "annual_positive_top_1_rate": (annual_control_pilot.get("summary") or {}).get("positive_top_1_rate"),
            }
        else:
            timing_precision_gate = {
                "status": "blocked",
                "maximum_supported_precision": "unvalidated_broad_window",
                "blocked_claims": ["exact_day", "exact_month_from_current_replay_score"],
                "domain_support": {"career": "blocked", "marriage": "partial_candidate"},
                "reason": "control_pilot_missing",
            }
        candidate_refs = case_index_by_domain.get(route, [])
        packet = machine_evidence_packet if isinstance(machine_evidence_packet, dict) else {}
        sections = packet.get("sections") if isinstance(packet.get("sections"), dict) else {}
        used_sections = {name for name, section in sections.items() if isinstance(section, dict) and section.get("status") == "used"}
        dasha_used = "dasha_boundaries" in used_sections
        external_oracle_status = (
            sections.get("external_oracle_status", {}).get("status")
            if isinstance(sections.get("external_oracle_status"), dict)
            else "missing"
        )
        scored_candidates = []
        for ref in candidate_refs:
            profile = case_profiles.get(ref, {"domains": [], "evidence_sections": []})
            overlap = sorted(used_sections & set(profile["evidence_sections"]))
            trigger_score = (10 if dasha_used else 0) + (10 if external_oracle_status == "official_verified" else 0)
            score = (50 if route in profile["domains"] else 0) + min(30, len(overlap) * 5) + trigger_score
            scored_candidates.append({
                "case_source": ref,
                "score": score,
                "reference_grade": "partial_reference" if score >= 50 else "reference_only",
                "recorded_outcome": profile.get("recorded_outcome"),
                "similarities": {
                    "route_match": route in profile["domains"],
                    "evidence_section_overlap": overlap,
                },
                "differences": {
                    "unmatched_required_sections": sorted(set(profile["evidence_sections"]) - used_sections),
                },
                "event_trigger_match": {
                    "status": (
                        "partial_match_official_timing_available"
                        if dasha_used and external_oracle_status == "official_verified"
                        else "partial_match_official_timing_blocked"
                        if dasha_used
                        else "not_matched_missing_dasha"
                    ),
                    "checks": {
                        "dasha_boundaries": "used" if dasha_used else "missing",
                        "external_oracle_status": external_oracle_status,
                        "recorded_trigger_keywords": list(profile.get("event_trigger_keywords", [])),
                    },
                    "boundary": "Trigger check uses available timing evidence only; it is not event outcome validation.",
                },
                "outcome_validation": {
                    "status": "local_outcome_recorded_trigger_not_replayed",
                    "recorded_outcome": profile.get("recorded_outcome"),
                    "boundary": "Outcome is read from the local case source profile; this does not replay the case chart or prove similarity.",
                },
            })
        return {
            "status": "partial_scored" if scored_candidates else "catalog_available_matching_not_run",
            "batch_id": "real_case_studies_batch1",
            "route": route,
            "source_roots": ["references/real_case_studies", "references/real_case_calibration", "docs/benchmark"],
            "case_index_by_domain": case_index_by_domain,
            "required_replay_schema": "references/real_case_calibration/catalog.schema.json",
            "outcome_replay_manifest": replay_manifest,
            "holdout_replay_manifest": holdout_manifest,
            "public_outcome_benchmark": public_outcome_benchmark,
            "supplemental_public_probe": supplemental_public_probe,
            "corrected_v21_observation": corrected_v21_observation,
            "negative_control_pilot": negative_control_pilot,
            "annual_control_pilot": annual_control_pilot,
            "timing_precision_gate": timing_precision_gate,
            "candidate_refs": list(candidate_refs),
            "scored_candidates": scored_candidates,
            "reference_grade": scored_candidates[0]["reference_grade"] if scored_candidates else "ungraded_until_similarity_scored",
            "boundary": (
                "The public benchmark replays twenty dated outcomes, including a frozen ten-case holdout, but it contains positive events only. It can "
                "measure activation recall, not specificity or scientific predictive accuracy; user-chart "
                "similarity still requires separate structured matching."
            ),
        }

    def runtime_evidence_log(
        self,
        *,
        surface: str,
        entry_mode: str,
        route_packet: dict[str, Any],
        executed_steps: list[str],
        skipped_steps: list[str],
        vedastro_official: dict[str, Any] | None = None,
        interpretation_source_runtime_coverage: dict[str, Any] | None = None,
        machine_evidence_packet: dict[str, Any] | None = None,
        real_case_calibration: dict[str, Any] | None = None,
        western_evidence_packet: dict[str, Any] | None = None,
        blind: bool = False,
    ) -> dict[str, Any]:
        official = vedastro_official if isinstance(vedastro_official, dict) else {}
        runtime_truth = official.get("runtime_truth") if isinstance(official.get("runtime_truth"), dict) else {}
        vedastro_state = self._vedastro_cloud_state(official)
        external_cross_validation = self._external_engine_cross_validation(vedastro_state)
        blocked_items: list[str] = []
        if vedastro_state != "official_verified":
            blocked_items.append("vedastro_official_raw_snapshot_not_verified")
        if external_cross_validation["status"] != "complete":
            blocked_items.append("external_engine_cross_validation_partial")
        packet = machine_evidence_packet if isinstance(machine_evidence_packet, dict) else {}
        packet_status = packet.get("status") or "required_not_satisfied"
        packet_sections = packet.get("sections") if isinstance(packet.get("sections"), dict) else {}
        archive_section = packet_sections.get("vedastro_official_raw_archive_manifest")
        archive_status = (
            archive_section.get("status")
            if isinstance(archive_section, dict)
            else "required_not_satisfied"
        )
        if not packet:
            blocked_items.append("machine_evidence_packet_not_yet_materialized")
        elif packet_status != "complete":
            blocked_items.append("machine_evidence_packet_partial")
        if archive_status != "used":
            blocked_items.append("vedastro_official_raw_archive_manifest_missing")
        case_packet = real_case_calibration if isinstance(real_case_calibration, dict) else {}
        case_status = case_packet.get("status") or "required_not_satisfied"
        timing_precision = case_packet.get("timing_precision_gate") if isinstance(case_packet.get("timing_precision_gate"), dict) else {}
        timing_precision_status = timing_precision.get("status") or "blocked"
        functional_packet = packet.get("functional_benefic_malefic") if isinstance(packet.get("functional_benefic_malefic"), dict) else {}
        functional_status = functional_packet.get("status") or "blocked"
        if functional_status != "used":
            blocked_items.append("functional_benefic_malefic_blocked")
        if not case_packet:
            blocked_items.append("real_case_calibration_not_yet_materialized")
        elif case_status != "complete":
            blocked_items.append("real_case_calibration_partial")
        if timing_precision_status != "pass":
            blocked_items.append("timing_precision_gate_blocked")
        cross_system_arbitration = build_cross_system_arbitration(
            route_packet=route_packet,
            jyotish_evidence=packet,
            western_evidence=western_evidence_packet,
        )
        if cross_system_arbitration["status"] != "used":
            blocked_items.append("cross_system_arbitration_not_complete")
        technique_audit_table = [
            {
                "technique": "VedAstro Cloud State",
                "status": vedastro_state,
                "used": vedastro_state == "official_verified",
                "effect_on_confidence": (
                    "official_cloud_evidence_available"
                    if vedastro_state == "official_verified"
                    else "confidence_capped_without_verified_official_cloud"
                ),
            },
            {
                "technique": "VedAstro Raw Archive Manifest",
                "status": archive_status,
                "used": archive_status == "used",
                "effect_on_confidence": (
                    "official_raw_archive_is_auditable"
                    if archive_status == "used"
                    else "official_raw_archive_not_auditable_for_this_run"
                ),
            },
            {
                "technique": "External Engine Cross-Validation",
                "status": external_cross_validation["status"],
                "used": external_cross_validation["status"] == "complete",
                "effect_on_confidence": (
                    "three_engine_runtime_closure_available"
                    if external_cross_validation["status"] == "complete"
                    else "claims_capped_until_pyjhora_jhora_jyotishganit_are_invoked_for_this_run"
                ),
            },
            *cross_system_arbitration["technique_audit_rows"],
            {
                "technique": "Evidence Packet",
                "status": packet_status,
                "used": bool(packet),
                "effect_on_confidence": "complete_packet_required_for_high_confidence" if packet_status != "complete" else "supports_high_confidence",
            },
            {
                "technique": "Blind Technical Mode",
                "status": "used" if blind else "available_not_requested",
                "used": bool(blind),
                "effect_on_confidence": "prevents_conversation_feedback_leakage" if blind else "normal_runtime_mode",
            },
            {
                "technique": "MEVG / Global Web Evidence",
                "status": "blocked",
                "used": False,
                "effect_on_confidence": "caps_claims_until_global_web_evidence_runs",
            },
            {
                "technique": "Real Case Calibration",
                "status": case_status,
                "used": bool(case_packet),
                "effect_on_confidence": "partial_reference_only_until_outcome_replay" if case_status != "complete" else "supports_calibration",
            },
            {
                "technique": "Timing Precision Gate",
                "status": timing_precision_status,
                "used": bool(timing_precision),
                "maximum_supported_precision": timing_precision.get("maximum_supported_precision", "unvalidated_broad_window"),
                "blocked_claims": timing_precision.get("blocked_claims", ["exact_day", "exact_month_from_current_replay_score"]),
                "domain_support": timing_precision.get("domain_support", {}),
                "effect_on_confidence": "blocks_false_precision_until_control_date_rankings_pass",
            },
            {
                "technique": "Functional Benefic/Malefic",
                "status": functional_status,
                "used": functional_status == "used",
                "key_functional_benefics": functional_packet.get("functional_benefics", []),
                "key_functional_malefics": functional_packet.get("functional_malefics", []),
                "yogakarakas": functional_packet.get("yogakarakas", []),
                "effect_on_confidence": functional_packet.get(
                    "effect_on_confidence",
                    "high_rigor_claims_blocked_until_functional_nature_layer_is_present",
                ),
            },
        ]
        return {
            "name": "UnifiedConsultationRuntimeEvidenceLog",
            "surface": surface,
            "entry_mode": entry_mode,
            "route": dict(route_packet),
            "executed_steps": list(executed_steps),
            "skipped_steps": list(skipped_steps),
            "vedastro_cloud_state": vedastro_state,
            "vedastro_runtime_truth": dict(runtime_truth),
            "external_engine_cross_validation": external_cross_validation,
            "cross_system_arbitration": cross_system_arbitration,
            "source_priority": {
                "mode": self.SOURCE_PRIORITY["mode"],
                "priority": list(self.SOURCE_PRIORITY["priority"]),
            },
            "evidence_sources": {
                "vedastro_official": vedastro_state,
                "local_modules": "used" if executed_steps else "not_used",
                "interpretation_source_runtime_coverage": (
                    "used" if isinstance(interpretation_source_runtime_coverage, dict) and interpretation_source_runtime_coverage else "not_used"
                ),
            },
            "evidence_packet_contract": {
                "status": packet_status,
                "required_sections": list(self.EVIDENCE_PACKET_REQUIRED_SECTIONS),
                "missing_sections": packet.get("missing_sections", []),
            },
            "blind_technical_mode": {
                "enabled": bool(blind),
                "allowed_sources": ["birth_payload", "pdf", "machine_evidence_packet"],
                "disallowed_sources": ["conversation_feedback", "memory_linked_personal_history"],
            },
            "real_case_calibration": {
                "status": case_status,
                "required_fields": [
                    "case_source",
                    "chart_similarity",
                    "transit_or_dasha_trigger",
                    "event",
                    "similarities",
                    "differences",
                    "reference_grade",
                ],
            },
            "quality_gate": {
                "technique_audit_table_required": True,
                "technique_audit_table": technique_audit_table,
                "required_rows": [
                    "VedAstro Cloud State",
                    "VedAstro Raw Archive Manifest",
                    "External Engine Cross-Validation",
                    "Western Cross-Validation",
                    "Cross-System Arbitration",
                    "Evidence Packet",
                    "Blind Technical Mode",
                    "MEVG / Global Web Evidence",
                    "Real Case Calibration",
                    "Timing Precision Gate",
                    "Functional Benefic/Malefic",
                ],
                "status": "blocked" if blocked_items else "pass",
                "blocked_items": blocked_items,
            },
        }
