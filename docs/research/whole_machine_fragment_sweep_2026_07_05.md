# Whole-Machine Jyotish Fragment Sweep 2026-07-05

## Scope

Read-only sweep for project source, local mirrors, Codex work folders, WorkBuddy copies, downloads, desktop artifacts, and configured cloud git remote. No files were deleted or moved.

## Git State

Current workspace:

- Path: `<repo>`
- Branch: `codex/release-hygiene-ci`
- Upstream: `origin/codex/release-hygiene-ci`
- Remote fetch: `git@github.com:732642856/yinduzhanxing.git`
- Remote push: `https://github.com/732642856/yinduzhanxing.git`
- Worktree: dirty; do not reset or overwrite user changes.

Remote checks:

- `git ls-remote --heads --tags origin` failed with `ssh: connect to host github.com port 22: Operation timed out`.
- `git ls-remote --heads --tags https://github.com/732642856/yinduzhanxing.git` failed with `LibreSSL SSL_connect: SSL_ERROR_SYSCALL in connection to github.com:443`.
- `python3 scripts/remote_repo_visibility_check.py` now records this state structurally and sets `must_not_claim_synced: true` unless terminal refs are verified.
- `python3 scripts/remote_repo_visibility_check.py --timeout 8` returned `status: blocked`; SSH timed out, HTTPS git returned `SSL_ERROR_SYSCALL`, and GitHub API returned `UNEXPECTED_EOF_WHILE_READING`.
- `python3 scripts/pre_work_check.py --remote-timeout 8 --command-timeout 45` later returned `status: pass` with `must_not_claim_synced: false`; network was observed to fluctuate, so this proves terminal visibility for that run, not that local dirty work was pushed.
- Browser/Web access to `https://github.com/732642856/yinduzhanxing` succeeded.
- Browser/Web branch page shows repository is public, default `main` updated Jun 13, 2026, and active `codex/release-hygiene-ci` updated Jul 2, 2026.
- Browser/Web commit page for `main` shows latest visible commit `4ff6248 Complete v6.9.14 precision modules` on Jun 13, 2026.

Conclusion: cloud repo exists and is browser-readable, but terminal ref parity is `blocked` for this sweep.

## Local Git Repositories Found

Relevant candidates from bounded split scan:

- `<repo>` — current main workspace; only implementation target.
- `<home>/.workbuddy/skills/jyotish-vedic-astrology` — dirty historical/distribution mirror; read-only reference.
- `<home>/.workbuddy/skills` — WorkBuddy skills container.
- `<home>/Documents/星轨talk` — adjacent talk engine repo with Jyotish adapters.
- `<home>/Documents/Codex/2026-06-20/732642856-talk-https-github-com-732642856/work/talk-active` — older Codex talk worktree.
- `<home>/Documents/Codex/2026-06-20/732642856-talk-https-github-com-732642856/work/talk` — older Codex talk worktree.
- `<home>/Documents/Codex/2026-06-18/new-chat-4/work/starcanvas` — adjacent astrology/canvas project.
- `<home>/Documents/Codex/2026-06-18/new-chat-4/work/starcanvas-active` — adjacent astrology/canvas project.
- `<home>/Documents/星轨画布` — adjacent astrology/canvas project.
- `<home>/WorkBuddy` and dated WorkBuddy folders — historical/reference material.

## High-Value Fragment Files

Keep these in mind before adapter/oracle/skill work:

- `<home>/Documents/星轨talk/engines-repo/jyotish/jyotish-adapter.js`
- `<home>/Documents/星轨talk/engines-repo/jyotish/vedic-calc-runner.py`
- `<home>/Documents/星轨talk/engines-repo/jyotish/jyotishganit-adapter.js`
- `<home>/Documents/星轨talk/engines-repo/jyotish/jyotishganit-runner.py`
- `<home>/Documents/星轨talk/engines-repo/local-jyotish-reference-audit.js`
- `<home>/Documents/星轨talk/reports/local-jyotish-reference-audit.md`
- `<home>/Documents/ObsidianVault/03_研究_术数占星/印度占星 Jyotish.md`
- `<home>/Documents/ObsidianVault/03_研究_术数占星/印度占星研究结论 v3.md`
- `<home>/Documents/ObsidianVault/03_研究_术数占星/PRIVATE_REDACTED_CASE · 印度占星完整解盘报告 v2.md`
- `<home>/Documents/Codex/2026-06-20/732642856-yinduzhanxing-https-github-com-732642856/outputs/yinduzhanxing_local_audit_2026-06-20.md`

## Boundaries

- Main repo remains the runtime source of truth.
- `.workbuddy` is historical/distribution reference only.
- Obsidian, Downloads, Desktop, and personal reports may contain private material; do not commit raw contents.
- Adjacent repos may inform adapter design but are not runtime dependencies.
- Cloud-git parity remains blocked until terminal `git ls-remote` or equivalent succeeds.

## Acceptance Commands

```bash
python3 scripts/pre_work_check.py --remote-timeout 8 --command-timeout 45
python3 -m pytest -q tests/test_runtime_import_boundaries.py tests/test_project_fragment_governance.py tests/test_preflight_fragment_scan.py tests/test_remote_repo_visibility_check.py tests/test_pre_work_check.py
```

```bash
git status --short --branch
git remote -v
```
