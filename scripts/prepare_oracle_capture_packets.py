#!/usr/bin/env python3
"""Prepare fillable external-oracle evidence packets and operator notes."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "scripts"))

from oracle_collection_queue import build_queue, write_evidence_packets  # noqa: E402
from oracle_evidence_validator import build_report  # noqa: E402


def _resolve(path: str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return ROOT_DIR / candidate


def _load_json(path: str) -> dict[str, Any]:
    with _resolve(path).open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(value, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def _first_priority_packet(queue: dict[str, Any], validator_report: dict[str, Any], output_path: Path) -> Path:
    by_capture_id = {
        packet.get("capture_id"): packet
        for task in queue.get("tasks", [])
        if isinstance((packet := task.get("evidence_packet", {})), dict)
    }
    for packet_result in validator_report.get("packets", []):
        if packet_result.get("valid") is True:
            continue
        capture_id = packet_result.get("capture_id")
        if not capture_id or capture_id not in by_capture_id:
            continue
        return output_path / f"{capture_id}.json"

    packets = sorted(path for path in output_path.glob("external_*.json"))
    if not packets:
        return output_path / "external_oracle_packet.json"
    return packets[0]


def _write_next_steps(path: Path, oracle_file: str, output_dir: str, first_packet: str) -> None:
    text = f"""# External Oracle Capture Next Steps

First priority packet:

`{os.path.basename(first_packet)}`

## Fill The Packet

1. Open JHora, PyJHora, VedAstro, or another documented external source.
2. Use the exact birth data, ayanamsa, node mode, timezone, and settings in the packet.
3. Save a redacted screenshot or stdout snippet under `references/oracle/artifacts/`.
4. Fill missing metadata fields and missing `target_placeholders`.
5. Set or keep `status` as `external_verified` only after the artifact and target values are filled.

不得把本仓库本地输出当作 external oracle。

## Apply The Packet

```bash
python3 scripts/oracle_collection_queue.py \\
  --oracle-file {oracle_file} \\
  --apply-packet {first_packet} \\
  --format json
```

## Validate Again

```bash
python3 scripts/oracle_collection_queue.py \\
  --oracle-file {oracle_file} \\
  --format json > /tmp/jyotish_oracle_queue_filled.json

python3 scripts/oracle_evidence_validator.py \\
  --queue-file /tmp/jyotish_oracle_queue_filled.json
```

Packets in `{output_dir}` must not become valid until real external evidence is filled.
"""
    path.write_text(text, encoding="utf-8")


def prepare_packets(oracle_file: str, output_dir: str) -> dict[str, Any]:
    output_path = _resolve(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    oracle = _load_json(oracle_file)
    queue = build_queue(oracle)
    packet_count = write_evidence_packets(queue, str(output_path))
    validator_report = build_report(queue)

    packets = sorted(path.name for path in output_path.glob("external_*.json"))
    first_priority_path = _first_priority_packet(queue, validator_report, output_path)

    manifest = {
        "scope": "external_oracle_capture_packet_manifest",
        "oracle_file": oracle_file,
        "packet_count": packet_count,
        "packets": packets,
        "first_priority_packet": str(first_priority_path),
        "validator_summary": validator_report["summary"],
    }
    _write_json(output_path / "capture_manifest.json", manifest)
    _write_next_steps(output_path / "OPERATOR_NEXT_STEPS.md", oracle_file, output_dir, str(first_priority_path))

    return {
        "scope": "external_oracle_capture_packet_preparation",
        "oracle_file": oracle_file,
        "output_dir": str(output_path),
        "packet_count": packet_count,
        "first_priority_packet": str(first_priority_path),
        "validator_summary": validator_report["summary"],
        "manifest": str(output_path / "capture_manifest.json"),
        "operator_next_steps": str(output_path / "OPERATOR_NEXT_STEPS.md"),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare external oracle capture packets")
    parser.add_argument("--oracle-file", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    print(json.dumps(prepare_packets(args.oracle_file, args.output_dir), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
