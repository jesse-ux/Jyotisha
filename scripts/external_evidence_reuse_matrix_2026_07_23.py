#!/usr/bin/env python3
"""Build a reuse matrix for remaining external-evidence gaps."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "references/oracle/external_evidence_reuse_matrix_2026_07_23.json"

ROWS = [
    {
        "gap": "KP 12 cusp exact longitude",
        "can_open_source_help": True,
        "best_reuse_path": "Use provider/OpenAPI surfaces to capture pinned raw, not copy hidden hosted calculations.",
        "candidates": [
            {"name": "RoxyAPI KP", "url": "https://github.com/RoxyAPI/kp-astrology-api", "reuse": "api_surface_reference"},
            {"name": "AstrologyAPI kp_house_cusps", "url": "https://astrologyapi.com/docs/api-ref/77/kp_house_cusps", "reuse": "hosted_api_candidate"},
            {"name": "Prokerala KP docs", "url": "https://api.prokerala.com/docs", "reuse": "hosted_api_candidate"},
            {"name": "AjmerAstro KP tool", "url": "https://www.ajmerastro.com/en/kp-astrology", "reuse": "tool_surface_reference"},
        ],
        "still_missing": ["API key/terms", "version metadata", "raw retention permission", "canonical request", "public expected table"],
        "current_status": "blocked_until_key_terms_version",
    },
    {
        "gap": "KP significator workflow",
        "can_open_source_help": True,
        "best_reuse_path": "Use public workflow references as audit rules; keep numeric prediction blocked.",
        "candidates": [
            {"name": "AstroSage KP fundamentals", "url": "https://kpastrology.astrosage.com/kp-learning-home/tutorial/chapter-2-fundamental-principles", "reuse": "workflow_reference"},
            {"name": "Scribd significator table snippets", "url": "https://www.scribd.com/doc/159331923/Significator-Table", "reuse": "snippet_reference_only"},
        ],
        "still_missing": ["complete 12 cusp oracle", "planet/cusp significator raw", "event outcome oracle", "negative holdout"],
        "current_status": "calculable_displayable_public_oracle_blocked",
    },
    {
        "gap": "Gulika / Sphuta numeric packet",
        "can_open_source_help": True,
        "best_reuse_path": "Use PyJHora/JHora-style black-box replay or local Swiss-Ephemeris only after complete public input exists.",
        "candidates": [
            {"name": "local guarded Gulika implementation", "url": "local:superpowers/prashna-integration-guarded/scripts/gulika.py", "reuse": "formula_reference_only"},
            {"name": "CourseHero Gulika fragment", "url": "https://www.coursehero.com/file/69722801/387858709-Gulika-and-Mandi-pdftxt/", "reuse": "partial_numeric_candidate"},
        ],
        "still_missing": ["place", "timezone", "coordinates", "source-safe full input", "local replay raw/hash"],
        "current_status": "partial_candidate_blocked",
    },
    {
        "gap": "Prashna / Tajika / Saham numeric packet",
        "can_open_source_help": True,
        "best_reuse_path": "Reuse existing local formulas and open calculators only as candidates until expected numeric values are citable.",
        "candidates": [
            {"name": "guarded Tajika/Saham scripts", "url": "local:superpowers/prashna-integration-guarded/scripts/tajika.py", "reuse": "formula_context_only"},
            {"name": "VedAstro Prasna Marga Ch5", "url": "https://vedastro.org/blog/Prasna-Marga-Chapter-5-Mathematical-Foundations.html", "reuse": "formula_context_only"},
            {"name": "Naksham Varshaphal calculator", "url": "https://nakshamastro.com/astrohub/vedic/varshaphal", "reuse": "calculator_surface_candidate"},
        ],
        "still_missing": ["complete chart input", "expected Saham/Sphuta longitudes", "day/night convention", "raw/hash replay"],
        "current_status": "candidate_queue",
    },
    {
        "gap": "timing / birth-time rectification holdout",
        "can_open_source_help": False,
        "best_reuse_path": "Open-source code can score features after labels exist; it cannot create independent human labels.",
        "candidates": [
            {"name": "local holdout validator", "url": "local:scripts/day_level_holdout_validator.py", "reuse": "already_integrated"},
            {"name": "local blind evaluator", "url": "local:scripts/timing_ranker_blind_eval.py", "reuse": "already_integrated"},
        ],
        "still_missing": ["independent human positive labels", "independent human negative windows", "frozen blind packet before scoring"],
        "current_status": "blocked_until_independent_human_labels",
    },
]


def build() -> dict:
    return {
        "scope": "external_evidence_reuse_matrix",
        "created_at": "2026-07-23",
        "claim_status": "reuse_plan_only",
        "truth_matrix_allowed": False,
        "production_tuning_allowed": False,
        "rows": ROWS,
        "summary": {
            "gap_count": len(ROWS),
            "open_source_can_help_count": sum(1 for row in ROWS if row["can_open_source_help"]),
            "requires_human_labels_count": sum("human" in " ".join(row["still_missing"]) for row in ROWS),
            "ready_to_upgrade_count": 0,
        },
        "boundary": "Open-source and local fragments can reduce implementation and replay effort, but cannot replace missing terms, expected numeric values, raw/hash capture, or independent human labels.",
    }


def main() -> int:
    data = build()
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
