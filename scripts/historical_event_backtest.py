#!/usr/bin/env python3
"""Reusable historical event backtest entrypoint built on strict workflow."""

from __future__ import annotations

import argparse
import json
from typing import Any

import mcp_server


SUPPORTED_DOMAINS = {
    "career": {
        "route": "career",
        "question": "请严格回测这条事业事件是否成立，并判断是职业状态、角色变化、升迁窗口还是项目兑现。",
    },
    "wealth": {
        "route": "finance",
        "question": "请严格回测这条财富事件是否成立，并判断更接近收入增长、到账、套现还是公众财富状态。",
    },
    "finance": {
        "route": "finance",
        "question": "请严格回测这条财富事件是否成立，并判断更接近收入增长、到账、套现还是公众财富状态。",
    },
    "marriage": {
        "route": "relationship",
        "question": "请严格回测这条婚恋事件是否成立，并判断是否达到正式关系或婚姻层。",
    },
    "relationship": {
        "route": "relationship",
        "question": "请严格回测这条婚恋事件是否成立，并判断是否达到正式关系或婚姻层。",
    },
}


def _route_for_domain(domain: str) -> dict[str, str] | None:
    return SUPPORTED_DOMAINS.get(str(domain).strip().lower())


def _load_payload(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _event_result_class(
    verdict: str | None,
    blocked: bool,
    expected_label: str | None,
    actual_label: str | None,
) -> tuple[str, dict[str, Any]]:
    if blocked:
        return "blocked", {"reason": "strict_workflow_blocked"}
    if verdict == "high_probability_window" and actual_label and (
        not expected_label or expected_label == actual_label
    ):
        return "strong_hit", {"reason": "supported_route_and_label"}
    if verdict in {"high_probability_window", "moderate_probability_window"}:
        if expected_label and actual_label and expected_label != actual_label:
            return "weak_hit", {"reason": "label_mismatch_under_supported_route"}
        return "weak_hit", {"reason": "supported_route_without_exact_label"}
    if verdict == "weak_window_needs_confirmation":
        return "weak_hit", {"reason": "weak_window_needs_confirmation"}
    return "miss", {"reason": verdict or "insufficient_evidence"}


def _official_snapshot_summary(strict: dict[str, Any]) -> dict[str, Any]:
    present = strict.get("present_evidence") or {}
    official = present.get("vedastro_official_snapshot")
    if not isinstance(official, dict):
        return {"level": "missing", "status": "missing", "source": None}
    return {
        "level": official.get("level") or "missing",
        "status": official.get("status"),
        "source": official.get("source"),
    }


def _source_priority_mode(strict: dict[str, Any]) -> str | None:
    present = strict.get("present_evidence") or {}
    source_priority = present.get("source_priority")
    if not isinstance(source_priority, dict):
        return None
    return source_priority.get("mode")


def _run_supported_event(subject: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    route_info = _route_for_domain(event.get("domain", ""))
    if route_info is None:
        return {
            "id": event.get("id"),
            "date": event.get("date"),
            "domain": event.get("domain"),
            "route": None,
            "expected_label": event.get("expected_label"),
            "actual_label": None,
            "matched_expected_label": False,
            "result_class": "unsupported_domain",
            "boundary": {"reason": "route_not_yet_implemented_for_event_backtest"},
            "official_snapshot": {"level": "missing", "status": "missing", "source": None},
            "evidence": {"source_priority_mode": None, "confidence_cap": "unsupported"},
        }

    result = mcp_server.strict_workflow(
        question=route_info["question"],
        year=int(subject["year"]),
        month=int(subject["month"]),
        day=int(subject["day"]),
        hour=int(subject["hour"]),
        minute=int(subject["minute"]),
        lat=float(subject["lat"]),
        lon=float(subject["lon"]),
        tz=float(subject["tz"]),
        age=int(subject.get("age", 0)),
        transit_date=str(event["date"]),
        node_mode=str(subject.get("node_mode", "mean")),
    )
    strict = result.get("strict_workflow") if isinstance(result, dict) else {}
    if not isinstance(strict, dict):
        strict = {}

    judgement = strict.get("event_judgement") if isinstance(strict.get("event_judgement"), dict) else {}
    actual_label = judgement.get("dominant_label")
    expected_label = event.get("expected_label")
    verdict = judgement.get("verdict")
    blocked = bool(strict.get("blocked"))
    result_class, boundary = _event_result_class(verdict, blocked, expected_label, actual_label)

    return {
        "id": event.get("id"),
        "date": event.get("date"),
        "domain": event.get("domain"),
        "route": route_info["route"],
        "expected_label": expected_label,
        "actual_label": actual_label,
        "matched_expected_label": bool(expected_label and expected_label == actual_label),
        "result_class": result_class,
        "boundary": boundary,
        "official_snapshot": _official_snapshot_summary(strict),
        "evidence": {
            "verdict": verdict,
            "score": judgement.get("score"),
            "confidence_cap": strict.get("confidence_cap"),
            "missing_evidence": strict.get("missing_evidence") or [],
            "blocked_items": strict.get("blocked_items") or [],
            "conflicts": strict.get("conflicts") or [],
            "adjudication_stages": strict.get("adjudication_stages") or {},
            "multi_reference_reading_summary": strict.get("multi_reference_reading_summary") or {},
            "main_conflicts": strict.get("main_conflicts") or strict.get("conflicts") or [],
            "source_priority_mode": _source_priority_mode(strict),
            "primary_drivers": judgement.get("primary_drivers") or [],
            "secondary_context": judgement.get("secondary_context") or [],
            "technique_audit": strict.get("technique_audit") or [],
            "life_event_graph": strict.get("life_event_graph") or {},
        },
    }


def build_report(payload: dict[str, Any]) -> dict[str, Any]:
    subject = payload.get("subject") or {}
    events = payload.get("events") or []
    rows = [_run_supported_event(subject, event) for event in events]

    summary = {
        "total_events": len(rows),
        "strong_hits": sum(1 for row in rows if row["result_class"] == "strong_hit"),
        "weak_hits": sum(1 for row in rows if row["result_class"] == "weak_hit"),
        "misses": sum(1 for row in rows if row["result_class"] == "miss"),
        "blocked_events": sum(1 for row in rows if row["result_class"] == "blocked"),
        "unsupported_domain_events": sum(1 for row in rows if row["result_class"] == "unsupported_domain"),
        "official_primary_events": sum(
            1 for row in rows if row["official_snapshot"].get("level") == "primary"
        ),
    }

    return {
        "scope": "historical_event_backtest",
        "summary": summary,
        "boundary": (
            "This report measures whether current strict routes can support supplied historical events. "
            "Unsupported domains and blocked routes must not be overstated as validated predictive accuracy."
        ),
        "events": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run reusable historical-event backtest")
    parser.add_argument("--input", required=True, help="Path to local backtest payload JSON")
    args = parser.parse_args()

    report = build_report(_load_payload(args.input))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
