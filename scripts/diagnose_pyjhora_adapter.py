#!/usr/bin/env python3
"""Report whether the PyJHora comparison adapter can run in this environment."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADAPTER_RELATIVE = "benchmarks/jyotish/scripts/run_pyjhora_compare.py"


def build_report() -> dict:
    adapter = ROOT / ADAPTER_RELATIVE
    module_name = os.environ.get("PYJHORA_MODULE_NAME", "jhora").strip() or "jhora"
    adapter_exists = adapter.exists()
    module_available = importlib.util.find_spec(module_name) is not None

    if not adapter_exists:
        status = "missing_adapter"
    elif not module_available:
        status = "missing_dependency"
    else:
        status = "available"

    return {
        "scope": "pyjhora_adapter_diagnostics",
        "status": status,
        "adapter_command": f"python3 {ADAPTER_RELATIVE}",
        "adapter_exists": adapter_exists,
        "dependency_module": module_name,
        "dependency_available": module_available,
        "missing_dependency": None if module_available else module_name,
        "install_hint": {
            "package": "PyJHora",
            "commands": ["pip install PyJHora"],
            "note": "Install in an isolated optional benchmark environment, not as a hard runtime dependency.",
        },
        "license_boundary": "AGPL external benchmark only; do not vendor or make it a runtime dependency.",
        "ephemeris_data_note": "Recent PyJHora releases may require separate Swiss Ephemeris data download/configuration before full chart comparison can run.",
        "boundary": "This is an adapter readiness smoke check only; it does not run PyJHora chart comparison.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = parser.parse_args()
    report = build_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        print(f"PyJHora adapter status: {report['status']}")
        print(f"Adapter command: {report['adapter_command']}")
        if report["missing_dependency"]:
            print(f"Missing dependency: {report['missing_dependency']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
