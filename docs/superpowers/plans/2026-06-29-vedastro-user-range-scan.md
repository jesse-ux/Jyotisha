# VedAstro User Range Scan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose VedAstro range scan as an ordinary user action in the web app.

**Architecture:** Reuse the existing `vedastro_service_adapter` as the only network boundary. The API validates user chart/date/domain inputs and returns the adapter result shape. The frontend displays blocked/live results in Trust Center and attaches the latest result to `chartData.modules.vedastro_range_scan_result`.

**Tech Stack:** Python stdlib HTTP server, existing JS API bridge, existing Trust Center/provenance UI.

## Global Constraints

- Default CI must not require network.
- Do not leak full VedAstro endpoint paths or API keys to the frontend.
- VedAstro evidence remains secondary external timing evidence.
- Use TDD: failing test first, then minimal implementation.

---

### Task 1: API Route

**Files:**
- Modify: `scripts/vedastro_service_adapter.py`
- Modify: `scripts/jyotish_api_server.py`
- Test: `tests/test_api_server_security.py`

**Interfaces:**
- Consumes: `vedastro_service_adapter.run_range_scan_for_case(case, domain, start_date, end_date, case_id='user_chart')`
- Produces: `POST /api/vedastro/range_scan`

- [ ] Write failing route test.
- [ ] Add adapter helper for user birth case.
- [ ] Add API route and validation.
- [ ] Run focused API test.

### Task 2: Frontend User Panel

**Files:**
- Modify: `jyotish-app/api-bridge.js`
- Modify: `jyotish-app/public/api-bridge.js`
- Modify: `jyotish-app/main.js`
- Test: `tests/test_frontend_productization.py`

**Interfaces:**
- Consumes: `window.JyotishAPI.runVedAstroRangeScan(payload)`
- Produces: `renderVedAstroUserScanPanel`, `runVedAstroRangeScanFromPanel`

- [ ] Write failing static frontend test.
- [ ] Add bridge function.
- [ ] Add Trust Center scan panel and action handler.
- [ ] Attach latest result to `chartData.modules.vedastro_range_scan_result`.
- [ ] Run focused frontend test and build.

### Task 3: Verification And Records

**Files:**
- Modify: `task_plan.md`
- Modify: `progress.md`
- Modify: `findings.md`

- [ ] Run VedAstro/API/frontend focused tests.
- [ ] Run quick quality gate.
- [ ] Update project records with product boundary.
