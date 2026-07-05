#!/usr/bin/env python3
"""Report whether the local jyotishganit reference checkout is importable."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ADAPTER_RELATIVE = "references/open_source_sources/jyotishganit"


def build_report() -> dict:
    adapter_relative = os.environ.get("JYOTISHGANIT_ADAPTER_PATH", DEFAULT_ADAPTER_RELATIVE).strip() or DEFAULT_ADAPTER_RELATIVE
    adapter = ROOT / adapter_relative
    package_dir = adapter / "jyotishganit"
    license_file = adapter / "LICENSE"

    if not adapter.exists() or not package_dir.exists():
        status = "missing_checkout"
        importable = False
        error = None
    else:
        sys.path.insert(0, str(adapter))
        try:
            importable = importlib.util.find_spec("jyotishganit") is not None
            status = "available" if importable else "runtime_error"
            error = None if importable else "package_not_importable"
        except Exception as exc:  # pragma: no cover - defensive diagnostic
            importable = False
            status = "runtime_error"
            error = f"{type(exc).__name__}: {exc}"
        finally:
            try:
                sys.path.remove(str(adapter))
            except ValueError:
                pass

    return {
        "scope": "jyotishganit_adapter_diagnostics",
        "status": status,
        "adapter_path": adapter_relative,
        "checkout_exists": adapter.exists(),
        "package_exists": package_dir.exists(),
        "importable": importable,
        "license": "MIT" if license_file.exists() else "unknown",
        "error": error,
        "boundary": "This is a reference-checkout readiness smoke check only; it does not run jyotishganit calculations.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = parser.parse_args()
    report = build_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        print(f"jyotishganit adapter status: {report['status']}")
        print(f"Adapter path: {report['adapter_path']}")
        if report["error"]:
            print(f"Error: {report['error']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
