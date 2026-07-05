#!/usr/bin/env python3
"""Read-only remote repository visibility diagnostic.

This is a guardrail, not a sync tool. It never pushes, fetches, or mutates the
worktree. It records whether terminal git can verify remote refs and whether
GitHub's API is reachable as a fallback visibility signal.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib import request


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GITHUB_SLUG = "732642856/yinduzhanxing"


def run_command(args: list[str], timeout: int) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            args,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {"ok": False, "error": f"timeout after {timeout}s: {' '.join(args)}", "stdout": exc.stdout or "", "stderr": exc.stderr or ""}
    return {
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "error": "" if completed.returncode == 0 else (completed.stderr or completed.stdout).strip(),
    }


def github_slug_from_remote_url(url: str) -> str | None:
    patterns = [
        r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/.]+)(?:\.git)?$",
        r"github\.com/(?P<owner>[^/]+)/(?P<repo>[^/.]+)(?:\.git)?$",
    ]
    for pattern in patterns:
        match = re.search(pattern, url.strip())
        if match:
            return f"{match.group('owner')}/{match.group('repo')}"
    return None


def parse_ls_remote(stdout: str) -> dict[str, Any]:
    heads: dict[str, str] = {}
    tags: dict[str, str] = {}
    for line in stdout.splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        sha, ref = parts
        if ref.startswith("refs/heads/"):
            heads[ref.removeprefix("refs/heads/")] = sha
        elif ref.startswith("refs/tags/") and not ref.endswith("^{}"):
            tags[ref.removeprefix("refs/tags/")] = sha
    return {"heads": heads, "tags": tags, "ref_count": len(heads) + len(tags)}


def git_remote_urls(timeout: int) -> list[str]:
    urls: list[str] = []
    for args in (["git", "remote", "get-url", "origin"], ["git", "remote", "get-url", "--push", "origin"]):
        result = run_command(args, timeout)
        if result["ok"]:
            url = result["stdout"].strip()
            if url and url not in urls:
                urls.append(url)
    return urls


def git_ls_remote(url: str, timeout: int) -> dict[str, Any]:
    result = run_command(["git", "ls-remote", "--heads", "--tags", url], timeout)
    parsed = parse_ls_remote(result.get("stdout", "")) if result["ok"] else {"heads": {}, "tags": {}, "ref_count": 0}
    return {"method": "git_ls_remote", "url": url, **parsed, "ok": result["ok"], "error": result.get("error", "")}


def github_api_branches(slug: str, timeout: int) -> dict[str, Any]:
    url = f"https://api.github.com/repos/{slug}/branches"
    req = request.Request(url, headers={"User-Agent": "jyotish-preflight/1.0", "Accept": "application/vnd.github+json"})
    try:
        with request.urlopen(req, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # network/SSL/status errors are diagnostic data here
        return {"method": "github_api_branches", "url": url, "ok": False, "branches": [], "error": f"{type(exc).__name__}: {exc}"}
    branches = [item.get("name", "") for item in payload if isinstance(item, dict)]
    return {"method": "github_api_branches", "url": url, "ok": bool(branches), "branches": branches, "error": ""}


def build_report(timeout: int) -> dict[str, Any]:
    local_branch = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], timeout)
    local_head = run_command(["git", "rev-parse", "HEAD"], timeout)
    urls = git_remote_urls(timeout)
    slug = next((github_slug_from_remote_url(url) for url in urls if github_slug_from_remote_url(url)), DEFAULT_GITHUB_SLUG)
    git_checks = [git_ls_remote(url, timeout) for url in urls] or [git_ls_remote(f"https://github.com/{slug}.git", timeout)]
    api_check = github_api_branches(slug, timeout)
    git_verified = any(check["ok"] and check["ref_count"] > 0 for check in git_checks)
    api_visible = api_check["ok"]
    status = "verified" if git_verified else ("web_visible_git_blocked" if api_visible else "blocked")
    return {
        "scope": "remote_repo_visibility_check",
        "status": status,
        "must_not_claim_synced": status != "verified",
        "local": {
            "branch": local_branch.get("stdout", "").strip(),
            "head": local_head.get("stdout", "").strip(),
        },
        "github_slug": slug,
        "git_checks": git_checks,
        "github_api": api_check,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=12)
    args = parser.parse_args()
    print(json.dumps(build_report(args.timeout), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
