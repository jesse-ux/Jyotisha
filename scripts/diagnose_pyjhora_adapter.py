#!/usr/bin/env python3
"""Report whether the PyJHora comparison adapter can run in this environment."""

from __future__ import annotations

import argparse
import contextlib
import importlib
import importlib.util
import io
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
    import_error = None
    if module_available:
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                importlib.import_module(f"{module_name}.utils")
                importlib.import_module(f"{module_name}.horoscope.chart.charts")
                importlib.import_module(f"{module_name}.panchanga.drik")
        except Exception as exc:
            import_error = f"{exc.__class__.__name__}: {exc}"

    if not adapter_exists:
        status = "missing_adapter"
    elif not module_available:
        status = "missing_dependency"
    elif import_error:
        status = "dependency_import_failed"
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
        "dependency_import_error": import_error,
        "install_hint": {
            "package": "PyJHora",
            "commands": [
                "pip install -r requirements.txt -r requirements-reference-engines.txt"
            ],
            "note": "Install in an isolated optional benchmark environment, not as a hard runtime dependency.",
        },
        "license_boundary": "AGPL external benchmark only; do not vendor or make it a runtime dependency.",
        "ephemeris_data_note": "Recent PyJHora releases may require separate Swiss Ephemeris data download/configuration before full chart comparison can run.",
        "boundary": "This verifies required PyJHora modules import successfully, but does not run chart comparison.",
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
