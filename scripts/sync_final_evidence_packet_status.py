#!/usr/bin/env python3
"""Inspect public JHora evidence; optionally repair an explicitly local packet."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "references" / "evidence_manifests" / "jhora_master_evidence_manifest.json"
LOCAL_EVIDENCE_DIR = ROOT / "scratch" / "local" / "pdf_review_123456"
PACKET_RE = re.compile(r"\.v(\d+)\.json$")


def load_manifest() -> dict:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    required = {"schema_version", "artifact_id", "source_scope", "release_gate", "evidence"}
    missing = sorted(required - manifest.keys())
    if missing:
        raise SystemExit(f"invalid JHora evidence manifest; missing: {', '.join(missing)}")
    if manifest["artifact_id"] != "jhora_master_evidence":
        raise SystemExit("invalid JHora evidence manifest artifact_id")
    if manifest["release_gate"].get("local_scratch_required") is not False:
        raise SystemExit("public JHora evidence manifest must not require local scratch")
    return manifest


def latest_packet(work_dir: Path | None = None) -> tuple[int, Path]:
    work_dir = work_dir or LOCAL_EVIDENCE_DIR
    packets: list[tuple[int, Path]] = []
    for path in work_dir.glob("jhora_master_evidence_packet_public_sample_19550224_1915.v*.json"):
        match = PACKET_RE.search(path.name)
        if match:
            packets.append((int(match.group(1)), path))
    if not packets:
        raise FileNotFoundError("no versioned local JHora master evidence packets found")
    return max(packets)


def sync_local_packet_metadata(work_dir: Path | None = None) -> str:
    work_dir = work_dir or LOCAL_EVIDENCE_DIR
    version, path = latest_packet(work_dir)
    packet = json.loads(path.read_text(encoding="utf-8"))
    metadata = packet.setdefault("metadata", {})
    wanted_version = f"v{version}"
    changed = False
    for key, value in {
        "status": "final_output_v1",
        "current_version": wanted_version,
        "packet_version": wanted_version,
        "canonical_packet": path.name,
    }.items():
        if metadata.get(key) != value:
            metadata[key] = value
            changed = True
    if packet.get("status") != "final_output_v1":
        packet["status"] = "final_output_v1"
        changed = True
    if changed:
        path.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    ledger = work_dir / "evidence_packet_status_ledger_public_sample_19550224_1915.md"
    if ledger.exists():
        text = ledger.read_text(encoding="utf-8")
        line_re = re.compile(
            r"\| Master evidence packet \| `jhora_master_evidence_packet_public_sample_19550224_1915\.v\d+\.json` \| active \| Current canonical structured packet\. \|"
        )
        wanted_line = f"| Master evidence packet | `{path.name}` | active | Current canonical structured packet. |"
        new_text = line_re.sub(wanted_line, text, count=1)
        if new_text != text:
            ledger.write_text(new_text, encoding="utf-8")
    return path.name


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sync-local", action="store_true", help="Repair local scratch metadata; never required for release.")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    manifest = load_manifest()
    result = {
        "artifact_id": manifest["artifact_id"],
        "manifest_path": str(MANIFEST_PATH.relative_to(ROOT)),
        "release_gate": manifest["release_gate"],
        "evidence": manifest["evidence"],
        "local_scratch": "not_inspected",
    }
    if args.sync_local:
        result["local_scratch"] = {"synced_packet": sync_local_packet_metadata()}
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"validated {result['manifest_path']}; local scratch {result['local_scratch']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
