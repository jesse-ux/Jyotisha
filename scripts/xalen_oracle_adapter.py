#!/usr/bin/env python3
"""Run the pinned Apache-2.0 Xalen oracle probe and preserve raw JSON."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "benchmarks/xalen_oracle/Cargo.toml"
COMMIT = "cc6edbec1f748ebdc4950ae6198f575c5ada73fa"


def run_probe(payload: dict) -> dict:
    completed = subprocess.run(
        ["cargo", "run", "--quiet", "--locked", "--manifest-path", str(MANIFEST)],
        input=json.dumps(payload), text=True, capture_output=True, timeout=300, check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "xalen probe failed")
    raw = json.loads(completed.stdout)
    return {
        "status": "raw_verified",
        "engine": "xalen-ephemeris",
        "source_commit": COMMIT,
        "license": "Apache-2.0",
        "raw": raw,
        "boundary": "Fourth observation only; no majority-vote truth promotion.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--mode", choices=["shared_input", "independent_ephemeris"], default="shared_input")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    payload["mode"] = args.mode
    report = run_probe(payload)
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
