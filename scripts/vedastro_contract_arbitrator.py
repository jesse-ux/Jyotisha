#!/usr/bin/env python3
"""Arbitrate multiple VedAstro contract probe runs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def arbitrate(runs: list[dict[str, Any]]) -> dict[str, Any]:
    vectors = [_canonical(run.get("normalized_vectors")) for run in runs]
    method_statuses = [str((run.get("method_contract") or {}).get("status")) for run in runs]
    version_statuses = [str((run.get("api_version_contract") or {}).get("status")) for run in runs]
    time_signatures = [_canonical(run.get("time_contract")) for run in runs]
    stable = bool(runs) and len(set(vectors)) == 1
    resolved = len(runs) >= 3 and stable and set(method_statuses) == {"resolved"} and set(version_statuses) == {"captured"} and len(set(time_signatures)) == 1
    return {
        "scope": "vedastro_contract_cross_run_arbitration",
        "status": "resolved" if resolved else "blocked",
        "run_count": len(runs),
        "cross_run_normalized_stable": stable,
        "method_statuses": method_statuses,
        "api_version_statuses": version_statuses,
        "time_contract_stable": bool(runs) and len(set(time_signatures)) == 1,
        "field_statuses": {"VedAstro.D1.longitude": "resolved" if resolved else "blocked"},
        "reason": None if resolved else "contract_version_or_method_semantics_not_stable_across_three_versioned_runs",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--output", type=Path, default=ROOT / "references" / "oracle" / "vedastro_contract_arbitration_2026_07_17.json")
    args = parser.parse_args()
    rows = []
    artifacts = []
    for raw_path in args.paths:
        path = Path(raw_path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows.append(payload)
        artifacts.append({"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "contract_status": payload.get("contract_status")})
    report = arbitrate(rows)
    report["artifacts"] = artifacts
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
