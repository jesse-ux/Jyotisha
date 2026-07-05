#!/usr/bin/env python3
"""Print or install Cline MCP config for this Jyotish repo."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def build_config(repo_root: Path, python_bin: str) -> dict:
    repo_root = repo_root.resolve()
    return {
        "mcpServers": {
            "jyotish": {
                "command": python_bin,
                "args": [str(repo_root / "mcp_server.py")],
                "cwd": str(repo_root),
                "env": {
                    "PYTHONPATH": str(repo_root / "scripts"),
                },
            }
        }
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(ROOT), help="repo root for generated paths")
    parser.add_argument("--python", default=sys.executable, help="Python executable for Cline to run")
    parser.add_argument(
        "--install-project",
        action="store_true",
        help="write project-local .cline/mcp.json for this checkout",
    )
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    config = build_config(repo_root, args.python)
    text = json.dumps(config, ensure_ascii=False, indent=2)
    if args.install_project:
        target = repo_root / ".cline" / "mcp.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text + "\n", encoding="utf-8")
        print(str(target))
        return 0
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

