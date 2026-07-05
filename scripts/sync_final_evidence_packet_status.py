#!/usr/bin/env python3
"""Sync latest final JHora evidence packet metadata with its numeric version."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORK_DIR = ROOT / "scratch" / "local" / "pdf_review_123456"
PACKET_RE = re.compile(r"\.v(\d+)\.json$")


def latest_packet() -> tuple[int, Path]:
    packets: list[tuple[int, Path]] = []
    for path in WORK_DIR.glob("jhora_master_evidence_packet_REDACTED_DATE_REDACTED_TIME.v*.json"):
        match = PACKET_RE.search(path.name)
        if match:
            packets.append((int(match.group(1)), path))
    if not packets:
        raise SystemExit("no versioned JHora master evidence packets found")
    return max(packets)


def main() -> int:
    version, path = latest_packet()
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

    ledger = WORK_DIR / "evidence_packet_status_ledger_REDACTED_DATE_REDACTED_TIME.md"
    if ledger.exists():
        text = ledger.read_text(encoding="utf-8")
        line_re = re.compile(
            r"\| Master evidence packet \| `jhora_master_evidence_packet_REDACTED_DATE_REDACTED_TIME\.v\d+\.json` \| active \| Current canonical structured packet\. \|"
        )
        wanted_line = f"| Master evidence packet | `{path.name}` | active | Current canonical structured packet. |"
        new_text = line_re.sub(wanted_line, text, count=1)
        if new_text != text:
            ledger.write_text(new_text, encoding="utf-8")

    print(f"synced {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
