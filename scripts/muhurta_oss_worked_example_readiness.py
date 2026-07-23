#!/usr/bin/env python3
"""Build Muhurta OSS worked-example readiness packet.

The packet records public/open-source candidates for factor comparison. It does
not import their code and does not allow a final Muhurta verdict.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "references/oracle/muhurta_oss_worked_example_readiness_2026_07_23.json"

ROWS = [
    {
        "source_id": "roxyapi_panchang_api",
        "url": "https://github.com/topics/tithi",
        "license_status": "candidate_needs_repo_metadata_check",
        "feature_surface": ["rahu_kaal", "abhijit", "chandrabalam", "tarabalam"],
        "numeric_worked_example_status": "not_found_in_search_snippet",
        "reuse_policy": "reference_only_until_license_and_fixture",
    },
    {
        "source_id": "fusionstrings_panchangam",
        "url": "https://github.com/fusionstrings/panchangam",
        "license_status": "candidate_needs_repo_metadata_check",
        "feature_surface": ["rahu_kalam", "yamaganda", "gulika", "abhijit_muhurta"],
        "numeric_worked_example_status": "api_candidate_not_oracle",
        "reuse_policy": "reference_only_until_pinned_adapter",
    },
    {
        "source_id": "bidyashish_vedicpanchanga",
        "url": "https://github.com/bidyashish/vedicpanchanga.com",
        "license_status": "candidate_needs_repo_metadata_check",
        "feature_surface": ["muhurta_finder", "rahu_kala", "abhijit", "tyajyam", "hora"],
        "numeric_worked_example_status": "app_candidate_not_oracle",
        "reuse_policy": "reference_only_until_pinned_adapter",
    },
    {
        "source_id": "happyalu_panchang_muhurt",
        "url": "https://github.com/happyalu/panchang-muhurt/",
        "license_status": "candidate_needs_repo_metadata_check",
        "feature_surface": ["panchanga", "muhurta_filters", "red_flag_timeslots"],
        "numeric_worked_example_status": "filter_candidate_not_oracle",
        "reuse_policy": "reference_only_until_license_and_fixture",
    },
    {
        "source_id": "vijayalur_tarabala_chandrabala_panchaka",
        "url": "https://vijayalur.com/2011/10/02/tarabala-chandrabala-panchaka/",
        "license_status": "public_article_reference",
        "feature_surface": ["tarabala", "chandrabala", "panchaka"],
        "numeric_worked_example_status": "formula_reference_not_replay_packet",
        "reuse_policy": "cite_as_reference_only",
    },
]


def build() -> dict:
    factors = sorted({factor for row in ROWS for factor in row["feature_surface"]})
    return {
        "scope": "muhurta_oss_worked_example_readiness",
        "created_at": "2026-07-23",
        "claim_status": "candidate_source_matrix",
        "truth_matrix_allowed": False,
        "production_tuning_allowed": False,
        "final_muhurta_verdict_allowed": False,
        "rows": ROWS,
        "summary": {
            "candidate_count": len(ROWS),
            "factor_surface": factors,
            "numeric_oracle_ready_count": 0,
            "pinned_adapter_ready_count": 0,
        },
        "next_actions": [
            "Pin one permissive OSS package with license and package hash.",
            "Capture local factor raw/hash for Tarabala, Chandrabala, Rahu Kalam, Yamaganda, Gulika Kalam, Abhijit, Panchaka, Sankranti, Vyatipata and Vaidhriti.",
            "Promote only sources with full input, expected factor values, version identity and replayable raw.",
        ],
        "boundary": "These are candidate references only; they do not authorize a final auspicious-date verdict.",
    }


def main() -> int:
    packet = build()
    OUTPUT.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(packet, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
