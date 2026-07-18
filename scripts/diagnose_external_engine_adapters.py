#!/usr/bin/env python3
"""Aggregate external-engine adapter readiness diagnostics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from diagnose_vedastro_mode import build_report as build_vedastro_report
    from diagnose_pyjhora_adapter import build_report as build_pyjhora_report
    from diagnose_jyotishganit_adapter import build_report as build_jyotishganit_report
    from three_engine_parity_replay_validator import validate_manifest as validate_parity_replay_manifest
except Exception:  # pragma: no cover - import path varies in tests/CLI
    from scripts.diagnose_vedastro_mode import build_report as build_vedastro_report
    from scripts.diagnose_pyjhora_adapter import build_report as build_pyjhora_report
    from scripts.diagnose_jyotishganit_adapter import build_report as build_jyotishganit_report
    from scripts.three_engine_parity_replay_validator import validate_manifest as validate_parity_replay_manifest


REQUIRED_PARITY_OUTPUTS = ["D1", "D9", "D10", "D2", "D4", "Vimshottari", "Shadbala", "Ashtakavarga"]


def _public_pyjhora_parity_manifest() -> dict:
    path = Path("references/oracle/pyjhora_same_chart_parity_public_smoke_manifest.json")
    try:
        baseline = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"status": "not_available", "tested": False}

    supplemental_path = Path("references/oracle/pyjhora_extended_parity_public_smoke_manifest.json")
    try:
        supplemental = json.loads(supplemental_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        supplemental = None

    result = dict(baseline)
    supplements = [supplemental] if supplemental and supplemental.get("tested") else []
    covered = set(baseline.get("covered_outputs", []))
    sample_counts = {name: baseline.get("sample_count", 0) for name in covered}
    partial_sample_counts = {}
    source_reports = [baseline["source_report"]] if baseline.get("source_report") else []
    for item in supplements:
        item_count = item.get("sample_count", 0)
        for name in item.get("covered_outputs", []):
            covered.add(name)
            sample_counts[name] = max(sample_counts.get(name, 0), item_count)
        for name in item.get("partial_outputs", []):
            partial_sample_counts[name] = max(partial_sample_counts.get(name, 0), item_count)
        if item.get("source_report"):
            source_reports.append(item["source_report"])

    result["covered_outputs"] = [name for name in REQUIRED_PARITY_OUTPUTS if name in covered]
    result["missing_required_outputs"] = [name for name in REQUIRED_PARITY_OUTPUTS if name not in covered]
    result["output_sample_counts"] = sample_counts
    result["partial_output_sample_counts"] = partial_sample_counts
    result["source_reports"] = source_reports
    result["supplemental_verifications"] = supplements
    result["boundary"] = (
        "Partial PyJHora verification with per-output sample counts. D2/D4/Ashtakavarga use a one-chart "
        "supplemental replay; Shadbala absolute values remain mismatched. This is not JHora desktop, "
        "VedAstro, jyotishganit, or predictive validation."
    )
    return result


def _same_chart_parity_contract(engines: dict) -> dict:
    pyjhora_public = _public_pyjhora_parity_manifest()
    replay_manifest = validate_parity_replay_manifest("references/oracle/three_engine_parity_replay_manifest.json")
    replay_covers_all_engines = bool(
        replay_manifest.get("tested") and not replay_manifest.get("missing_engines")
    )
    engine_states = {}
    for name, engine in engines.items():
        available = engine["status"] == "available"
        engine_states[name] = {
            "available": available,
            "tested": bool(
                replay_covers_all_engines
                or (name == "PyJHora/JHora" and pyjhora_public.get("tested"))
            ),
            "blocked": not available,
            "blocking_reason": "" if available else engine["status"],
        }
    if not all(state["available"] for state in engine_states.values()):
        contract_status = "blocked"
    elif not all(state["tested"] for state in engine_states.values()):
        contract_status = "partial"
    else:
        contract_status = replay_manifest.get("status", "partial")
    return {
        "status": contract_status,
        "required_outputs": REQUIRED_PARITY_OUTPUTS,
        "expected_oracle_fields": {
            "VedAstro": [
                "official_raw_response",
                "official_chart",
                "section_statuses",
                "request_manifest",
                "source_metadata.artifact_path",
            ],
            "PyJHora/JHora": [
                "raw_output_path",
                "settings.ayanamsa",
                "settings.node_mode",
                "D1",
                "D9",
                "D10",
                "D2",
                "D4",
                "Vimshottari",
                "Shadbala",
                "Ashtakavarga",
            ],
            "jyotishganit": ["raw_output_path", "panchanga", "tithi", "nakshatra", "yoga", "karana"],
        },
        "engine_states": engine_states,
        "replay_manifest": replay_manifest,
        "partial_verifications": {"PyJHora/JHora": pyjhora_public},
        "boundary": "Availability, executed raw coverage, and numerical parity are separate states; mismatch is not ready.",
    }


def build_report() -> dict:
    vedastro = build_vedastro_report()
    pyjhora = build_pyjhora_report()
    jyotishganit = build_jyotishganit_report()
    engines = {
        "VedAstro": {
            "status": "available" if vedastro["official_ready"] else "blocked",
            "mode": vedastro["mode"],
            "readiness_blockers": vedastro["readiness_blockers"],
            "official_closure_plan": vedastro.get("official_closure_plan", {}),
        },
        "PyJHora/JHora": {
            "status": pyjhora["status"],
            "adapter_command": pyjhora["adapter_command"],
            "missing_dependency": pyjhora["missing_dependency"],
            "install_hint": pyjhora.get("install_hint", {}),
            "license_boundary": pyjhora.get("license_boundary"),
            "ephemeris_data_note": pyjhora.get("ephemeris_data_note"),
        },
        "jyotishganit": {
            "status": jyotishganit["status"],
            "adapter_path": jyotishganit["adapter_path"],
            "license": jyotishganit["license"],
        },
    }
    return {
        "scope": "external_engine_adapter_diagnostics",
        "status": "complete" if all(engine["status"] == "available" for engine in engines.values()) else "partial",
        "engines": engines,
        "same_chart_parity_contract": _same_chart_parity_contract(engines),
        "boundary": "Readiness diagnostics only; this does not run a three-engine consultation comparison.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = parser.parse_args()
    report = build_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        print(f"External engine adapter status: {report['status']}")
        for name, engine in report["engines"].items():
            print(f"{name}: {engine['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
