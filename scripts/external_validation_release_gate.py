#!/usr/bin/env python3
"""Verify the commercial public external-validation evidence release."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "references" / "evidence_manifests" / "commercial_external_validation_release.v1.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def evaluate_manifest(manifest_path: Path = DEFAULT_MANIFEST) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assets = []
    for item in manifest["assets"]:
        path = ROOT / item["path"]
        observed = sha256_file(path) if path.is_file() else None
        integrity = "verified" if observed == item["sha256"] else ("missing" if observed is None else "mismatch")
        assets.append(
            {
                "id": item["id"],
                "path": item["path"],
                "scope": item["scope"],
                "expected_sha256": item["sha256"],
                "observed_sha256": observed,
                "integrity": integrity,
            }
        )

    verified = sum(item["integrity"] == "verified" for item in assets)
    boundaries = manifest["release_boundaries"]
    return {
        "artifact_id": manifest["artifact_id"],
        "release_scope": manifest["release_scope"],
        "status": "pass" if verified == len(assets) else "blocked",
        "assets": assets,
        "engines": manifest["engines"],
        "summary": {
            "assets_total": len(assets),
            "assets_verified": verified,
            "external_oracle_closure": boundaries["external_oracle_closure"],
            "prediction_accuracy_verified": boundaries["prediction_accuracy_verified"],
            "production_tuning_allowed": boundaries["production_tuning_allowed"],
        },
        "boundary": "A passing release validates only versioned public evidence integrity. It does not close external oracles, verify prediction accuracy, or authorize production tuning.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--require-match", action="store_true")
    args = parser.parse_args()
    report = evaluate_manifest(args.manifest)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"external validation release: {report['status']}")
        print(f"assets: {report['summary']['assets_verified']}/{report['summary']['assets_total']} verified")
        print(f"VedAstro: {report['engines']['VedAstro']['status']}")
        print(f"production_tuning_allowed: {report['summary']['production_tuning_allowed']}")
    return 0 if report["status"] == "pass" or not args.require_match else 1


if __name__ == "__main__":
    raise SystemExit(main())
