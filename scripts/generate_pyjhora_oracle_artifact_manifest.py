#!/usr/bin/env python3
"""Generate a tracked manifest for PyJHora black-box oracle artifacts."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = ROOT / "references" / "oracle" / "artifacts"
PENDING_DIR = ARTIFACTS_DIR / "pending_packets"
OUTPUT_PATH = ARTIFACTS_DIR / "pyjhora_oracle_artifact_manifest.json"


def _front_for_name(name: str) -> str:
    lowered = name.lower()
    if "varshaphala" in lowered or "sahams" in lowered or "tajika" in lowered:
        return "tajika_sahams"
    if "shadbala" in lowered or "moon_longitude" in lowered:
        return "shadbala"
    return "dasha"


def _relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def build_manifest() -> dict[str, Any]:
    artifacts = sorted(
        path for path in ARTIFACTS_DIR.glob("pyjhora_*")
        if path.is_file() and path.name != OUTPUT_PATH.name
    )
    pending_packets = sorted(
        path for path in PENDING_DIR.glob("*pyjhora_20260627.json")
        if path.is_file()
    )

    fronts: dict[str, dict[str, Any]] = defaultdict(lambda: {"artifact_count": 0, "packet_count": 0, "artifacts": [], "pending_packets": []})
    for artifact in artifacts:
        front = _front_for_name(artifact.name)
        fronts[front]["artifact_count"] += 1
        fronts[front]["artifacts"].append(artifact.name)
    for packet in pending_packets:
        front = _front_for_name(packet.name)
        fronts[front]["packet_count"] += 1
        fronts[front]["pending_packets"].append(packet.name)

    report = {
        "scope": "pyjhora_oracle_artifact_manifest",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifact_count": len(artifacts),
        "packet_count": len(pending_packets),
        "artifacts": [path.name for path in artifacts],
        "pending_packets": [path.name for path in pending_packets],
        "fronts": {
            front: {
                "artifact_count": payload["artifact_count"],
                "packet_count": payload["packet_count"],
                "artifacts": payload["artifacts"],
                "pending_packets": payload["pending_packets"],
            }
            for front, payload in sorted(fronts.items())
        },
        "files": {
            "manifest": _relative(OUTPUT_PATH),
            "artifacts_dir": _relative(ARTIFACTS_DIR),
            "pending_packets_dir": _relative(PENDING_DIR),
        },
        "boundary": (
            "These files are black-box external evidence only. They document PyJHora outputs and "
            "pending oracle packets without importing AGPL code into the local skill implementation."
        ),
    }
    OUTPUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    print(json.dumps(build_manifest(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
