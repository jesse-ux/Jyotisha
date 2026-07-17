#!/usr/bin/env python3
"""Audit VedAstro's official MIT source contract without invoking the service."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


def _read(root: Path, relative: str) -> str:
    return (root / relative).read_text(encoding="utf-8-sig")


def audit_source(root: Path) -> dict:
    project = _read(root, "Library/Library.csproj")
    time_source = _read(root, "Library/Data/Time.cs")
    tools_source = _read(root, "Library/Logic/Tools.cs")
    core_source = _read(root, "Library/Logic/Calculate/Core.cs")
    version_match = re.search(r"<Version>([^<]+)</Version>", project)
    checks = {
        "mit_license": "<PackageLicenseExpression>MIT</PackageLicenseExpression>" in project,
        "offset_parse_exact": 'DateTimeOffset.ParseExact(timezoneRaw, "zzz"' in tools_source,
        "zero_offset_auto_lookup": "parsedTimezone == null || parsedTimezone == TimeSpan.Zero" in tools_source and "GeoLocationToTimezone" in tools_source,
        "time_keeps_offset": "DateTimeOffset.ParseExact(stdDateTimeText, Time.DateTimeFormat" in time_source and "HH:mm dd/MM/yyyy zzz" in time_source,
        "all_planet_longitude_is_nirayana": "AllPlanetLongitude(Time time)" in core_source and "PlanetNirayanaLongitude" in core_source,
    }
    commit = None
    try:
        commit = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        pass
    files = {}
    for relative in ("Library/Library.csproj", "Library/Data/Time.cs", "Library/Logic/Tools.cs", "Library/Logic/Calculate/Core.cs"):
        files[relative] = hashlib.sha256((root / relative).read_bytes()).hexdigest()
    return {
        "source": "https://github.com/VedAstro/VedAstro",
        "source_commit": commit,
        "library_version": version_match.group(1) if version_match else None,
        "source_contract_status": "verified" if all(checks.values()) else "blocked",
        "checks": checks,
        "timezone_contract": {
            "zero_offset": "auto_lookup_sentinel" if checks["zero_offset_auto_lookup"] else "blocked",
            "negative_offset": "literal_offset" if checks["offset_parse_exact"] else "blocked",
            "conclusion": "+00:00 and the location's real offset may intentionally produce identical results.",
        },
        "longitude_contract": {"AllPlanetLongitude": "nirayana" if checks["all_planet_longitude_is_nirayana"] else "blocked"},
        "deployment_identity_status": "blocked",
        "deployment_identity_reason": "Remote responses expose neither library version nor source commit.",
        "files": files,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit_source(args.source_root)
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["source_contract_status"] == "verified" else 2


if __name__ == "__main__":
    raise SystemExit(main())
