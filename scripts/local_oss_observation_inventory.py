#!/usr/bin/env python3
"""Inventory local OSS Jyotish candidates as observation-only sources."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "references" / "open_source_sources"
CANDIDATES = ["VedicAstro", "jyotishganit", "panchanga_api", "rishi-ai-mcp", "jaimini-tropical", "vedic-astro-skills"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_commit(path: Path) -> str | None:
    try:
        return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def first_existing(path: Path, names: list[str]) -> Path | None:
    for name in names:
        p = path / name
        if p.exists():
            return p
    return None


def license_hint(path: Path) -> dict[str, Any]:
    p = first_existing(path, ["LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"])
    if not p:
        return {"status": "missing", "file": None, "sha256": None, "hint": "unknown"}
    text = p.read_text(encoding="utf-8", errors="ignore")[:3000].lower()
    if "mit license" in text or "permission is hereby granted" in text:
        hint = "MIT"
    elif "apache license" in text:
        hint = "Apache-2.0"
    elif "bsd" in text:
        hint = "BSD-like"
    elif "gnu affero" in text:
        hint = "AGPL"
    elif "gnu general public license" in text:
        hint = "GPL"
    else:
        hint = "unknown"
    return {"status": "present", "file": str(p.relative_to(ROOT)), "sha256": sha256_file(p), "hint": hint}


def file_manifest(path: Path) -> list[dict[str, Any]]:
    wanted = ["README.md", "README.rst", "pyproject.toml", "package.json", "pubspec.yaml", "requirements.txt"]
    rows = []
    for name in wanted:
        p = path / name
        if p.exists():
            rows.append({"path": str(p.relative_to(ROOT)), "sha256": sha256_file(p)})
    return rows


def api_hints(path: Path) -> list[str]:
    hints = []
    for pattern in ("*.py", "*.ts", "*.js", "*.dart"):
        for p in list(path.rglob(pattern))[:200]:
            if any(part in {".git", "node_modules", "__pycache__"} for part in p.parts):
                continue
            rel = str(p.relative_to(path))
            name = p.stem.lower()
            if any(k in name or k in rel.lower() for k in ["panch", "muhur", "dasha", "kp", "chart", "asht", "shadbala", "jaimini"]):
                hints.append(rel)
            if len(hints) >= 30:
                return hints
    return hints


def main() -> int:
    rows = []
    for name in CANDIDATES:
        path = BASE / name
        if not path.exists():
            rows.append({"project_id": name, "status": "missing"})
            continue
        rows.append({
            "project_id": name,
            "status": "present",
            "local_path": str(path.relative_to(ROOT)),
            "git_commit": git_commit(path),
            "license": license_hint(path),
            "manifest_files": file_manifest(path),
            "api_surface_hints": api_hints(path),
            "claim_status": "observation_only",
            "runtime_dependency_allowed": False,
            "truth_upgrade_allowed": False,
        })
    out = {
        "scope": "local_oss_observation_inventory",
        "created_at": "2026-07-19",
        "status": "complete",
        "claim_status": "observation_only",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "boundary": "Local OSS candidates are pinned for reuse/probe triage only. License and hash metadata do not validate astrological truth.",
        "projects": rows,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
