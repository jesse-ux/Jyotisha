# Prashna Remedies Unified Entry Implementation Plan
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
**Goal:** Reuse existing `prashna` and `remedies` modules inside the unified consultation workflow so web/API/skill can expose three parallel entry modes: direct chart, rectification, and time-question (Prashna).
**Architecture:** Keep the current `execute_consultation_workflow()` and `UnifiedConsultationOrchestrator` as the single runtime planner. Add one new `entry_mode` (`prashna`) and one gate-fed remedies path that consumes `strict_audit_gate`/guided-topic conclusion packets instead of raw free-form frontend fields. Frontend only switches entry payload shape and display mode; backend remains the source of truth.
**Tech Stack:** Python stdlib, existing repo modules (`prashna.py`, `remedies.py`, `unified_consultation_orchestrator.py`, `jyotish_api_server.py`), existing web app JS/HTML, pytest.

## Global Constraints
- Reuse existing modules; no new subsystem.
- Keep source priority: VedAstro official snapshot first, local supplemental second, fallback last.
- Remedies must not accept arbitrary raw advice inputs from frontend once unified path exists.
- Frontend must expose exactly three peer entry modes: `direct_chart`, `rectification`, `prashna`.
- Keep diffs small and local to existing orchestrator/API/frontend files.

### Task 1: Add `prashna` to unified runtime planner
**Files:**
- Modify: `scripts/unified_consultation_orchestrator.py`
- Test: `tests/test_unified_consultation_orchestrator.py`
**Interfaces:**
- Consumes: `entry_mode: str`, `question: str | None`, existing route/theme normalization.
- Produces: runtime planner contract supporting `entry_mode == "prashna"` and route/theme selection for Prashna.
- [ ] **Step 1: Write failing tests**
- [ ] **Step 2: Run planner tests to verify failure**
- [ ] **Step 3: Implement minimal planner support for `prashna`**
- [ ] **Step 4: Re-run planner tests**

### Task 2: Route consultation workflow through Prashna entry mode
**Files:**
- Modify: `scripts/jyotish_api_server.py`
- Test: `tests/test_api_server_security.py`
**Interfaces:**
- Consumes: `POST /api/consultation_workflow` payload w/ `entry_mode = "prashna"`, `question`, `question_text`, optional `horary_number`, existing birth/location/time fields.
- Produces: consultation workflow result containing `entry_mode`, `runtime_planner`, `prashna` result block, and shared provenance fields.
- [ ] **Step 1: Write failing API workflow tests for `prashna` entry**
- [ ] **Step 2: Run targeted tests to verify failure**
- [ ] **Step 3: Implement minimal `prashna` entry path by reusing `_compute_prashna()`**
- [ ] **Step 4: Re-run targeted tests**

### Task 3: Make unified remedies consume strict gate output only
**Files:**
- Modify: `scripts/jyotish_api_server.py`
- Test: `tests/test_api_server_security.py`
**Interfaces:**
- Consumes: guided-topic / strict workflow conclusion packet containing `strict_audit_gate`, `topic`, `supporting_planets`, `active_dasha_lord`, and strength inputs already computed in workflow.
- Produces: remedies response derived from audited conclusion context, not arbitrary frontend-entered `shadbala`/`doshas` blobs in unified mode.
- [ ] **Step 1: Write failing test showing unified remedies path rejects missing gate context**
- [ ] **Step 2: Run targeted test to verify failure**
- [ ] **Step 3: Implement minimal audited remedies adapter around existing `recommend_remedies()`**
- [ ] **Step 4: Re-run targeted tests**

### Task 4: Expose three entry modes in frontend
**Files:**
- Modify: `jyotish-app/index.html`
- Modify: `jyotish-app/main.js`
- Modify: `jyotish-app/api-bridge.js`
- Test: `tests/test_frontend_productization.py`
**Interfaces:**
- Consumes: user choice among `direct_chart`, `rectification`, `prashna`.
- Produces: frontend payloads to `/api/consultation_workflow`, plus Prashna-specific question fields when `prashna` selected.
- [ ] **Step 1: Write failing frontend contract test for 3 entry modes**
- [ ] **Step 2: Run targeted frontend test to verify failure**
- [ ] **Step 3: Implement minimal UI/payload switch reuse of existing sections**
- [ ] **Step 4: Re-run targeted frontend tests**

### Task 5: Wire remedies display to unified audited output
**Files:**
- Modify: `jyotish-app/main.js`
- Test: `tests/test_frontend_productization.py`
**Interfaces:**
- Consumes: unified workflow response including audited remedies packet.
- Produces: remedies section rendered from audited packet, not standalone free-form request flow.
- [ ] **Step 1: Write failing render test**
- [ ] **Step 2: Run targeted test to verify failure**
- [ ] **Step 3: Implement minimal audited remedies rendering**
- [ ] **Step 4: Re-run targeted tests**

### Task 6: End-to-end verification
**Files:**
- Modify if needed: `tests/test_api_server_security.py`, `tests/test_frontend_productization.py`
**Interfaces:**
- Produces: passing targeted regression coverage for planner, API workflow, remedies gate, and frontend entry modes.
- [ ] **Step 1: Run targeted backend tests**
- [ ] **Step 2: Run targeted frontend tests**
- [ ] **Step 3: Run one live local consultation/prashna smoke probe**
- [ ] **Step 4: Record any remaining boundary explicitly**
