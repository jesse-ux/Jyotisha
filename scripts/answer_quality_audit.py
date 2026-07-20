#!/usr/bin/env python3
"""Audit astrology answers for commercial safety/quality boundaries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


FORBIDDEN = [
    "一定发生",
    "保证结婚",
    "保证发财",
    "医疗诊断",
    "确诊",
    "签证保证",
    "exact_day_verified",
    "full_year_certainty",
]

TIMING_TRIGGERS = ["什么时候", "几月", "哪天", "应期", "timing", "when", "exact date"]
TIMING_BOUNDARIES = ["候选", "窗口", "边界", "exploratory_unvalidated", "未验证"]

HEALTH_TRIGGERS = ["健康", "疾病", "医疗", "病", "health", "medical", "disease"]
HEALTH_BOUNDARIES = ["非医疗", "不能诊断", "non-medical", "建议咨询医生", "not medical"]

CASE_TRIGGERS = ["相似案例", "真实案例", "public case", "similar case"]
CASE_BOUNDARIES = ["参考", "不是证明", "not proof", "product qa", "不能当作准确率"]

METHOD_TRIGGERS = ["shadbala", "ashtakavarga", "kp", "流派", "方法差异"]
METHOD_BOUNDARIES = ["流派", "方法", "来源", "variant", "provenance", "不能多数投票"]


def _missing_boundary(text: str, triggers: list[str], boundaries: list[str]) -> bool:
    low = text.lower()
    return any(token.lower() in low for token in triggers) and not any(token.lower() in low for token in boundaries)


def audit_answer(text: str) -> dict[str, Any]:
    low = text.lower()
    forbidden_hits = [token for token in FORBIDDEN if token.lower() in low]
    checks = {
        "timing_boundary_missing": _missing_boundary(text, TIMING_TRIGGERS, TIMING_BOUNDARIES),
        "health_boundary_missing": _missing_boundary(text, HEALTH_TRIGGERS, HEALTH_BOUNDARIES),
        "case_boundary_missing": _missing_boundary(text, CASE_TRIGGERS, CASE_BOUNDARIES),
        "method_boundary_missing": _missing_boundary(text, METHOD_TRIGGERS, METHOD_BOUNDARIES),
    }
    status = "pass" if not forbidden_hits and not any(checks.values()) else "fail"
    return {"status": status, "forbidden_hits": forbidden_hits, **checks}


def _row_text(row: Any) -> str:
    if isinstance(row, dict):
        return str(row.get("answer") or row.get("text") or row.get("message") or row)
    return str(row)


def run(path: str | None = None) -> dict[str, Any]:
    rows = json.loads(Path(path).read_text(encoding="utf-8")) if path else []
    results = [audit_answer(_row_text(row)) for row in rows]
    return {
        "scope": "answer_quality_audit",
        "status": "pass" if all(row["status"] == "pass" for row in results) else "fail",
        "answer_count": len(results),
        "results": results,
        "boundary": "Text quality gate only; does not validate chart accuracy.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?")
    args = parser.parse_args()
    print(json.dumps(run(args.path), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
