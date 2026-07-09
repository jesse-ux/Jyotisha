#!/usr/bin/env python3
"""Aggregate external-engine adapter readiness diagnostics."""

from __future__ import annotations

import argparse
import json

try:
    from diagnose_vedastro_mode import build_report as build_vedastro_report
    from diagnose_pyjhora_adapter import build_report as build_pyjhora_report
    from diagnose_jyotishganit_adapter import build_report as build_jyotishganit_report
except Exception:  # pragma: no cover - import path varies in tests/CLI
    from scripts.diagnose_vedastro_mode import build_report as build_vedastro_report
    from scripts.diagnose_pyjhora_adapter import build_report as build_pyjhora_report
    from scripts.diagnose_jyotishganit_adapter import build_report as build_jyotishganit_report


REQUIRED_PARITY_OUTPUTS = ["D1", "D9", "D10", "D2", "D4", "Vimshottari", "Shadbala", "Ashtakavarga"]


def _same_chart_parity_contract(engines: dict) -> dict:
    engine_states = {}
    for name, engine in engines.items():
        available = engine["status"] == "available"
        engine_states[name] = {
            "available": available,
            "tested": False,
            "blocked": not available,
            "blocking_reason": "" if available else engine["status"],
        }
    return {
        "status": "ready" if all(state["available"] for state in engine_states.values()) else "blocked",
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
        "boundary": "This is a parity contract, not proof that the same-chart comparison has run.",
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
