#!/usr/bin/env python3
"""Validate the commercial astrology acceptance matrix.

Default mode is deliberately blocked: the contract exists, but real E2E proof
requires captured answer-context JSON files for each question id.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "references" / "cross_project_contract" / "commercial_astrology_e2e_acceptance_questions_2026_07_19.json"

LAYER_PATTERNS: dict[str, list[str]] = {
    "Vimshottari Dasha": ["vimshottari", "dasha"],
    "Narayana Dasha": ["narayana"],
    "D9": ["d9"],
    "D10": ["d10"],
    "D2": ["d2"],
    "D11": ["d11"],
    "D4": ["d4"],
    "D5": ["d5"],
    "D6": ["d6"],
    "D7": ["d7"],
    "D8": ["d8"],
    "D12": ["d12"],
    "D24": ["d24"],
    "UL": ["ul", "upapada"],
    "A10": ["a10"],
    "Darakaraka": ["darakaraka", "dk"],
    "Shadbala": ["shadbala"],
    "Ashtakavarga": ["ashtakavarga"],
    "Shadbala/AV provenance registry": ["shadbala", "ashtakavarga", "provenance"],
    "VedAstro gateway boundary": ["vedastro"],
    "timing precision contract": ["verified_window", "candidate_windows", "exact_triggers"],
    "gender interpretation boundary": ["gender", "spouse", "supplement"],
    "functional benefic/malefic": ["functional_benefic_malefic"],
    "12th house": ["12th", "twelfth", "house_12"],
    "6th/8th/12th house": ["6th", "8th", "12th"],
    "4th/5th/9th house": ["4th", "5th", "9th"],
    "5th/9th house": ["5th", "9th"],
    "Rahu/Ketu context": ["rahu", "ketu"],
    "Mercury/Jupiter context": ["mercury", "jupiter"],
    "Ashtakoot boundary": ["ashtakoot"],
    "birth-time uncertainty boundary": ["birth_time", "uncertain"],
    "rectification boundary": ["rectification"],
    "candidate windows": ["candidate_windows"],
    "not_auto_rectified": ["not_auto_rectified"],
    "no_majority_vote": ["no_majority_vote"],
    "verified_window": ["verified_window"],
    "candidate_windows": ["candidate_windows"],
    "exact_triggers": ["exact_triggers"],
    "day-level holdout boundary": ["holdout", "exploratory_unvalidated"],
    "health non-medical boundary": ["health", "non_medical"],
    "annual forecast boundary": ["annual", "forecast"],
    "transit context": ["transit"],
}

FORBIDDEN_PATTERNS: dict[str, list[str]] = {
    "exact day/month verified": ["exact_day_verified", "exact_month_verified"],
    "single-factor Venus/Jupiter truth": ["single_factor_venus_jupiter_truth"],
    "gender changes career math": ["gender_changes_career_math"],
    "D10 missing when present": ["d10_missing_when_present"],
    "guaranteed financial outcome": ["guaranteed_financial_outcome"],
    "D2/D11 missing when present": ["d2_d11_missing_when_present"],
    "medical diagnosis": ["medical_diagnosis"],
    "guaranteed disease event": ["guaranteed_disease_event"],
    "visa/legal guarantee": ["visa_guarantee", "legal_guarantee"],
    "guaranteed child outcome": ["guaranteed_child_outcome"],
    "property/legal guarantee": ["property_guarantee", "legal_guarantee"],
    "exam result guarantee": ["exam_result_guarantee"],
    "single-factor Mercury/Jupiter truth": ["single_factor_mercury_jupiter_truth"],
    "relationship guarantee": ["relationship_guarantee"],
    "gender binary forced when not provided": ["forced_binary_gender"],
    "auto-rectified exact birth time": ["auto_rectified_exact_birth_time"],
    "majority vote truth": ["majority_vote_truth"],
    "method variant as absolute error": ["method_variant_absolute_error"],
    "day/month prediction verified before holdout": ["day_month_verified_before_holdout"],
    "exact_triggers as guaranteed events": ["exact_triggers_guaranteed_events"],
    "full-year certainty": ["full_year_certainty"],
}


def _flatten(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True).lower()


def _has_layer(text: str, layer: str) -> bool:
    patterns = LAYER_PATTERNS.get(layer, [layer.lower()])
    return all(pattern.lower() in text for pattern in patterns)


def _has_forbidden(text: str, claim: str) -> bool:
    return any(pattern.lower() in text for pattern in FORBIDDEN_PATTERNS.get(claim, [claim.lower()]))


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate(contract_path: Path = DEFAULT_CONTRACT, context_dir: Path | None = None) -> dict[str, Any]:
    contract = _load_json(contract_path)
    rows: list[dict[str, Any]] = []
    status = "pass"

    for question in contract["questions"]:
        qid = question["id"]
        context_path = context_dir / f"{qid}.json" if context_dir else None
        if not context_path or not context_path.exists():
            rows.append(
                {
                    "id": qid,
                    "status": "blocked",
                    "reason": "missing_runtime_context_json",
                    "required_layers": question["required_layers"],
                }
            )
            status = "blocked"
            continue

        text = _flatten(_load_json(context_path))
        missing = [layer for layer in question["required_layers"] if not _has_layer(text, layer)]
        forbidden = [claim for claim in question["must_not_claim"] if _has_forbidden(text, claim)]
        row_status = "pass" if not missing and not forbidden else "fail"
        if row_status == "fail":
            status = "fail"
        rows.append({"id": qid, "status": row_status, "missing_layers": missing, "forbidden_claim_hits": forbidden})

    return {
        "scope": "commercial_astrology_e2e_acceptance_runner",
        "contract": str(contract_path.relative_to(ROOT) if contract_path.is_relative_to(ROOT) else contract_path),
        "status": status,
        "runtime_context_required": True,
        "question_count": len(contract["questions"]),
        "rows": rows,
    }


def write_question_manifest(contract_path: Path, output_path: Path) -> dict[str, Any]:
    contract = _load_json(contract_path)
    manifest = {
        "scope": "commercial_astrology_e2e_question_manifest",
        "contract_id": contract["contract_id"],
        "capture_instruction": "Run each user_question through the commercial consultation flow and save the answer context as <id>.json for this runner.",
        "questions": [
            {
                "id": question["id"],
                "user_question": question["user_question"],
                "required_layers": question["required_layers"],
                "context_filename": f"{question['id']}.json",
            }
            for question in contract["questions"]
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--context-dir", type=Path)
    parser.add_argument("--write-question-manifest", type=Path)
    args = parser.parse_args()

    if args.write_question_manifest:
        manifest = write_question_manifest(args.contract, args.write_question_manifest)
        print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    report = evaluate(args.contract, args.context_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
