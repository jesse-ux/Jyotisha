#!/usr/bin/env python3
"""Minimal local env loader for repo-scoped developer configuration."""

from __future__ import annotations

import os
from pathlib import Path


DEFAULT_ENV_FILES = (".env.local", ".jyotish.local.env")
_LOADED_ROOTS: set[Path] = set()


def _parse_env_line(line: str) -> tuple[str, str] | None:
    text = line.strip()
    if not text or text.startswith("#") or "=" not in text:
        return None
    key, value = text.split("=", 1)
    key = key.strip()
    value = value.strip()
    if not key:
        return None
    if value and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    return key, value


def load_local_env(root: str | Path | None = None) -> list[Path]:
    if os.environ.get("JYOTISH_SKIP_LOCAL_ENV", "").strip().lower() in {"1", "true", "yes"}:
        return []

    repo_root = (Path(root) if root is not None else Path(__file__).resolve().parents[1]).resolve()
    if repo_root in _LOADED_ROOTS:
        return []
    _LOADED_ROOTS.add(repo_root)

    loaded: list[Path] = []
    for name in DEFAULT_ENV_FILES:
        path = repo_root / name
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            parsed = _parse_env_line(line)
            if not parsed:
                continue
            key, value = parsed
            os.environ.setdefault(key, value)
        loaded.append(path)
    return loaded
