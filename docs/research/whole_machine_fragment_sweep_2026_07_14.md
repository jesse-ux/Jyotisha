# Whole-Machine Fragment Sweep: 2026-07-14

## Scope

Bounded read-only scan of `Documents`, `WorkBuddy`, `.workbuddy`, `Downloads`,
`Desktop`, and Codex attachments. Search depth followed the command set in
`pre_work_error_ledger.md`.

## Runtime Truth

- Primary source/runtime repo: `/Users/wuyongnaren/Documents/印度占星`.
- Active branch at scan time: `codex/release-hygiene-ci`.
- `.workbuddy/skills/jyotish-vedic-astrology` is an unversioned historical
  distribution mirror. It is never a runtime source or merge source.

## Divergent Repository

- `/Users/wuyongnaren/WorkBuddy/2026-07-05-19-03-49/yinduzhanxing` is a Git
  checkout of the same remote, on `main` at `8b53983`.
- It is not a clean fast-forward copy of the active source branch. Symmetric
  comparison against active source commit `c5404ec` found 432 source-only and
  390 WorkBuddy-only commits, with merge base `a5bbba2`.
- No files were copied, merged, deleted, or treated as authoritative.

## Classified Artifacts

- Desktop and Obsidian contain personal reports and research notes. They are
  private reference material, excluded from public release and source imports.
- Main repo contains benchmark outputs, raw local smoke artifacts, and clean
  release trial material. They remain subject to existing privacy scan and
  `.gitignore` boundaries.
- Existing local planning, benchmark, and real-case drafts in the active repo
  remain uncommitted and were not changed by this sweep.

## Required Guard

1. Before adapter, oracle, release, or entrypoint work, read this sweep plus
   the two earlier sweep records.
2. Do not merge or copy from the WorkBuddy checkout without an explicit,
   commit-by-commit review and a separate branch.
3. Do not publish private desktop/Obsidian reports or use them as test fixtures.
