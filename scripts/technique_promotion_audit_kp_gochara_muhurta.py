#!/usr/bin/env python3
"""Audit KP/Gochara/Muhurta/Panchanga fragments and runtime entrypoints."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def build_audit(root: Path) -> dict:
    api = _text(root / "scripts/jyotish_api_server.py")
    research_main_js = _text(root / "jyotish-app/main.js")
    commercial_page = _text(root / "frontend/src/app/page.tsx")
    dashaflow_muhurtha = root / "references/open_source_sources/dashaflow/muhurtha.py"
    panchanga_license = _text(root / "references/open_source_sources/panchanga_api/LICENSE").splitlines()
    kp_reference = root / "/Users/wuyongnaren/.workbuddy/backups/jyotish-vedic-astrology-20260711-154109/references/kp-astrology-complete-system.md"
    gochara_template = Path("/tmp/jyotisha-optimize/assets/event_timing_template.md")
    panchanga_called = (
        "/api/panchanga_range" in api
        and (
            ("panchanga-range" in research_main_js and "panchanga-csv" in research_main_js)
            or ("panchanga-range" in commercial_page and "panchanga-csv" in commercial_page)
        )
    )

    items = [
        {
            "technique_id": "panchanga_calendar",
            "current_call_status": "formally_called_in_api_and_web" if panchanga_called else "partial",
            "main_artifacts": [
                "scripts/jyotish_api_server.py",
                "frontend/src/app/page.tsx",
                "jyotish-app/main.js (research static UI only, absent in commercial repo)",
            ],
            "external_or_reference_artifacts": ["references/open_source_sources/panchanga_api"],
            "reuse_decision": "do_not_duplicate_runtime",
            "source_or_license_boundary": "Existing runtime/UI present; panchanga_api license observed as "
            + (panchanga_license[0] if panchanga_license else "unknown")
            + ". Treat external panchanga_api as reference unless license/API contract is separately audited.",
            "next_action": "add panchanga claim/display contract and source/oracle packet for tithi/nakshatra/yoga/karana/rahu-kalam outputs",
            "claim_boundary": "Panchanga is runtime-visible but still needs field-level external oracle examples for high-rigor claims.",
        },
        {
            "technique_id": "muhurta_dashaflow_candidate",
            "current_call_status": "oss_reference_not_main_runtime",
            "main_artifacts": [],
            "external_or_reference_artifacts": [str(dashaflow_muhurtha)],
            "reuse_decision": "license_audit_before_reuse",
            "source_or_license_boundary": "dashaflow/muhurtha.py exists under references/open_source_sources; verify license and formula sources before adapting.",
            "next_action": "audit dashaflow license, extract formula surface, then compare Tarabala/Chandrabala/Rahu Kalam against local Panchanga.",
            "claim_boundary": "Muhurta remains reference-only until license, formula, and worked examples close.",
        },
        {
            "technique_id": "kp_astrology",
            "current_call_status": "reference_only_not_main_runtime",
            "main_artifacts": [],
            "external_or_reference_artifacts": [str(kp_reference)],
            "reuse_decision": "reference_only",
            "source_or_license_boundary": "KP backup/reference may contain useful notes but must pass privacy/license/source audit; do not copy blindly.",
            "next_action": "create KP separate track: cusp system, ayanamsa, star lord/sub lord, ruling planets, public oracle examples.",
            "claim_boundary": "KP is not part of current main Jyotish runtime truth.",
        },
        {
            "technique_id": "gochara_event_timing_template",
            "current_call_status": "template_reference_not_main_runtime",
            "main_artifacts": [],
            "external_or_reference_artifacts": [str(gochara_template)],
            "reuse_decision": "reference_only",
            "source_or_license_boundary": "Template in /tmp must be privacy/source reviewed before promotion.",
            "next_action": "turn Gochara template into scoring contract only after Dasha+Varga+Transit features and negative holdout are ready.",
            "claim_boundary": "Transit template is not a calibrated timing engine.",
        },
    ]
    return {
        "scope": "technique_promotion_audit_kp_gochara_muhurta",
        "created_at": "2026-07-19",
        "truth_policy": "runtime_presence_not_oracle_closure",
        "production_tuning_allowed": False,
        "summary": {
            "items_checked": len(items),
            "formally_called_count": sum("formally_called" in item["current_call_status"] for item in items),
            "reference_only_count": sum("not_main_runtime" in item["current_call_status"] or "template_reference" in item["current_call_status"] for item in items),
        },
        "items": items,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    audit = build_audit(args.root)
    text = json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
