# Unified Consultation Runtime Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the consultation runtime planner execute real reusable steps, make thematic report consume upstream unified contracts before deriving again, and collapse monthly adjudication / interpretation axes / strict audit gate into one shared adjudication object reused by guided topics, AI payloads, and frontend.

**Architecture:** Keep the existing repo surfaces, but stop letting each layer rebuild its own partial truth. The API workflow becomes the single executor of route steps, full-reading/chart strict outputs become preferred upstream evidence for thematic report, and a compact `strict_adjudication_bundle` becomes the canonical shared object carried through backend, prompt-pack, guided topics, and UI.

**Tech Stack:** Python 3, existing `jyotish_api_server.py`, `jyotish_engine.py`, `guided_topic_discovery.py`, vanilla frontend JS, pytest.

## Global Constraints

- Reuse existing repo code paths instead of inventing new parallel engines.
- Use TDD: failing tests first, then minimal implementation.
- Do not break current API payload compatibility where avoidable.
- Preserve VedAstro official-first boundary and fallback honesty.
- Keep edits scoped to the current workflow and display contract.

---

### Task 1: Lock the unified runtime and adjudication bundle contract in tests

**Files:**
- Modify: `/Users/wuyongnaren/Documents/印度占星/tests/test_api_server_security.py`
- Modify: `/Users/wuyongnaren/Documents/印度占星/tests/test_cli_smoke.py`
- Modify: `/Users/wuyongnaren/Documents/印度占星/tests/test_frontend_productization.py`

**Interfaces:**
- Consumes: `_compute_consultation_workflow(...)`, `_compute_thematic_report(...)`, `build_guided_topics(...)`
- Produces: failing tests requiring `runtime_planner.executed_steps`, `strict_adjudication_bundle`, and thematic-report reuse behavior

- [ ] **Step 1: Write failing API workflow/runtime tests**

Add assertions to `tests/test_api_server_security.py` for:

```python
assert result["runtime_planner"]["executed_steps"] == [
    "compute_chart",
    "run_rectification_gate",
    "run_historical_event_backtest",
    "run_thematic_report",
]
assert result["runtime_planner"]["skipped_steps"] == []
assert result["thematic_report"]["mode"] == "upstream_contract_reuse"
assert result["thematic_report"]["evidence_source"]["source"] == "consultation_workflow_upstream_contract"
```

- [ ] **Step 2: Run targeted API workflow test to verify failure**

Run: `python3 -m pytest tests/test_api_server_security.py::test_consultation_workflow_reuses_chart_data_for_thematic_report_without_recursive_full_reading -q`

Expected: FAIL because `executed_steps` / `mode` / `evidence_source` are missing or different.

- [ ] **Step 3: Write failing shared adjudication bundle tests**

Add assertions in `tests/test_api_server_security.py` and `tests/test_cli_smoke.py`:

```python
bundle = career["strict_adjudication_bundle"]
assert bundle["monthly_adjudication_summary"]["primary_state"]["value"] == "推进"
assert bundle["strict_audit_gate"]["functional_benefic_malefic"]["gate"] == "hard"
assert bundle["interpretation_axes"][0]["axis"] == "角色定位"
```

and:

```python
assert topic["strict_adjudication_bundle"]["monthly_adjudication_summary"] == topic["monthly_adjudication_summary"]
assert topic["strict_adjudication_bundle"]["strict_audit_gate"] == topic["strict_audit_gate"]
```

- [ ] **Step 4: Run targeted adjudication tests to verify failure**

Run: `python3 -m pytest tests/test_api_server_security.py::test_thematic_report_interpretation_axes_are_strict_paragraphs_for_each_theme tests/test_cli_smoke.py::test_full_reading_guided_topics_can_carry_official_day_signal_summary -q`

Expected: FAIL because `strict_adjudication_bundle` is missing.

- [ ] **Step 5: Commit**

```bash
git add tests/test_api_server_security.py tests/test_cli_smoke.py tests/test_frontend_productization.py
git commit -m "test: lock unified consultation runtime contract"
```

### Task 2: Make runtime_planner a real executor and make thematic report prefer upstream unified contracts

**Files:**
- Modify: `/Users/wuyongnaren/Documents/印度占星/scripts/unified_consultation_orchestrator.py`
- Modify: `/Users/wuyongnaren/Documents/印度占星/scripts/jyotish_api_server.py`
- Test: `/Users/wuyongnaren/Documents/印度占星/tests/test_api_server_security.py`

**Interfaces:**
- Consumes: `UnifiedConsultationOrchestrator.runtime_planner(...)`, `_compute_consultation_workflow(...)`
- Produces: planner with `executed_steps` / `skipped_steps`, thematic input payload with `strict_workflow_contracts`, and `_compute_thematic_report(...)` mode `upstream_contract_reuse`

- [ ] **Step 1: Add failing helper-level test coverage if needed**

If `tests/test_unified_consultation_orchestrator.py` lacks direct planner coverage, add:

```python
planner = orchestrator.runtime_planner(...)
assert planner["sync_steps"][0] == "compute_chart"
assert planner["reuse_contract"]["thematic_report"] == "thematic_report"
```

- [ ] **Step 2: Implement runtime executed/skipped step recording**

In `/Users/wuyongnaren/Documents/印度占星/scripts/jyotish_api_server.py`, refactor `_compute_consultation_workflow(...)` so it:
- initializes `executed_steps = []`, `skipped_steps = []`
- runs only steps listed in `runtime_planner["sync_steps"]`
- appends actual executed step names
- records skipped steps from the known runtime step set

- [ ] **Step 3: Pass upstream strict data into thematic report**

When building the thematic payload in `_compute_consultation_workflow(...)`, pass:

```python
"upstream_contract": {
    "chart": chart_for_theme,
    "strict_workflow_contracts": prompt_snapshot_contracts,
    "guided_topics": chart_modules_guided_topics,
}
```

where `prompt_snapshot_contracts` comes from `chart["ai_prompt_pack"]["evidence_snapshot"]["strict_workflow_contracts"]` when available.

- [ ] **Step 4: Implement upstream-contract-first thematic reuse**

In `_compute_thematic_report(...)`, before calling `_derive_thematic_evidence(...)`, detect:

```python
upstream_contract = body.get("upstream_contract")
```

and if it contains usable `strict_workflow_contracts` or chart evidence, set:
- `mode = "upstream_contract_reuse"`
- `evidence_source["source"] = "consultation_workflow_upstream_contract"`
- reuse upstream evidence/contracts before local derivation fallback

- [ ] **Step 5: Run tests to verify green**

Run: `python3 -m pytest tests/test_api_server_security.py::test_consultation_workflow_reuses_chart_data_for_thematic_report_without_recursive_full_reading tests/test_api_server_security.py::test_thematic_report_handles_missing_dasa_convergence_without_crash tests/test_unified_consultation_orchestrator.py -q`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add scripts/unified_consultation_orchestrator.py scripts/jyotish_api_server.py tests/test_api_server_security.py tests/test_unified_consultation_orchestrator.py
git commit -m "feat: execute unified consultation runtime steps"
```

### Task 3: Collapse monthly adjudication, audit gate, and axes into one canonical strict adjudication bundle

**Files:**
- Modify: `/Users/wuyongnaren/Documents/印度占星/scripts/jyotish_api_server.py`
- Modify: `/Users/wuyongnaren/Documents/印度占星/scripts/guided_topic_discovery.py`
- Modify: `/Users/wuyongnaren/Documents/印度占星/scripts/jyotish_engine.py`
- Test: `/Users/wuyongnaren/Documents/印度占星/tests/test_api_server_security.py`
- Test: `/Users/wuyongnaren/Documents/印度占星/tests/test_cli_smoke.py`

**Interfaces:**
- Consumes: strict workflow contracts, `monthly_adjudication_summary`, `technique_audit_summary`, `interpretation_axes`
- Produces: `strict_adjudication_bundle` with:
  - `monthly_adjudication_summary`
  - `monthly_adjudication_summary_humanized`
  - `strict_audit_gate`
  - `interpretation_axes`
  - `narrative_contract`

- [ ] **Step 1: Add bundle builder in API server**

Create a helper in `/Users/wuyongnaren/Documents/印度占星/scripts/jyotish_api_server.py` that returns:

```python
{
    "theme": theme_name,
    "monthly_adjudication_summary": monthly_frame,
    "monthly_adjudication_summary_humanized": humanized,
    "strict_audit_gate": report_payload.get("technique_audit_summary") or {},
    "interpretation_axes": axes,
    "narrative_contract": {...},
}
```

- [ ] **Step 2: Attach canonical bundle to thematic report payload**

In `_apply_monthly_adjudication_to_theme_report(...)`, set:

```python
report_payload["strict_adjudication_bundle"] = bundle
```

while keeping legacy top-level fields for compatibility.

- [ ] **Step 3: Make guided topics read only the bundle first**

In `/Users/wuyongnaren/Documents/印度占星/scripts/guided_topic_discovery.py`, replace separate contract lookups with:

```python
bundle = _as_dict(contract.get("strict_adjudication_bundle"))
```

and populate:
- `strict_audit_gate`
- `monthly_adjudication_summary`
- `official_day_signal_summary` fallback only if not in bundle

- [ ] **Step 4: Make prompt pack carry the bundle through**

In `/Users/wuyongnaren/Documents/印度占星/scripts/jyotish_engine.py`, ensure each strict workflow contract already exported into `ai_prompt_pack.evidence_snapshot.strict_workflow_contracts` includes `strict_adjudication_bundle`.

- [ ] **Step 5: Run backend/shared contract tests**

Run: `python3 -m pytest tests/test_api_server_security.py::test_apply_monthly_adjudication_to_theme_report_injects_four_layers_into_final_chinese_fields tests/test_api_server_security.py::test_thematic_report_interpretation_axes_are_strict_paragraphs_for_each_theme tests/test_cli_smoke.py::test_full_reading_guided_topics_can_carry_official_day_signal_summary -q`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add scripts/jyotish_api_server.py scripts/guided_topic_discovery.py scripts/jyotish_engine.py tests/test_api_server_security.py tests/test_cli_smoke.py
git commit -m "feat: unify strict adjudication bundle"
```

### Task 4: Make frontend and AI consume the single shared bundle

**Files:**
- Modify: `/Users/wuyongnaren/Documents/印度占星/jyotish-app/main.js`
- Modify: `/Users/wuyongnaren/Documents/印度占星/jyotish-app/ai-chat.js`
- Modify: `/Users/wuyongnaren/Documents/印度占星/tests/test_frontend_productization.py`

**Interfaces:**
- Consumes: `strict_adjudication_bundle`
- Produces: UI and AI prompt entry consuming bundle first, legacy fields second

- [ ] **Step 1: Add failing frontend assertions**

Add assertions requiring:

```python
assert "strict_adjudication_bundle" in main
assert "strict_adjudication_bundle" in ai_chat
```

and keep legacy checks for compatibility.

- [ ] **Step 2: Update guided topic card rendering**

In `/Users/wuyongnaren/Documents/印度占星/jyotish-app/main.js`, read:

```javascript
const bundle = topic?.strict_adjudication_bundle || {};
```

and derive:
- `strict_audit_gate`
- `monthly_adjudication_summary`
- `interpretation_axes`

from the bundle first.

- [ ] **Step 3: Update AI chat payload construction**

In `/Users/wuyongnaren/Documents/印度占星/jyotish-app/ai-chat.js`, include:

```javascript
guidedTopicContext.strict_adjudication_bundle
```

as the first-class context object, while preserving old fields.

- [ ] **Step 4: Run frontend contract tests**

Run: `python3 -m pytest tests/test_frontend_productization.py::test_guided_topic_questions_reuse_ai_chat_entry tests/test_frontend_productization.py::test_complete_reading_surfaces_guided_topic_discovery -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add jyotish-app/main.js jyotish-app/ai-chat.js tests/test_frontend_productization.py
git commit -m "feat: make frontend consume strict adjudication bundle"
```

### Task 5: Run the smallest real regressions and inspect real-user output

**Files:**
- Modify: `/Users/wuyongnaren/Documents/印度占星/progress.md` (only if you are already tracking this thread there)

**Interfaces:**
- Consumes: completed runtime/thematic/bundle/frontend flow
- Produces: verified real output for the REDACTED_DATE REDACTED_TIME REDACTED_PLACE case

- [ ] **Step 1: Run focused regression suite**

Run:

```bash
python3 -m pytest \
  tests/test_api_server_security.py::test_consultation_workflow_reuses_chart_data_for_thematic_report_without_recursive_full_reading \
  tests/test_api_server_security.py::test_thematic_report_interpretation_axes_are_strict_paragraphs_for_each_theme \
  tests/test_cli_smoke.py::test_full_reading_guided_topics_can_carry_official_day_signal_summary \
  tests/test_frontend_productization.py::test_guided_topic_questions_reuse_ai_chat_entry \
  -q
```

Expected: all PASS.

- [ ] **Step 2: Run real consultation workflow sample**

Run a local Python one-off calling `_compute_consultation_workflow(...)` with:
- `REDACTED_DATE REDACTED_TIME`
- `lat=36.42`
- `lon=114.2`
- `tz=8`
- themes `career/marriage/wealth`

Verify:
- `runtime_planner.executed_steps` is populated
- `thematic_report.mode == "upstream_contract_reuse"`
- each theme contains `strict_adjudication_bundle`

- [ ] **Step 3: Summarize verified behavior**

Record the exact outputs observed for:
- executed runtime steps
- thematic report mode
- presence of strict adjudication bundle in theme payloads and guided topics

- [ ] **Step 4: Commit**

```bash
git add progress.md
git commit -m "docs: record unified consultation runtime verification"
```

## Self-Review

- Spec coverage: the three requested root-cause cuts are directly covered by Tasks 2, 3, and 4.
- Placeholder scan: no TBD/TODO placeholders remain.
- Type consistency: the canonical object is always named `strict_adjudication_bundle`; runtime execution telemetry always uses `executed_steps` and `skipped_steps`.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-01-unified-consultation-runtime-hardening.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints
