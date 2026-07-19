#!/usr/bin/env python3
"""Build effective skill capability view by applying skill_truth_overlay."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_effective_registry(registry_path: Path, overlay_path: Path) -> dict:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    overlay = json.loads(overlay_path.read_text(encoding="utf-8"))
    overrides = {row["technique_id"]: row for row in overlay["overrides"]}
    rows = []
    for technique_id, raw in sorted(registry["techniques"].items()):
        override = overrides.get(technique_id)
        rows.append(
            {
                "technique_id": technique_id,
                "registry_status": raw.get("status"),
                "effective_status": override["corrected_status"] if override else raw.get("status"),
                "overlay_evidence": override.get("evidence") if override else "",
                "overlay_reason": override.get("reason") if override else "",
                "public_label": raw.get("public_label") or raw.get("name") or technique_id,
            }
        )
    for technique_id, override in sorted(overrides.items()):
        if technique_id not in registry["techniques"]:
            rows.append(
                {
                    "technique_id": technique_id,
                    "registry_status": override["registry_status"],
                    "effective_status": override["corrected_status"],
                    "overlay_evidence": override["evidence"],
                    "overlay_reason": override["reason"],
                    "public_label": technique_id,
                }
            )
    return {
        "scope": "effective_skill_capability_view",
        "truth_source_order": [str(overlay_path), str(registry_path)],
        "technique_count": len(rows),
        "overlay_count": len(overrides),
        "techniques": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=Path("references/technique_registry.json"))
    parser.add_argument("--overlay", type=Path, default=Path("references/oracle/skill_truth_overlay_2026_07_19.json"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    view = build_effective_registry(args.registry, args.overlay)
    text = json.dumps(view, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
