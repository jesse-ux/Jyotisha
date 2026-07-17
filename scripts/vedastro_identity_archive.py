#!/usr/bin/env python3
"""Archive reproducible VedAstro package identity and hosted-version gap."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.request import urlopen


REGISTRATION_URL = (
    "https://api.nuget.org/v3/registration5-semver1/"
    "vedastro.library/{version}.json"
)


def _json_url(url: str, timeout: float) -> dict:
    with urlopen(url, timeout=timeout) as response:  # noqa: S310 - fixed public NuGet URL.
        return json.loads(response.read().decode("utf-8"))


def build_archive(version: str = "1.2.0", timeout: float = 20.0) -> dict:
    registration = _json_url(REGISTRATION_URL.format(version=version), timeout)
    catalog_url = registration["catalogEntry"]
    catalog = _json_url(catalog_url, timeout)
    deps = []
    for group in catalog.get("dependencyGroups") or []:
        target = group.get("targetFramework")
        for dep in group.get("dependencies") or []:
            deps.append(
                {
                    "target_framework": target,
                    "id": dep["id"],
                    "range": dep["range"],
                }
            )

    return {
        "scope": "vedastro_reproducible_identity_archive",
        "package": "VedAstro.Library",
        "version": version,
        "nuget_registration_url": REGISTRATION_URL.format(version=version),
        "nuget_catalog_url": catalog_url,
        "package_content_url": registration["packageContent"],
        "package_hash_algorithm": catalog.get("packageHashAlgorithm"),
        "package_hash": catalog.get("packageHash"),
        "package_size": catalog.get("packageSize"),
        "published": catalog.get("published") or registration.get("published"),
        "catalog_commit_id": catalog.get("catalog:commitId"),
        "catalog_commit_timestamp": catalog.get("catalog:commitTimeStamp"),
        "license": catalog.get("licenseExpression"),
        "project_url": catalog.get("projectUrl"),
        "dependencies": deps,
        "self_host_candidate_status": "reproducible_package_identity_archived",
        "hosted_api_status": "blocked",
        "hosted_api_blocker": (
            "api.vedastro.org does not expose a verified build commit, package hash, "
            "DLL hash, assembly version, container digest, or method-semantics contract."
        ),
        "boundary": (
            "This archive fixes a NuGet self-host candidate identity only; it does not "
            "prove the hosted API is running this package or the same method semantics."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="1.2.0")
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = build_archive(args.version, args.timeout)
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
