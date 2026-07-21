#!/usr/bin/env python3
"""Commercial privacy artifact gate.

This is a thin commercial wrapper around the existing public release privacy
scanner. It exists so CI/product checks can call a business-named gate without
duplicating privacy logic.
"""
from __future__ import annotations

import argparse
import json

from public_release_privacy_scan import build_report


def commercial_report() -> dict[str, object]:
    base = build_report()
    return {
        "scope": "commercial_privacy_artifact_scan",
        "status": base["status"],
        "finding_count": base["finding_count"],
        "scanned_files": base["scanned_files"],
        "privacy_boundary": "no_real_user_birth_data_private_cases_or_secret_values_in_public_artifacts",
        "scanner_reuse": "scripts/public_release_privacy_scan.py",
        "local_runtime_assets_not_committed": ["hip_main.dat", "hip_main.dat.download"],
        "findings": base["findings"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args()
    report = commercial_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"{report['status']}: {report['finding_count']} findings")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
