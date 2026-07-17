# Shadbala High-Rigor Migration Implementation Plan
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Port the reviewed `f3bae51` Shadbala component-formula correction and its public high-rigor parity evidence from research to the commercial backend without importing research worktree residue.

**Architecture:** Use the committed research tree at `f3bae51` as the only source. First add the precise-context regression to commercial and observe failure; then port the smallest calculation/API/engine changes needed for it. Public Steve Jobs artifacts and the parity manifest move only after privacy and hash checks.

**Tech Stack:** Python 3, pytest, existing Swiss Ephemeris/Jyotish engine, JSON evidence manifests.

### Task 1: Port formula regression first

**Files:**
- Create: `tests/test_shadbala_precise_context.py`
- Modify: `scripts/shadbala.py`
- Modify: `scripts/jyotish_engine.py`
- Modify: `scripts/jyotish_api_server.py`

- [ ] Copy the committed regression test from `f3bae51`; run it in commercial and observe failure.
- [ ] Diff the source commit against its parent, then port only paths exercised by the failing test.
- [ ] Run the precise-context test plus existing Shadbala tests.

### Task 2: Port public high-rigor evidence

**Files:**
- Create: `references/oracle/artifacts/jyotishganit_steve_jobs_high_rigor_raw.json`
- Create: `references/oracle/artifacts/local_steve_jobs_high_rigor_raw.json`
- Modify: `references/oracle/three_engine_parity_replay_manifest.json`

- [ ] Verify artifacts have no secret/private input and are referenced by the committed parity manifest.
- [ ] Copy exact committed public files, then run parity artifact-contract and replay-validator tests.

### Task 3: Verify and publish

**Files:**
- Modify: `references/evidence_manifests/commercial_external_validation_release.v1.json` when public evidence is added to release scope

- [ ] Run focused Shadbala, parity, API, privacy, and release-hash gates.
- [ ] Commit only reviewed migration files and push `codex/cross-project-contract`.
