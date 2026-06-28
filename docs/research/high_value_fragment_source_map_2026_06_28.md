# High-Value Fragment Source Map - 2026-06-28

## Goal

Prevent high-value Jyotish research, bridge notes, audits, and implementation clues from remaining scattered across multiple work surfaces and getting lost during multi-window work.

This document defines which locations are authoritative, which are draft-only, and which are recovery surfaces that must be reviewed before major strict-workflow or adjudicator changes.

## Why This File Exists

Recent carpet-level discovery showed that meaningful Jyotish materials are currently distributed across four separate layers:

1. the main repository
2. local draft folders inside the repository
3. external work-brain locations such as Gemini/Codex attachments
4. synced distribution copies such as WorkBuddy skill mirrors

Without an explicit source hierarchy, valuable materials can be:

- forgotten entirely
- reused from the wrong layer
- copied backward from distribution mirrors
- duplicated in new docs while older drafts remain invisible

## Authority Tiers

### 1. Main Repo Truth

These are the only sources allowed to define current product truth by default:

- `/Users/wuyongnaren/Documents/印度占星/SKILL.md`
- `/Users/wuyongnaren/Documents/印度占星/AGENTS.md`
- `/Users/wuyongnaren/Documents/印度占星/references/`
- `/Users/wuyongnaren/Documents/印度占星/scripts/`
- `/Users/wuyongnaren/Documents/印度占星/tests/`
- `/Users/wuyongnaren/Documents/印度占星/docs/research/` (committed reports only)
- `/Users/wuyongnaren/Documents/印度占星/docs/superpowers/specs/`
- `/Users/wuyongnaren/Documents/印度占星/docs/superpowers/plans/`

Rule:

- This is the only layer allowed to declare current engine behavior, workflow boundaries, benchmark status, and implementation truth.

### 2. Repo Local Drafts

These are high-value but non-authoritative draft materials inside the repo:

- `/Users/wuyongnaren/Documents/印度占星/docs/research/local_drafts/2026-06/`
- `/Users/wuyongnaren/Documents/印度占星/scratch/local/`

Rule:

- These files may contain valuable design work, audits, and batch notes.
- They must be reviewed before adjacent feature work.
- They do not become truth until promoted into committed research docs, references, tests, or code.

### 3. External Work Brain

These are high-signal recovery surfaces outside the repo:

- `/Users/wuyongnaren/.gemini/antigravity-ide/brain/`
- `/Users/wuyongnaren/.codex/attachments/`

Observed high-value examples include:

- `vedastro_capability_gap_analysis.md`
- `skill_deep_audit_report.md`
- multiple `task.md`, `walkthrough.md`, and `implementation_plan.md` files
- scratch VedAstro exploration scripts and dumps

Rule:

- These files are not authoritative.
- They must be treated as recovery, archaeology, and comparison inputs.
- Any claim or design found here must be re-anchored in repo truth before it can guide implementation.

### 4. Synced Distribution Copy

These are mirrored deployment/sync targets:

- `/Users/wuyongnaren/.workbuddy/skills/jyotish-vedic-astrology`

Rule:

- This layer is distribution output, not source-of-truth input.
- It may be scanned to detect drift.
- It must never be reverse-copied over the main repository.

## Highest-Value Orphaned Assets Identified

### A. Repo-Local Draft Packs

Most important current draft cluster:

- `/Users/wuyongnaren/Documents/印度占星/docs/research/local_drafts/2026-06/`

Especially notable:

- `antigravity_round39_yogi_wealth_bridge_audit_2026_06_28.md`
- `antigravity_round36_tajika_sahams_external_closure_pack_2026_06_26.md`
- `antigravity_round36_rtn_anomalous_d9_deepening_pack_2026_06_26.md`
- `antigravity_round37_public_benchmark_moat_board_2026_06_26.md`
- `three_fronts_skill_depth_audit_2026_06_26.md`
- `recovered_old_skill_reuse_audit_2026_06_26.md`

Value:

- These are likely the richest underused repo-local fragment set.
- They should be checked before new work on Yogi, Tajika/Sahams, RTN/D9, and benchmark positioning.

### B. Gemini Brain Recovery Notes

Observed high-value items:

- `/Users/wuyongnaren/.gemini/antigravity-ide/brain/c4e5264f-9865-4c70-93be-14776faa339e/vedastro_capability_gap_analysis.md`
- `/Users/wuyongnaren/.gemini/antigravity-ide/brain/f6d8f2e4-10d0-45ab-809a-edf24dd7285e/skill_deep_audit_report.md`
- `/Users/wuyongnaren/.gemini/antigravity-ide/brain/f6d8f2e4-10d0-45ab-809a-edf24dd7285e/vedastro_raw_reading.md`
- task/walkthrough/implementation files across multiple brain session directories

Value:

- These contain capability audits, raw readings, and implementation reasoning that may not yet have been promoted into repo docs.

### C. Distribution-Mirror Drift Checks

Observed high-value WorkBuddy mirror paths:

- `/Users/wuyongnaren/.workbuddy/skills/jyotish-vedic-astrology/references/quick-reference-guide.md`
- `/Users/wuyongnaren/.workbuddy/skills/jyotish-vedic-astrology/references/yogi-avayogi-system.md`
- `/Users/wuyongnaren/.workbuddy/skills/jyotish-vedic-astrology/references/verified-patterns-marriage-timing-v6.md`
- `/Users/wuyongnaren/.workbuddy/skills/jyotish-vedic-astrology/tests/test_knrao_benchmark_v6910.py`

Value:

- Good for parity checks.
- Not valid as a source layer for implementation decisions unless matched back to repo truth.

### D. Pending Oracle Packets

High-value unresolved asset pool:

- `/Users/wuyongnaren/Documents/印度占星/references/oracle/artifacts/pending_packets/`
- `/Users/wuyongnaren/Documents/印度占星/references/oracle/cases/`

Value:

- These are not random leftovers.
- They are active closure assets for Dasha, Shadbala, Tajika/Sahams, and historical edge cases.

## Required Pre-Work Scan Rule

Before touching any of the following:

- strict workflow logic
- adjudicator logic
- external oracle bridges
- benchmark claims
- skill truth or sync behavior

scan these layers in order:

1. main repo truth
2. repo local drafts
3. Gemini/Codex external work brain
4. WorkBuddy distribution copy

Then explicitly decide one of three outcomes:

- `no relevant fragment found`
- `relevant fragment found but remains draft/reference only`
- `relevant fragment found and should be promoted into repo truth`

## Promotion Rule

If a fragment is valuable enough to affect product behavior, planning, or benchmark claims, it must be promoted into one of these repo-truth forms:

- committed research doc under `docs/research/`
- reference doc under `references/`
- regression test under `tests/`
- implementation code under `scripts/` or `mcp_server.py`

It must not remain only in:

- Gemini brain
- Codex attachments
- WorkBuddy copy
- local draft folders

## Adjacent Current Fronts Most Likely To Need Fragment Recovery

1. `dignity_guardrail` and later `functional_role_guardrail`
2. VedAstro range-scan MVP hardening
3. Tajika/Sahams annual closure
4. RTN / high-order D9 / deep varga bridges
5. public benchmark and oracle closure reporting

## Working Reminder

This file is not a backlog. It is a source-discipline rule.

The main purpose is simple:

- stop losing high-value work across windows
- stop re-deriving what already exists in a hidden fragment
- stop accidentally treating mirrors and drafts as canonical truth
