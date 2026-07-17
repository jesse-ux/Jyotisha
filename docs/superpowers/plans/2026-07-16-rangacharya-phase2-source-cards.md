# Rangacharya Phase 2 Source Cards Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add formula-level source cards and wire Rangacharya runtime to them, so no screenshot/archive rule can be silently promoted into calculation or adjudication.

**Architecture:** Keep `references/rangacharya_source_manifest.json` as source inventory. Add `references/rangacharya_source_cards.json` as formula inventory. `scripts/rangacharya.py` loads cards and attaches card/status/blocker metadata to every experimental output.

**Tech Stack:** Python 3 stdlib JSON, existing `scripts/rangacharya.py`, pytest.

## Tasks

### Task 1: Source Card Tests

**Files:**
- Create `tests/test_rangacharya_source_cards.py`
- Create `references/rangacharya_source_cards.json`

- [ ] Write tests requiring schema, no secrets, no adjudication, and card ids for Phase 2 rule groups.
- [ ] Run tests and verify missing-card failure.
- [ ] Add minimal cards for core Arudha, Active/Effective Lagna, Sanmukha/Prakriti, special mappings, named yogas, UL family rules, and future article tracks.
- [ ] Run tests and verify pass.

### Task 2: Runtime Card Loader

**Files:**
- Modify `scripts/rangacharya.py`
- Modify `tests/test_rangacharya_variant.py`

- [ ] Write tests requiring outputs to include `source_card_id`, `source_card_status`, and `blocked_reason` when not verified.
- [ ] Implement JSON loader with safe fallback.
- [ ] Attach card metadata to AL/A7/A10/UL, active lagna, and effective lagna.
- [ ] Run focused tests.

### Task 3: Planning Sync And Verification

**Files:**
- Modify `.planning/rangacharya_vedastro_design_20260716/task_plan.md`
- Modify `.planning/rangacharya_vedastro_design_20260716/progress.md`

- [ ] Record Phase 2 source-card completion.
- [ ] Run focused Rangacharya tests.
- [ ] Run mandatory pre-work check.
- [ ] Run secret scan.
