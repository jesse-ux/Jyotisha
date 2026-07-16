#!/usr/bin/env python3
"""Validate a reviewable external raw-oracle artifact before parity replay."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


SUPPORTED_ENGINES = {"VedAstro", "PyJHora_JHora", "jyotishganit"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_raw_oracle_import(engine: str, artifact_path: str | Path, metadata: dict[str, Any]) -> dict[str, Any]:
    if engine not in SUPPORTED_ENGINES:
        raise ValueError(f"unsupported oracle engine: {engine}")
    path = Path(artifact_path).expanduser().resolve()
    if not path.is_file():
        raise ValueError("source artifact does not exist")
    required = ("case_id", "license_boundary", "collection_method", "birth_data_policy")
    missing = [key for key in required if not metadata.get(key)]
    if missing:
        raise ValueError(f"missing raw-oracle metadata: {', '.join(missing)}")
    if metadata["birth_data_policy"] != "public_case_only":
        raise ValueError("raw-oracle imports require public_case_only birth data")
    return {
        "scope": "external_raw_oracle_import",
        "schema_version": 1,
        "engine": engine,
        "status": "raw_imported_uncompared",
        "source_artifact": str(path),
        "source_artifact_sha256": sha256_file(path),
        "metadata": {
            key: metadata[key]
            for key in (*required, "engine_version", "ayanamsa", "node_mode", "captured_at")
            if metadata.get(key) is not None
        },
        "comparison_ready": False,
        "boundary": "Import integrity only. Parity is external_verified only after normalized field comparison passes.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", required=True, choices=sorted(SUPPORTED_ENGINES))
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--metadata-json", required=True, help="JSON file containing import metadata")
    args = parser.parse_args()
    metadata = json.loads(Path(args.metadata_json).read_text(encoding="utf-8"))
    print(json.dumps(build_raw_oracle_import(args.engine, args.artifact, metadata), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
