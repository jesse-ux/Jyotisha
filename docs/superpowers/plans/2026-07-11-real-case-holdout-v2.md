# Real-Case Holdout V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add ten new research-grade holdout cases, compare frozen v1/v2 Jyotish replay logic across twenty cases, and promote only improvements that generalize to holdout data.

**Architecture:** Keep batch 1 immutable as discovery/training evidence. Store batch 2 separately, run both rule versions through one benchmark runner, and generate batch/combined comparison reports. Production orchestration receives only the promoted rule version plus explicit external-oracle and specificity boundaries.

**Tech Stack:** Python 3, Swiss Ephemeris-backed local CLI, JSON manifests/schemas, pytest, public Astro-Databank and independently sourced event records.

## Global Constraints

- Batch 2 must contain ten new people: five career events and five legal marriages.
- Birth time must be Rodden A or AA; event date must have primary or verified-secondary source.
- Freeze v2 before observing batch-2 results.
- V2 additions: node dispositor, D10/D9 Lagna-lord and domain-house lord, A10/UL lord, Amatyakaraka/Darakaraka, and annual-layer audit when available.
- Do not change score thresholds after batch-2 results.
- No user birth data or private conversation feedback.
- No scientific accuracy claim without sourced negative controls.

### Task 1: Freeze V2 Contract

**Files:**
- Modify: `tests/test_public_real_case_benchmark.py`
- Modify: `scripts/public_real_case_benchmark.py`

- [ ] Add failing tests for explicit `v1` and `v2` rule versions.
- [ ] Add deterministic v2 signal helpers and preserve v1 output.
- [ ] Verify v1 batch-1 results remain unchanged.

### Task 2: Add Holdout Manifest

**Files:**
- Create: `references/real_case_calibration/replay_manifest_holdout_v2.json`
- Modify: `tests/test_real_case_replay_validator.py`

- [ ] Add failing validation test for ten new A/AA cases and 5/5 domain split.
- [ ] Research and import birth/event sources.
- [ ] Validate no person overlaps batch 1.

### Task 3: Run V1/V2 Holdout Comparison

**Files:**
- Modify: `scripts/public_real_case_benchmark.py`
- Create: `docs/benchmark/public_real_case_holdout_v2_2026_07_11.json`

- [ ] Add batch comparison summary and rule-promotion decision.
- [ ] Run v1 and frozen v2 on batch 2.
- [ ] Run combined twenty-case summary.
- [ ] Promote v2 only if holdout recall/exact-label improve without more blocked cases.

### Task 4: Integrate and Document

**Files:**
- Modify: `scripts/unified_consultation_orchestrator.py`
- Create: `docs/research/public_real_case_20_case_closure_2026_07_11.md`
- Modify: `docs/research/pre_work_error_ledger.md`

- [ ] Expose promoted benchmark summary and remaining gaps.
- [ ] Document misses, conflicts, external-engine states, and next negative-control design.
- [ ] Run focused tests, privacy scan, diff check, and pre-work gate.
