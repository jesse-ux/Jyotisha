#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared orchestration contract for skill/MCP and web/API surfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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
        "timing": ["compute_chart", "run_rectification_gate", "run_thematic_report"],
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

        domain_tokens = {
            "career": ("career", "job", "work", "promotion", "business", "profession", "事业", "工作", "升职", "生意"),
            "relationship": ("marriage", "married", "wedding", "relationship", "love", "spouse", "partner", "divorce", "婚恋", "婚姻", "感情", "配偶", "恋爱", "结婚", "marry"),
            "finance": ("money", "wealth", "finance", "investment", "property", "income", "财务", "财富", "投资", "房产", "收入"),
        }
        first_hits: list[tuple[int, str]] = []
        for route_name, tokens in domain_tokens.items():
            indexes = [text.find(token) for token in tokens if token in text]
            indexes = [idx for idx in indexes if idx >= 0]
            if indexes:
                first_hits.append((min(indexes), route_name))

        if first_hits:
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
