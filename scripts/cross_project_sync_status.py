#!/usr/bin/env python3
"""Compare allow-listed shared contract files between the two Jyotish projects."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "references" / "cross_project_contract" / "sync_policy.v1.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_policy(path: Path = DEFAULT_POLICY) -> dict[str, Any]:
    policy = json.loads(path.read_text(encoding="utf-8"))
    if policy.get("schema_version") != 1:
        raise ValueError("sync policy schema_version must be 1")
    if policy.get("sync_model") != "research_validates_commercial_receives_mature":
        raise ValueError("sync policy must encode research-first commercial-mature flow")
    if not isinstance(policy.get("shared_files"), list) or not policy["shared_files"]:
        raise ValueError("sync policy must contain shared_files")
    return policy


def compare_peer(peer_root: Path, *, policy_path: Path = DEFAULT_POLICY, root: Path = ROOT) -> dict[str, Any]:
    policy = load_policy(policy_path)
    missing: list[str] = []
    mismatched: list[str] = []
    checked: list[dict[str, str]] = []

    for rel_path in policy["shared_files"]:
        local = root / rel_path
        peer = peer_root / rel_path
        if not local.exists() or not peer.exists():
            missing.append(rel_path)
            continue
        local_hash = _sha256(local)
        peer_hash = _sha256(peer)
        checked.append({"path": rel_path, "local_sha256": local_hash, "peer_sha256": peer_hash})
        if local_hash != peer_hash:
            mismatched.append(rel_path)

    return {
        "status": "pass" if not missing and not mismatched else "fail",
        "sync_model": policy["sync_model"],
        "checked_count": len(checked),
        "missing": missing,
        "mismatched": mismatched,
        "checked": checked,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--peer", type=Path, required=True, help="Path to the other Jyotish repository")
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--format", choices=("json",), default="json")
    args = parser.parse_args()

    report = compare_peer(args.peer, policy_path=args.policy)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
