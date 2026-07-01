# Repo Cleanup And Promotion Map - 2026-07-01

## Purpose

This note turns the current fragment-governance findings into one concrete cleanup map.

It does **not** delete historical assets. It defines:

1. what should remain reference-only,
2. what should be promoted into repo truth next,
3. what must never flow back into runtime truth.

This file is for practical day-to-day use during multi-window work.

## Rule Summary

Three layers need active discipline:

1. `docs/research/local_drafts/2026-06`
2. external Gemini work-brain scratch under `/Users/wuyongnaren/.gemini/antigravity-ide/brain`
3. WorkBuddy mirror under `/Users/wuyongnaren/.workbuddy/skills/jyotish-vedic-astrology`

The repo runtime truth remains:

- `SKILL.md`
- `AGENTS.md`
- `scripts/`
- `tests/`
- `references/`
- canonical committed `docs/research/*.md`

## A. Local Drafts 2026-06

Status:

- high-value source pool
- not runtime truth
- not directly callable by workflow

Current governance source:

- [local_drafts_2026_06_disposition.md](/Users/wuyongnaren/Documents/印度占星/docs/research/local_drafts_2026_06_disposition.md)

### Promote First

These are the highest-value draft fronts to convert into canonical repo truth next:

1. `antigravity_round36_tajika_sahams_external_closure_pack_2026_06_26.md`
2. `antigravity_round37_dasha_external_oracle_shortest_closure_board_2026_06_26.md`
3. `antigravity_round37_shadbala_absolute_value_frontier_board_2026_06_26.md`
4. `antigravity_round39_yogi_wealth_bridge_audit_2026_06_28.md`
5. `three_fronts_skill_depth_audit_2026_06_26.md`
6. `current_skill_core_gap_rerank_2026_06_26.md`
7. `five_hard_fronts_master_board_2026_06_26.md`

### Promotion Targets

When promoted, they should end up in one of four canonical forms only:

- `docs/research/*.md`
- `references/*.md`
- `tests/*.py`
- `scripts/*.py`

Current promoted packs:

- [promote_first_repo_truth_pack_2026_07_01.md](/Users/wuyongnaren/Documents/印度占星/docs/research/promote_first_repo_truth_pack_2026_07_01.md)
- [promote_second_repo_truth_pack_2026_07_01.md](/Users/wuyongnaren/Documents/印度占星/docs/research/promote_second_repo_truth_pack_2026_07_01.md)
- [promote_third_repo_truth_pack_2026_07_01.md](/Users/wuyongnaren/Documents/印度占星/docs/research/promote_third_repo_truth_pack_2026_07_01.md)
- [promote_fourth_repo_truth_pack_2026_07_01.md](/Users/wuyongnaren/Documents/印度占星/docs/research/promote_fourth_repo_truth_pack_2026_07_01.md)

### Do Not Do

- do not import draft code directly into runtime
- do not cite drafts as final capability truth without re-anchoring
- do not delete the draft pack just to reduce clutter

## B. External Gemini Work-Brain

Status:

- recovery-only
- useful for archaeology
- not repo truth

Examples already flagged by preflight:

- `run_vedastro.py`
- `test_vedastro_events.py`
- `test_vedastro_network.py`
- `vedastro_capability_gap_analysis.md`

### Allowed Use

Allowed:

- compare ideas
- recover lost exploration
- re-anchor findings into repo docs or code

Not allowed:

- treat these files as current implementation truth
- link runtime imports to them
- quote them as final project status without repo confirmation

### Cleanup Action

The cleanup action here is **documentation and triage**, not repo-side deletion:

- if a work-brain artifact is still valuable, rewrite its claim into repo truth
- if it is obsolete, leave it in recovery-only status and stop re-reading it during normal implementation

## C. WorkBuddy Mirror

Status:

- distribution mirror
- historical reference only
- explicitly not runtime source-of-truth

Canonical boundary sources:

- [unique_main_chain_map_2026_07_01.md](/Users/wuyongnaren/Documents/印度占星/docs/research/unique_main_chain_map_2026_07_01.md)
- [whole_project_fragment_sweep_and_vedastro_ledger_link_2026_06_28.md](/Users/wuyongnaren/Documents/印度占星/docs/research/whole_project_fragment_sweep_and_vedastro_ledger_link_2026_06_28.md)

### Allowed Use

Allowed:

- parity check
- drift detection
- distribution packaging reference

Not allowed:

- reverse-copy runtime code into repo truth
- add mirror path to import path
- treat mirror docs as more current than the main repo

## Required Pre-Work Checklist

Before touching:

- strict workflow
- VedAstro official ingestion
- benchmark/oracle closure
- wealth/career/relationship adjudicators
- fragment reuse claims

do this:

1. check canonical repo truth first
2. check `local_drafts_2026_06_disposition.md`
3. check `preflight_fragment_scan.py` output
4. only then inspect Gemini brain or WorkBuddy mirror if the canonical layer is insufficient

## Current Best Cleanup Strategy

This is the shortest safe path:

1. keep runtime code untouched unless a real gap is proven
2. keep drafts in place but promote the top-value seven items above
3. keep Gemini work-brain strictly as recovery-only
4. keep WorkBuddy strictly as mirror/reference-only
5. enforce the boundary through tests and preflight output, not by memory

## Boundary

This cleanup map exists to reduce repeated rediscovery cost.

It does **not** mean:

- local drafts are garbage
- external work-brain is useless
- WorkBuddy mirror should be deleted

It means all three must stay outside runtime truth until explicitly re-anchored.
