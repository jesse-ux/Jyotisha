#!/usr/bin/env python3
"""Classify OSS/web Jyotish sources by allowed verification use."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


SOURCES: list[dict[str, Any]] = [
    {
        "source_id": "jyotishganit_mit",
        "name": "northtara/jyotishganit",
        "url": "https://github.com/northtara/jyotishganit",
        "license_status": "MIT",
        "source_type": "open_source_engine",
        "allowed_use_tier": "permissive_adapter_or_formula_observation",
        "can_copy_code": True,
        "can_be_oracle_truth": False,
        "required_before_truth": [
            "pinned commit/package hash",
            "same input contract",
            "field-level raw output",
            "method provenance",
            "worked-example or independent oracle arbitration",
        ],
    },
    {
        "source_id": "xalen_ephemeris_apache",
        "name": "vedika-io/xalen-ephemeris",
        "url": "https://github.com/vedika-io/xalen-ephemeris",
        "license_status": "Apache-2.0",
        "source_type": "open_source_ephemeris",
        "allowed_use_tier": "permissive_adapter_or_formula_isolation",
        "can_copy_code": True,
        "can_be_oracle_truth": False,
        "required_before_truth": [
            "pinned commit/Cargo.lock hash",
            "same ayanamsa/node/timezone contract",
            "same raw longitude/JD input",
            "component-level formula provenance",
        ],
    },
    {
        "source_id": "vedastro_python_mit",
        "name": "VedAstro.Python",
        "url": "https://github.com/VedAstro/VedAstro.Python",
        "license_status": "MIT",
        "source_type": "client_wrapper",
        "allowed_use_tier": "client_wrapper_observation_only",
        "can_copy_code": True,
        "can_be_oracle_truth": False,
        "required_before_truth": [
            "hosted deployment build/version identity",
            "raw response hash",
            "endpoint/method documentation",
        ],
    },
    {
        "source_id": "public_kp_pdf_candidate",
        "name": "Public KP calculation PDF candidates",
        "url": "references/oracle/public_worked_example_queue_2026_07_19.json",
        "license_status": "public_web_candidate_not_license_cleared_for_copying",
        "source_type": "worked_example_candidate",
        "allowed_use_tier": "manual_oracle_candidate_queue",
        "can_copy_code": False,
        "can_be_oracle_truth": False,
        "required_before_truth": [
            "full birth/input data",
            "ayanamsa/timezone/house system",
            "expected cusp/star/sub values",
            "citation/page",
            "replay artifact hash",
        ],
    },
    {
        "source_id": "public_real_case_story",
        "name": "Public biography/news/event cases",
        "url": "global_web_search_or_public_dataset",
        "license_status": "citation_only",
        "source_type": "real_case_reference",
        "allowed_use_tier": "case_reference_for_user_explanation",
        "can_copy_code": False,
        "can_be_oracle_truth": False,
        "required_before_truth": [
            "reliable birth record",
            "dated positive events",
            "explicitly evidenced non-event windows",
            "independent human label freeze",
            "no tuning on holdout",
        ],
    },
]


def build(date: str) -> dict[str, Any]:
    return {
        "scope": "external_source_use_tier_registry",
        "created_at": date,
        "claim_status": "ready_contract",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "summary": {
            "source_count": len(SOURCES),
            "copyable_code_source_count": sum(1 for row in SOURCES if row["can_copy_code"]),
            "oracle_truth_ready_count": sum(1 for row in SOURCES if row["can_be_oracle_truth"]),
        },
        "rules": [
            "Permissive OSS can be copied only after license, commit, and package hash are pinned.",
            "OSS engine agreement is evidence, not final truth, unless external worked examples close the method.",
            "Public stories can be shown as similar case references, not used as negative holdout labels.",
            "Public PDFs become oracle candidates only when full inputs, settings, numeric expected values, citation, and replay hash exist.",
            "Conflicting Shadbala/AV/KP results must be surfaced as method variants, not majority-voted.",
        ],
        "sources": SOURCES,
        "boundary": "This registry authorizes source usage tiers; it does not close timing, KP cusp, Shadbala/AV, or Muhurta numeric truth.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default="2026-07-20")
    args = parser.parse_args()
    print(json.dumps(build(args.date), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
