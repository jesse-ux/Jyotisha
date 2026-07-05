# Open Source P0 File Execution Plan
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
**Goal:** Finish the three P0 open-source integration fronts with the smallest real diff: `panchanga_api` sidecar integration, VedAstro official-default closure, and PyJHora black-box evidence consumption.
**Architecture:** Reuse the existing unified planner, API server, MCP strict workflow, local `muhurta/prashna/remedies` modules, and existing VedAstro/PyJHora audit scripts. Do not add a parallel runtime chain. Extend existing payloads so web, MCP, and skill all read the same contract.
**Tech Stack:** Python 3.11 stdlib, existing `scripts/` modules, existing `jyotish-app` frontend, pytest, existing repo docs.

## Global Constraints
- Reuse existing repo modules; no new subsystem.
- Keep authority order: VedAstro official snapshot first, local supplemental modules second, local fallback last.
- `PyJHora` remains black-box evidence only; do not import/copy AGPL code.
- `panchanga_api` ideas may shape sidecar outputs, but local computation stays in `scripts/muhurta.py`, `scripts/prashna.py`, `scripts/remedies.py`.
- Keep diffs tight: prefer helper functions inside current files over new files.
- Every task ends with targeted tests, not hand-waving.

## File Map

### P0-A: `panchanga_api`-style sidecar integration

| File | Role |
|---|---|
| `scripts/unified_consultation_orchestrator.py` | Decide when workflow should run `prashna`, `muhurta/panchanga`, and audited remedies sidecars. |
| `scripts/jyotish_api_server.py` | Build/attach `prashna`, `muhurta_panchanga`, and `audited_remedies` packets in one workflow response. |
| `scripts/muhurta.py` | Existing local Panchanga/Muhurta engine. Expose one compact helper fit for API/strict workflow payloads. |
| `scripts/prashna.py` | Existing time-question engine. Reuse, do not rebuild. |
| `scripts/remedies.py` | Existing remedies engine; only fed audited gate outputs. |
| `mcp_server.py` | Surface same sidecars in strict workflow output. |
| `jyotish-app/index.html` | Existing three-entry UI shell. Only minor control copy/visibility changes if needed. |
| `jyotish-app/main.js` | Send timing-sidecar inputs and render sidecar outputs. |
| `jyotish-app/renderers.js` | Reuse existing Panchanga rendering slot instead of new UI surface. |
| `tests/test_unified_consultation_orchestrator.py` | Planner contract tests. |
| `tests/test_api_server_security.py` | Workflow contract tests. |
| `tests/test_muhurta.py` | Compact Muhurta helper tests. |
| `tests/test_frontend_productization.py` | Frontend contract/render tests. |

### P0-B: VedAstro official-default closure

| File | Role |
|---|---|
| `scripts/vedastro_service_adapter.py` | Single official network boundary. Cache/queue/free-tier behavior lives here first. |
| `scripts/vedastro_priority.py` | Shared official-first source-priority contract. |
| `scripts/diagnose_vedastro_mode.py` | Runtime diagnosis for `official_extended` vs fallback, free-tier eligibility, queue/cache state. |
| `scripts/jyotish_api_server.py` | Attach official summary/runtime truth to chart/full-reading/thematic/workflow responses. |
| `scripts/unified_consultation_orchestrator.py` | Planner-visible official-step intent only; no extra engine. |
| `mcp_server.py` | Surface same runtime truth and official execution layer summary. |
| `jyotish-app/api-bridge.js` | Preserve official/runtime truth fields from API. |
| `jyotish-app/main.js` | Render compact source-priority/runtime-truth block. |
| `jyotish-app/professional-reading.js` | Show official/partial/fallback boundary in final reading. |
| `jyotish-app/ai-chat.js` | Carry official evidence snapshot/runtime truth into follow-up payload. |
| `tests/test_vedastro_runtime_mode_diagnostics.py` | Diagnose contract. |
| `tests/test_vedastro_official_full_snapshot.py` | Snapshot contract. |
| `tests/test_vedastro_service_adapter_executor.py` | Adapter execution/caching behavior. |
| `tests/test_api_server_security.py` | Response contract propagation. |
| `tests/test_frontend_productization.py` | Frontend visibility contract. |
| `tests/test_vedastro_official_mcp_bridge.py` | Official bridge smoke. |

### P0-C: PyJHora black-box evidence consumption

| File | Role |
|---|---|
| `scripts/generate_pyjhora_oracle_artifact_manifest.py` | Canonical artifact manifest generator. |
| `scripts/oracle_benchmark_inventory.py` | Make PyJHora artifact counts/queryable fronts visible. |
| `scripts/external_oracle_sanity_closure.py` | Summarize PyJHora evidence availability into closure report. |
| `scripts/historical_event_backtest.py` | Attach matching external evidence refs into backtest output. |
| `scripts/oracle_closure_master_dashboard.py` | Lift PyJHora evidence readiness into one master board. |
| `README.md` | State black-box boundary and what counts as closed vs not closed. |
| `tests/test_pyjhora_oracle_artifact_manifest.py` | Manifest shape tests. |
| `tests/test_oracle_benchmark_inventory.py` | Inventory tests. |
| `tests/test_external_oracle_sanity_closure.py` | Closure summary tests. |
| `tests/test_historical_event_backtest.py` | Backtest evidence-link tests. |
| `tests/test_oracle_closure_master_dashboard.py` | Master dashboard tests. |

## Task 1: Add `muhurta_panchanga` sidecar to unified workflow
**Files:**
- Modify: `scripts/muhurta.py`
- Modify: `scripts/unified_consultation_orchestrator.py`
- Modify: `scripts/jyotish_api_server.py`
- Test: `tests/test_muhurta.py`
- Test: `tests/test_unified_consultation_orchestrator.py`
- Test: `tests/test_api_server_security.py`

**Interfaces:**
- Consumes: existing birth/location/time payload, optional `reference_date`, optional user question/topic.
- Produces: `muhurta_panchanga: {status, source, panchanga, muhurta_windows, remedy_timing, blocked_reason?}` in workflow/module payload.

- [ ] **Step 1: Write failing helper test in `tests/test_muhurta.py`**
  - Target a new compact helper in `scripts/muhurta.py`, e.g. `build_muhurta_sidecar(...)`.
- [ ] **Step 2: Run targeted test to verify failure**
  - Run: `python3 -m pytest tests/test_muhurta.py -q`
- [ ] **Step 3: Write failing planner/API tests**
  - `tests/test_unified_consultation_orchestrator.py`: planner adds `run_muhurta_panchanga` for timing/remedy/prashna routes.
  - `tests/test_api_server_security.py`: workflow response includes `muhurta_panchanga`.
- [ ] **Step 4: Run targeted planner/API tests**
- [ ] **Step 5: Implement minimal helper in `scripts/muhurta.py`**
  - Reuse current Panchanga/Muhurta math.
  - Return compact summary only; no giant raw blob.
- [ ] **Step 6: Thread helper into `scripts/jyotish_api_server.py`**
  - Add one private helper, e.g. `_compute_muhurta_panchanga(...)`.
  - Attach result to consultation workflow and high-rigor/full-reading payloads where timing/remedies are relevant.
- [ ] **Step 7: Update planner in `scripts/unified_consultation_orchestrator.py`**
  - Add `run_muhurta_panchanga` only when route needs timing/remedy support.
- [ ] **Step 8: Re-run targeted tests**

## Task 2: Surface timing sidecar in MCP and frontend
**Files:**
- Modify: `mcp_server.py`
- Modify: `jyotish-app/main.js`
- Modify: `jyotish-app/renderers.js`
- Modify: `jyotish-app/index.html` only if an existing slot/label is missing
- Test: `tests/test_frontend_productization.py`

**Interfaces:**
- Consumes: workflow payload with `muhurta_panchanga`, `prashna`, `audited_remedies`.
- Produces: visible timing/remedy panel in frontend + strict workflow payload exposure in MCP.

- [ ] **Step 1: Write failing frontend/MCP contract test**
  - Assert payload/rendering can see `muhurta_panchanga`.
- [ ] **Step 2: Run targeted tests to verify failure**
- [ ] **Step 3: Thread `muhurta_panchanga` through `mcp_server.py` strict output**
- [ ] **Step 4: Reuse existing Panchanga render path in `jyotish-app/renderers.js`**
  - No new tab unless current UI truly has nowhere to show it.
- [ ] **Step 5: Update `jyotish-app/main.js` to render sidecar from unified workflow response**
- [ ] **Step 6: Re-run targeted tests**

## Task 3: Make VedAstro official path the real default contract
**Files:**
- Modify: `scripts/vedastro_service_adapter.py`
- Modify: `scripts/vedastro_priority.py`
- Modify: `scripts/diagnose_vedastro_mode.py`
- Modify: `scripts/jyotish_api_server.py`
- Test: `tests/test_vedastro_runtime_mode_diagnostics.py`
- Test: `tests/test_vedastro_service_adapter_executor.py`
- Test: `tests/test_vedastro_official_full_snapshot.py`
- Test: `tests/test_api_server_security.py`

**Interfaces:**
- Consumes: same birth payload/reference date/theme, existing env/free-tier settings, adapter cache/queue config.
- Produces: one normalized block:
  - `runtime_truth`
  - `official_execution_layers`
  - `source_priority`
  - `free_tier_strategy`

- [ ] **Step 1: Write/extend failing diagnostics tests**
  - Missing premium key should not masquerade as universal blocker.
  - Free-tier cache/queue possibility should be explicit.
- [ ] **Step 2: Run diagnostics tests to verify failure**
- [ ] **Step 3: Write/extend failing adapter/API tests**
  - Repeated same request should show cache-hit semantics.
  - Official snapshot status should flow as `ok/partial/blocked`, not disappear.
- [ ] **Step 4: Run targeted adapter/API tests**
- [ ] **Step 5: Tighten `scripts/vedastro_service_adapter.py`**
  - Reuse existing cache + queue path.
  - Expose explicit metadata, not hidden internal state.
- [ ] **Step 6: Tighten `scripts/vedastro_priority.py`**
  - Keep one source-priority truth used by API/MCP/frontend.
- [ ] **Step 7: Thread normalized blocks through `scripts/jyotish_api_server.py`**
  - `/api/chart`
  - `/api/full-reading`
  - `/api/thematic_report`
  - `/api/consultation_workflow`
- [ ] **Step 8: Re-run targeted tests**

## Task 4: Show VedAstro official/fallback truth in MCP + frontend
**Files:**
- Modify: `mcp_server.py`
- Modify: `jyotish-app/api-bridge.js`
- Modify: `jyotish-app/main.js`
- Modify: `jyotish-app/professional-reading.js`
- Modify: `jyotish-app/ai-chat.js`
- Test: `tests/test_frontend_productization.py`
- Test: `tests/test_vedastro_official_mcp_bridge.py`

**Interfaces:**
- Consumes: API payload with `runtime_truth`, `official_execution_layers`, `source_priority`.
- Produces: user-visible compact truth block and AI follow-up payload carrying same boundary.

- [ ] **Step 1: Write failing frontend contract tests**
  - Assert frontend preserves and renders runtime-truth/source-priority data.
- [ ] **Step 2: Run targeted tests to verify failure**
- [ ] **Step 3: Thread fields via `jyotish-app/api-bridge.js`**
- [ ] **Step 4: Render concise truth block in `jyotish-app/main.js` / `professional-reading.js`**
  - Show direct facts: official `ok/partial/blocked`, cache hit, queue used, fallback used or not.
- [ ] **Step 5: Pass same block into `jyotish-app/ai-chat.js` follow-up payload**
- [ ] **Step 6: Surface same summary in `mcp_server.py` strict workflow output**
- [ ] **Step 7: Re-run targeted tests**

## Task 5: Normalize PyJHora artifact manifest for downstream consumers
**Files:**
- Modify: `scripts/generate_pyjhora_oracle_artifact_manifest.py`
- Modify: `scripts/oracle_benchmark_inventory.py`
- Modify: `scripts/external_oracle_sanity_closure.py`
- Test: `tests/test_pyjhora_oracle_artifact_manifest.py`
- Test: `tests/test_oracle_benchmark_inventory.py`
- Test: `tests/test_external_oracle_sanity_closure.py`

**Interfaces:**
- Consumes: `references/oracle/artifacts/pyjhora_*` + `pending_packets/*pyjhora*.json`.
- Produces: consistent per-front summary (`dasha`, `shadbala`, `tajika_sahams`) for audit scripts.

- [ ] **Step 1: Write failing manifest/inventory tests**
  - Need front-wise counts + file refs + boundary text.
- [ ] **Step 2: Run targeted tests to verify failure**
- [ ] **Step 3: Extend `generate_pyjhora_oracle_artifact_manifest.py` minimally**
  - Add any missing fields needed by inventory/closure consumers.
- [ ] **Step 4: Update `oracle_benchmark_inventory.py` to consume manifest, not ad hoc file scanning**
- [ ] **Step 5: Update `external_oracle_sanity_closure.py` to report PyJHora evidence availability explicitly**
- [ ] **Step 6: Re-run targeted tests**

## Task 6: Feed PyJHora evidence into backtest + master dashboard
**Files:**
- Modify: `scripts/historical_event_backtest.py`
- Modify: `scripts/oracle_closure_master_dashboard.py`
- Modify: `README.md`
- Test: `tests/test_historical_event_backtest.py`
- Test: `tests/test_oracle_closure_master_dashboard.py`

**Interfaces:**
- Consumes: normalized PyJHora manifest/inventory summary.
- Produces:
  - backtest result includes matching `external_evidence_refs`
  - master dashboard shows PyJHora evidence readiness
  - README truth text stays honest

- [ ] **Step 1: Write failing backtest/dashboard tests**
- [ ] **Step 2: Run targeted tests to verify failure**
- [ ] **Step 3: Update `historical_event_backtest.py`**
  - Link relevant artifact refs by front/domain; do not overclaim validation.
- [ ] **Step 4: Update `oracle_closure_master_dashboard.py`**
  - Lift manifest summary into one closure board.
- [ ] **Step 5: Refresh README wording**
  - Keep “black-box evidence only” explicit.
- [ ] **Step 6: Re-run targeted tests**

## Task 7: Final regression pack
**Files:**
- No new files unless a missing narrow test is unavoidable

**Run:**
- [ ] `python3 -m pytest tests/test_muhurta.py tests/test_unified_consultation_orchestrator.py tests/test_api_server_security.py -q`
- [ ] `python3 -m pytest tests/test_vedastro_runtime_mode_diagnostics.py tests/test_vedastro_service_adapter_executor.py tests/test_vedastro_official_full_snapshot.py tests/test_vedastro_official_mcp_bridge.py tests/test_frontend_productization.py -q`
- [ ] `python3 -m pytest tests/test_pyjhora_oracle_artifact_manifest.py tests/test_oracle_benchmark_inventory.py tests/test_external_oracle_sanity_closure.py tests/test_historical_event_backtest.py tests/test_oracle_closure_master_dashboard.py -q`
- [ ] Run one manual local workflow smoke:
  - direct chart
  - prashna/time question
  - one repeated request to verify cache hit metadata
- [ ] Record remaining blocked items explicitly, especially:
  - official live endpoint availability
  - free-tier queue delay
  - missing PyJHora evidence fronts

## Fastest Execution Order

1. Task 3
2. Task 4
3. Task 1
4. Task 2
5. Task 5
6. Task 6
7. Task 7

Reason:

- VedAstro default truth is the highest-value user-facing fix.
- `muhurta/panchanga` sidecar reuses local code and is cheap once workflow contract is stable.
- PyJHora evidence work is mainly audit/dashboards, not user runtime critical path.

## Stop Conditions

Stop and mark `blocked` if any of these happen:

- VedAstro official endpoint can only return `blocked` in the current environment and no cache sample exists.
- A proposed PyJHora consumption change would require importing AGPL code instead of consuming stored artifacts.
- `panchanga_api`-style sidecar would require a second planner/entry system instead of extending current unified workflow.
