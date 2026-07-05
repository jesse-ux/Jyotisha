# VedAstro Runtime Truth Contract Implementation Plan
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
**Goal:** Expose machine-checkable runtime truth for VedAstro official execution and interpretation-source invocation so users and APIs can see what actually ran.
**Architecture:** Extend the existing unified consultation/high-rigor contract instead of building a new pipeline. Reuse `vedastro_service_adapter`, `vedastro_priority`, existing interpretation source inventory/strict workflow markers, and API response contracts.
**Tech Stack:** Python 3.11, existing `scripts/` API server/orchestrator modules, pytest.
## Global Constraints
- Reuse existing repo modules; no new parallel runtime chain.
- Keep VedAstro official as preferred evidence, but do not overclaim full-catalog execution.
- Add tests first for new response contract fields.
- Preserve current honesty boundaries and blocked states.

### Task 1: Add failing API contract tests for runtime truth fields
**Files:**
- Modify: `tests/test_vedastro_external_technique_evidence.py`
- Modify: `tests/test_api_server_security.py`
**Interfaces:**
- Consumes: `JyotishAPIHandler._high_rigor_vedastro_official_summary`, `execute_consultation_workflow`
- Produces: expected fields `runtime_truth`, `official_execution_layers`, `interpretation_source_runtime_coverage`
- [ ] Step 1: Write failing tests for consultation/high-rigor responses.
- [ ] Step 2: Run targeted pytest to confirm failure.
- [ ] Step 3: Keep assertions narrow: presence, semantics, blocked/partial handling.
- [ ] Step 4: Re-run targeted pytest.

### Task 2: Implement VedAstro runtime truth summary
**Files:**
- Modify: `scripts/jyotish_api_server.py`
- Check: `scripts/vedastro_priority.py`
**Interfaces:**
- Consumes: chart modules, `vedastro_official_full_snapshot`, `source_priority`, evidence snapshot
- Produces: normalized runtime truth block with official mode, readiness, executed layers, blocked reasons, catalog-vs-runtime boundary
- [ ] Step 1: Add helper(s) building normalized `runtime_truth` summary.
- [ ] Step 2: Thread summary into `_high_rigor_vedastro_official_summary`.
- [ ] Step 3: Thread same summary into consultation workflow top-level payload.
- [ ] Step 4: Run targeted tests.

### Task 3: Implement interpretation-source runtime coverage summary
**Files:**
- Modify: `scripts/jyotish_api_server.py`
- Check: `mcp_server.py`, `scripts/interpretation_source_inventory_gate.py`
**Interfaces:**
- Consumes: strict workflow secondary-context markers, existing source-pack status, current audit boundaries
- Produces: API-visible summary of proven runtime visibility vs unproven source assets
- [ ] Step 1: Add helper returning compact coverage summary.
- [ ] Step 2: Attach to consultation workflow and thematic/high-rigor payloads.
- [ ] Step 3: Ensure summary distinguishes `proven_runtime_markers` from `not_fully_closed`.
- [ ] Step 4: Run targeted tests.

### Task 4: Add reusable audit script for machine-checkable coverage
**Files:**
- Create: `scripts/interpretation_source_runtime_coverage.py`
- Add Test: `tests/test_interpretation_source_runtime_coverage.py`
**Interfaces:**
- Consumes: existing inventory gate data + strict workflow markers from runtime packs
- Produces: JSON/markdown report with extraction/source-pack/runtime visibility gaps
- [ ] Step 1: Write failing test for minimal report shape.
- [ ] Step 2: Implement minimal script reusing existing modules.
- [ ] Step 3: Run targeted tests.

### Task 5: Verify end-to-end targeted regression
**Files:**
- None or docs if output contract docs need refresh
**Interfaces:**
- Consumes: new contract fields/tests/scripts
- Produces: fresh verification evidence
- [ ] Step 1: Run targeted pytest set covering API contract + new coverage tool.
- [ ] Step 2: Run `python3 scripts/diagnose_vedastro_mode.py`.
- [ ] Step 3: Run new coverage script once in JSON mode.
- [ ] Step 4: Summarize actual status, not aspirational status.


### Task 6: Surface runtime truth in MCP and frontend result payloads
**Files:**
- Modify: `mcp_server.py`
- Modify: `jyotish-app/skill-map.js`
- Test: `tests/test_frontend_productization.py` and/or existing MCP/API contract tests
**Interfaces:**
- Consumes: `consultation_workflow` response contract
- Produces: visible runtime truth / source coverage status in MCP strict workflow output and frontend result panels
- [ ] Step 1: Add failing tests for visible payload fields.
- [ ] Step 2: Thread fields through MCP strict workflow response.
- [ ] Step 3: Render compact runtime truth/source coverage block in frontend result page.
- [ ] Step 4: Run targeted tests.

### Task 7: Harden official-extended runtime preflight
**Files:**
- Modify: `scripts/diagnose_vedastro_mode.py`
- Modify: `scripts/vedastro_service_adapter.py` and/or `.env.official.example` only if needed
- Test: existing VedAstro diagnostics/adapter tests
**Interfaces:**
- Consumes: current env + adapter time budget
- Produces: sharper preflight diagnosis for why official mode is not ready; no silent fast fallback confusion
- [ ] Step 1: Add failing diagnostics tests if missing.
- [ ] Step 2: Expose concrete readiness blockers in output contract.
- [ ] Step 3: Re-run diagnostics tests.

### Task 8: Split slow verification into smaller quality-gate profile(s)
**Files:**
- Modify: `scripts/run_quality_gate.py`
- Modify: relevant tests/docs if profile list changes
**Interfaces:**
- Consumes: current gate profiles and long-running test groups
- Produces: smaller verification profile(s) for runtime-truth/strict-workflow/official contracts
- [ ] Step 1: Add failing tests or assertions for new profile names/commands.
- [ ] Step 2: Implement profile split and command grouping.
- [ ] Step 3: Run targeted gate/profile tests.
