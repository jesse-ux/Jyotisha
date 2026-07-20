# Repository Layout

This repository mixes product code, astrology research, oracle artifacts, and local experimentation. To keep the worktree usable, follow these layout rules.

## Core Areas

- `<repo>/frontend/`
  - current Next.js production web application
- `<repo>/deploy/`
  - production container topology and operational source of truth; start with `deploy/README.md`
- `<repo>/mcp_server.py`
  - adjudicator-facing MCP entrypoint
- `<repo>/scripts/`
  - reusable project code and maintained tooling
- `<repo>/tests/`
  - maintained regression and contract tests
- `<repo>/references/`
  - durable knowledge assets, oracle cases, and frozen methodology

## Research

- `<repo>/docs/research/`
  - active research and current audits
- `<repo>/docs/research/archive/`
  - historical round notes and local draft research

## Historical Working Logs

- `<repo>/task_plan.md`
- `<repo>/findings.md`
- `<repo>/progress.md`

These root files preserve earlier implementation history and may mention retired
paths or commands. They are not runtime or deployment instructions. Use
`README.md` for current local development and `deploy/README.md` for production.

## Local Scratch

- `<repo>/scratch/local/scripts/`
  - one-off debugging scripts, temporary probes, ad hoc runners
- `<repo>/scratch/local/outputs/`
  - local generated JSON, text dumps, temporary reports

These paths are local-only and ignored by git.

## Local Runtime Noise

The following should stay out of normal versioned work:

- `<repo>/.agents/`
- `<repo>/venv_vedastro/`
- `<repo>/scratch/local/`

## Practical Rule

Before adding a new file, decide which lifecycle it belongs to:

1. reusable project asset
2. active research note
3. archived research
4. local scratch script
5. local generated output

If it is category 4 or 5, do not leave it in the repo root.
