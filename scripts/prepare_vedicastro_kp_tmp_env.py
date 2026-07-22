#!/usr/bin/env python3
"""Prepare an isolated temporary dependency path for VedicAstro KP probes.

Installs only under /tmp/vedicastro_flatlib_probe. Never mutates project
requirements, venvs, package-locks, or runtime dependencies.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


TARGET = Path("/tmp/vedicastro_flatlib_probe")
REQUIRED_PACKAGES = {
    "flatlib": "git+https://github.com/diliprk/flatlib.git@sidereal#egg=flatlib",
    "polars": "polars",
    "timezonefinder": "timezonefinder",
    "pyswisseph": "pyswisseph",
}


def stable(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def digest_tree(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    for file in sorted(p for p in path.rglob("*") if p.is_file()):
        rel = file.relative_to(path).as_posix()
        h.update(rel.encode("utf-8"))
        try:
            h.update(file.read_bytes())
        except OSError:
            continue
    return h.hexdigest()


def package_versions(target: Path) -> dict[str, str | None]:
    sys.path.insert(0, str(target))
    versions: dict[str, str | None] = {}
    for name in REQUIRED_PACKAGES:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def install(target: Path) -> dict[str, Any]:
    target.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--upgrade",
        "--target",
        str(target),
        *REQUIRED_PACKAGES.values(),
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=180)
    return {
        "command": cmd,
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }


def build_payload(target: Path, install_result: dict[str, Any] | None = None) -> dict[str, Any]:
    versions = package_versions(target) if target.exists() else {name: None for name in REQUIRED_PACKAGES}
    ready = all(versions.values())
    payload: dict[str, Any] = {
        "scope": "vedicastro_kp_tmp_env_preparer",
        "created_at": "2026-07-21",
        "target": str(target),
        "project_dependency_mutation_allowed": False,
        "required_packages": REQUIRED_PACKAGES,
        "package_versions": versions,
        "target_tree_hash": digest_tree(target),
        "claim_status": "runtime_dependency_ready" if ready else "blocked_runtime_dependency",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "boundary": "dependency_preparation_only_no_kp_oracle_truth",
    }
    if install_result is not None:
        payload["install_result"] = install_result
    return payload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default=str(TARGET))
    ap.add_argument("--report-only", action="store_true")
    ap.add_argument("--clean", action="store_true")
    args = ap.parse_args()
    target = Path(args.target)
    if args.clean and target.exists() and str(target).startswith("/tmp/"):
        shutil.rmtree(target)
    install_result = None if args.report_only else install(target)
    payload = build_payload(target, install_result)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if args.report_only or payload["claim_status"] == "runtime_dependency_ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
