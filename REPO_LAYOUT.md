# Repository Layout

This repository mixes product code, astrology research, oracle artifacts, and local experimentation. To keep the worktree usable, follow these layout rules.

## Core Areas

- `/Users/wuyongnaren/Documents/印度占星/mcp_server.py`
  - adjudicator-facing MCP entrypoint
- `/Users/wuyongnaren/Documents/印度占星/scripts/`
  - reusable project code and maintained tooling
- `/Users/wuyongnaren/Documents/印度占星/tests/`
  - maintained regression and contract tests
- `/Users/wuyongnaren/Documents/印度占星/references/`
  - durable knowledge assets, oracle cases, and frozen methodology

## Research

- `/Users/wuyongnaren/Documents/印度占星/docs/research/`
  - active research and current audits
- `/Users/wuyongnaren/Documents/印度占星/docs/research/archive/`
  - historical round notes and local draft research

## Local Scratch

- `/Users/wuyongnaren/Documents/印度占星/scratch/local/scripts/`
  - one-off debugging scripts, temporary probes, ad hoc runners
- `/Users/wuyongnaren/Documents/印度占星/scratch/local/outputs/`
  - local generated JSON, text dumps, temporary reports

These paths are local-only and ignored by git.

## Local Runtime Noise

The following should stay out of normal versioned work:

- `/Users/wuyongnaren/Documents/印度占星/.agents/`
- `/Users/wuyongnaren/Documents/印度占星/venv_vedastro/`
- `/Users/wuyongnaren/Documents/印度占星/scratch/local/`

## Practical Rule

Before adding a new file, decide which lifecycle it belongs to:

1. reusable project asset
2. active research note
3. archived research
4. local scratch script
5. local generated output

If it is category 4 or 5, do not leave it in the repo root.
