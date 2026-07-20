#!/usr/bin/env python3
"""Capture real consultation workflow contexts for the commercial E2E matrix."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.consultation_workflow_service import execute_consultation_workflow  # noqa: E402


DEFAULT_CONTRACT = ROOT / "references" / "cross_project_contract" / "commercial_astrology_e2e_acceptance_questions_2026_07_19.json"
DEFAULT_OUTPUT_DIR = ROOT / "artifacts" / "commercial_astrology_e2e_contexts_2026_07_19"

THEME_BY_ID = {
    "marriage_timing": ["marriage"],
    "career_direction": ["career"],
    "wealth_pattern": ["wealth"],
    "health_risk_window": ["health"],
    "foreign_migration": ["career"],
    "family_home_children": ["marriage", "wealth"],
    "education_learning_path": ["career"],
    "precise_timing_boundary": ["career"],
    "birth_time_uncertain": ["career"],
    "annual_forecast": ["career", "marriage", "wealth"],
}

CANONICAL_BIRTH = {
    "year": 1955,
    "month": 2,
    "day": 24,
    "hour": 19,
    "minute": 15,
    "lat": 37.7749,
    "lon": -122.4194,
    "tz": -8,
    "city": "San Francisco",
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


def _capture_body(question: dict[str, Any]) -> dict[str, Any]:
    qid = str(question["id"])
    return {
        **CANONICAL_BIRTH,
        "question": question["user_question"],
        "question_text": question["user_question"],
        "theme": THEME_BY_ID.get(qid, ["general"]),
        "entry_mode": "rectification" if qid == "birth_time_uncertain" else "direct_chart",
    }


def _capture_body_for_real_case(case: dict[str, Any], prompt: str) -> dict[str, Any]:
    birth = case["birth"]
    year, month, day = [int(part) for part in birth["date"].split("-")]
    hour, minute = [int(part) for part in birth["time"].split(":")[:2]]
    theme_map = {
        "timing": "career",
        "annual": "career",
        "migration": "career",
        "family": "marriage",
        "education": "career",
    }
    themes = [theme_map.get(domain, domain) for domain in case["domains"]]
    return {
        "year": year,
        "month": month,
        "day": day,
        "hour": hour,
        "minute": minute,
        "lat": birth["lat"],
        "lon": birth["lon"],
        "tz": birth["tz"],
        "city": birth["place"],
        "question": prompt,
        "question_text": prompt,
        "theme": themes,
        "evaluation_domains": case["domains"],
        "entry_mode": "direct_chart",
        "case_id": case["case_id"],
        "subject": case["subject"],
        "source_policy": birth["source_policy"],
    }


def capture(
    contract_path: Path = DEFAULT_CONTRACT,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    max_items: int | None = None,
    offset: int = 0,
) -> dict[str, Any]:
    contract = _load_json(contract_path)
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    if "cases" in contract:
        questions = [
            {"id": f"{case['case_id']}__{index + 1}", "body": _capture_body_for_real_case(case, prompt)}
            for case in contract["cases"]
            for index, prompt in enumerate(case["prompts"])
        ]
    else:
        questions = [{"id": str(question["id"]), "body": _capture_body(question)} for question in contract["questions"]]
    for question in questions[offset:]:
        if max_items is not None and len(rows) >= max_items:
            break
        qid = str(question["id"])
        result = execute_consultation_workflow(question["body"], surface="commercial_e2e_capture")
        context_path = output_dir / f"{qid}.json"
        context_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        rows.append(
            {
                "id": qid,
                "context_file": _display_path(context_path),
                "core_status": result.get("consumer_context", {}).get("core_status"),
                "route": result.get("consumer_context", {}).get("route"),
                "available_layers": result.get("consumer_context", {}).get("available_layers", []),
                "missing_route_layers": result.get("consumer_context", {}).get("missing_route_layers", []),
            }
        )
    manifest = {
        "scope": "commercial_astrology_e2e_context_capture",
        "contract": _display_path(contract_path),
        "output_dir": _display_path(output_dir),
        "question_count": len(rows),
        "offset": offset,
        "rows": rows,
    }
    (output_dir / "capture_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--max-items", type=int, default=None)
    parser.add_argument("--offset", type=int, default=0)
    args = parser.parse_args()
    print(
        json.dumps(
            capture(args.contract, args.output_dir, max_items=args.max_items, offset=args.offset),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
