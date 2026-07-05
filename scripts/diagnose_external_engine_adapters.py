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
