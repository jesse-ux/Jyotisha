#!/usr/bin/env python3
"""Generate a practical blank kit for the first external-oracle packets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from first_oracle_packet_assistant import build_report  # noqa: E402


FRONTS = ["dasha", "tajika_sahams", "shadbala"]


def _load_json(path: str) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_next_steps(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# Blank Oracle Kit Next Steps",
        "",
        "This kit prepares the current shortest external-oracle closure path.",
        "",
        "不得把本仓库本地输出当作 external oracle。",
        "",
        "## Recommended Order",
        "",
    ]
    for front in manifest["recommended_front_order"]:
        item = manifest["fronts"][front]
        lines.extend(
            [
                f"### {front}",
                "",
                f"- case_id: `{item['case_id']}`",
                f"- packet: `{item['packet_path']}`",
                f"- missing_field_count: `{item['missing_field_count']}`",
                f"- operator_card: `{item['operator_card']}`",
                f"- metadata_missing: `{item['missing_groups']['metadata']['count']}`",
                f"- target_missing: `{item['missing_groups']['target']['count']}`",
                "",
            ]
        )
        if item["missing_groups"]["bodies"]:
            lines.append("Body breakdown:")
            lines.append("")
            for body, payload in item["missing_groups"]["bodies"].items():
                lines.append(f"- {body}: `{payload['count']}`")
            lines.append("")
        lines.extend(
            [
                "Apply after filling:",
                "",
                "```bash",
                item["apply_command"],
                "```",
                "",
                "Validate after applying:",
                "",
                "```bash",
                item["validate_command"],
                "```",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def generate_blank_oracle_kit(output_dir: str) -> dict[str, Any]:
    output_path = Path(output_dir)
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    output_path.mkdir(parents=True, exist_ok=True)

    fronts: dict[str, Any] = {}
    for front in FRONTS:
        report = build_report(front)
        packet = _load_json(report["packet_template"])
        front_dir = output_path / front
        packet_path = front_dir / f"{report['capture_id']}.json"
        _write_json(packet_path, packet)
        fronts[front] = {
            "case_id": report["case_id"],
            "capture_id": report["capture_id"],
            "packet_path": str(packet_path),
            "operator_card": report["operator_card"],
            "missing_field_count": len(report["missing_fields"]),
            "missing_groups": report["missing_groups"],
            "apply_command": report["apply_command"],
            "validate_command": report["validate_command"],
        }

    recommended_front_order = list(FRONTS)
    manifest = {
        "scope": "first_oracle_blank_kit_manifest",
        "front_count": len(FRONTS),
        "recommended_front_order": recommended_front_order,
        "fronts": fronts,
        "boundary": (
            "These packets are blank external-oracle drafts only. They must be filled from JHora, PyJHora, "
            "VedAstro, or documented printed examples, never from this repository's local engine output."
        ),
    }
    manifest_path = output_path / "blank_oracle_kit_manifest.json"
    _write_json(manifest_path, manifest)
    next_steps_path = output_path / "BLANK_ORACLE_KIT_NEXT_STEPS.md"
    _write_next_steps(next_steps_path, manifest)
    return {
        "scope": "first_oracle_blank_kit",
        "front_count": len(FRONTS),
        "recommended_front_order": recommended_front_order,
        "manifest": str(manifest_path),
        "next_steps": str(next_steps_path),
        "fronts": {front: fronts[front]["packet_path"] for front in FRONTS},
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the first external-oracle blank kit")
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = generate_blank_oracle_kit(args.output_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
