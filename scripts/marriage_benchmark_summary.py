#!/usr/bin/env python3
"""Summarize the v6.1 marriage timing benchmark into adjudicator-ready evidence."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BENCHMARK = ROOT / "tests" / "test-data" / "verify-results-v6.1.json"
RAO_PARAMETERS = [f"P{index}" for index in range(1, 9)]


def _resolve(path: str | Path) -> Path:
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = ROOT / resolved
    return resolved


def _load_rows(path: str | Path) -> list[dict[str, Any]]:
    loaded = json.loads(_resolve(path).read_text(encoding="utf-8"))
    if not isinstance(loaded, list):
        raise ValueError("Marriage benchmark must be a JSON list")
    return [row for row in loaded if isinstance(row, dict)]


def _event_id(case_name: str, marriage: dict[str, Any]) -> str:
    return f"{case_name}|{marriage.get('spouse')}|{marriage.get('date')}"


def _hit_count(marriage: dict[str, Any]) -> int | None:
    summary = ((marriage.get("rao_8_params") or {}).get("summary") or {})
    value = summary.get("hit_count")
    return int(value) if isinstance(value, int) else None


def summarize_benchmark(path: str | Path = DEFAULT_BENCHMARK) -> dict[str, Any]:
    rows = _load_rows(path)
    parameter_hits = {key: 0 for key in RAO_PARAMETERS}
    hit_distribution: Counter[str] = Counter()
    label_lift_seed_cases: list[dict[str, Any]] = []
    event_count = 0
    divorce_count = 0

    for row in rows:
        case_name = row.get("name") or "unknown"
        for marriage in row.get("marriages") or []:
            if not isinstance(marriage, dict):
                continue
            event_count += 1
            if marriage.get("divorce"):
                divorce_count += 1
            rao = marriage.get("rao_8_params") or {}
            for parameter in RAO_PARAMETERS:
                if (rao.get(parameter) or {}).get("hit") is True:
                    parameter_hits[parameter] += 1
            score = _hit_count(marriage)
            if score is not None:
                hit_distribution[str(score)] += 1
                if score >= 6:
                    label_lift_seed_cases.append(
                        {
                            "event_id": _event_id(case_name, marriage),
                            "case": case_name,
                            "spouse": marriage.get("spouse"),
                            "date": marriage.get("date"),
                            "rao_hit_count": score,
                            "rao_hit_rate_pct": round(score / len(RAO_PARAMETERS) * 100, 2),
                            "use": "label_lift_failure_seed",
                        }
                    )

    parameter_summary = {
        parameter: {
            "hit_count": hits,
            "event_count": event_count,
            "hit_rate_pct": round(hits / event_count * 100, 2) if event_count else 0.0,
        }
        for parameter, hits in parameter_hits.items()
    }
    return {
        "scope": "marriage_timing_benchmark_summary",
        "schema_version": 1,
        "source_file": str(_resolve(path)),
        "case_count": len(rows),
        "ascendant_match_count": sum(1 for row in rows if row.get("asc_match") is True),
        "marriage_event_count": event_count,
        "divorce_event_count": divorce_count,
        "rao_hit_distribution": dict(sorted(hit_distribution.items(), key=lambda item: int(item[0]))),
        "rao_parameter_hits": parameter_summary,
        "label_lift_seed_cases": sorted(
            label_lift_seed_cases,
            key=lambda item: (-item["rao_hit_count"], item["case"], item["spouse"] or ""),
        ),
        "boundary": (
            "This summary preserves the v6.1 benchmark as adjudicator evidence. "
            "It does not recompute astrology, alter source data, or promote labels by itself."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Marriage Timing Benchmark Summary",
        "",
        f"- source_file: `{report['source_file']}`",
        f"- case_count: `{report['case_count']}`",
        f"- ascendant_match_count: `{report['ascendant_match_count']}`",
        f"- marriage_event_count: `{report['marriage_event_count']}`",
        f"- divorce_event_count: `{report['divorce_event_count']}`",
        "",
        "## Rao Hit Distribution",
        "",
        "| Rao hits | Event count |",
        "| ---: | ---: |",
    ]
    for score, count in report["rao_hit_distribution"].items():
        lines.append(f"| {score} | {count} |")
    lines.extend(
        [
            "",
            "## Rao Parameter Hits",
            "",
            "| Parameter | Hits | Hit rate |",
            "| --- | ---: | ---: |",
        ]
    )
    for parameter, row in report["rao_parameter_hits"].items():
        lines.append(f"| {parameter} | {row['hit_count']} | {row['hit_rate_pct']}% |")
    lines.extend(
        [
            "",
            "## Label Lift Seed Cases",
            "",
            "| Event | Rao hits |",
            "| --- | ---: |",
        ]
    )
    for row in report["label_lift_seed_cases"]:
        lines.append(f"| `{row['event_id']}` | {row['rao_hit_count']} |")
    lines.extend(["", "## Boundary", "", report["boundary"]])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize the v6.1 marriage timing benchmark")
    parser.add_argument("--benchmark-file", default=str(DEFAULT_BENCHMARK))
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args()

    report = summarize_benchmark(args.benchmark_file)
    if args.format == "markdown":
        print(render_markdown(report))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
