#!/usr/bin/env python3
"""Create a secret-free identity contract for a pinned VedAstro container build."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_commit(root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=False
    )
    return completed.stdout.strip() if completed.returncode == 0 else ""


def _inspect_image(tag: str) -> dict[str, Any] | None:
    completed = subprocess.run(
        ["docker", "image", "inspect", tag], text=True, capture_output=True, check=False
    )
    if completed.returncode != 0:
        return None
    payload = json.loads(completed.stdout)
    return payload[0] if isinstance(payload, list) and payload else None


def build_identity(
    source_root: Path,
    *,
    source_commit: str | None = None,
    image_inspect: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source_root = source_root.resolve()
    dockerfile = source_root / "API/Dockerfile"
    if not dockerfile.is_file():
        raise FileNotFoundError(dockerfile)
    docker_text = dockerfile.read_text(encoding="utf-8")
    base_images: list[str] = []
    stage_names: set[str] = set()
    for match in re.finditer(
        r"^FROM\s+([^\s]+)(?:\s+AS\s+([^\s]+))?",
        docker_text,
        flags=re.MULTILINE | re.IGNORECASE,
    ):
        image, stage = match.group(1), match.group(2)
        if image not in stage_names:
            base_images.append(image)
        if stage:
            stage_names.add(stage)
    project_files = sorted(source_root.glob("**/*.csproj"))
    project_hashes = {
        str(path.relative_to(source_root)): _sha256(path)
        for path in project_files
        if "/bin/" not in path.as_posix() and "/obj/" not in path.as_posix()
    }
    image_id = (image_inspect or {}).get("Id", "")
    repo_digests = (image_inspect or {}).get("RepoDigests") or []
    return {
        "scope": "vedastro_reproducible_build_identity",
        "source_root": str(source_root),
        "source_commit": source_commit or _git_commit(source_root),
        "dockerfile_path": "API/Dockerfile",
        "dockerfile_sha256": _sha256(dockerfile),
        "base_images": base_images,
        "project_file_hashes": project_hashes,
        "image_id": image_id,
        "repo_digests": repo_digests,
        "status": "reproducible_candidate_built" if image_id else "source_pinned_image_not_built",
        "boundary": "Identifies the pinned local candidate only; it does not identify api.vedastro.org.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_root", type=Path)
    parser.add_argument("--image-tag", default="")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = build_identity(
        args.source_root,
        image_inspect=_inspect_image(args.image_tag) if args.image_tag else None,
    )
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
