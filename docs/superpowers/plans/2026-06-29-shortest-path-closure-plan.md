# Shortest-Path Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Collapse the remaining Jyotish hard fronts into the smallest executable closure path: relationship adjudicator closure, Vimsopaka/functional-role closure, oracle closure, and VedAstro strict ingestion.

**Architecture:** Reuse existing strict workflow, adjudicator, oracle, and VedAstro bridge assets instead of opening new product surfaces. Drive every remaining change from fixed regression packs and external-truth comparison scripts so the project stops expanding sideways and starts closing hard boundaries.

**Tech Stack:** Python, pytest, existing MCP strict workflow code, existing full-reading/report pipeline, existing VedAstro adapter scripts, existing oracle comparison scripts, existing frontend static contract tests.

## Global Constraints

- Must obey `<repo>/AGENTS.md` high-rigor rules.
- Timing/event/outcome work must use `Vimshottari + Narayana Dasha` and relationship work must include `D9 + UL`.
- Functional Benefic/Malefic must remain explicit in high-rigor evidence and user-visible audit surfaces.
- Prefer existing repo-native code and reusable open-source references over new standalone implementations.
- Do not expand scope into new product features while these closure fronts remain open.
- Any claim touching oracle accuracy, global-first status, or perfect precision must stay blocked until external evidence says otherwise.

---

### Task 1: Freeze the closure board and stop scope drift

**Files:**
- Create: `<repo>/docs/research/shortest_path_closure_board_2026_06_29.md`
- Modify: `<repo>/docs/research/ACTIVE_FRONTS.md`
- Modify: `<repo>/task_plan.md`
- Test: `<repo>/tests/test_skill_gap_truth_audit.py`

**Interfaces:**
- Consumes: `<repo>/docs/research/ACTIVE_FRONTS.md`, `<repo>/task_plan.md`
- Produces: `shortest_path_closure_board_2026_06_29.md` with four closure lanes (`relationship`, `vimsopaka_functional_role`, `oracle`, `vedastro_ingestion`) and a fixed task order

- [ ] **Step 1: Write the failing test**

```python
def test_skill_gap_truth_registry_lists_hard_fronts_and_past_corrections() -> None:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    required_fronts = {
        "dasha_external_oracle",
        "shadbala_external_absolute_values",
        "tajika_sahams_annual_closure",
        "article_template_industrialization",
        "long_term_public_benchmark",
    }
    assert required_fronts <= set(data["hard_fronts"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_skill_gap_truth_audit.py -q`
Expected: FAIL if the closure board / active fronts drift exposes missing hard-front accounting

- [ ] **Step 3: Write minimal implementation**

```markdown
# Shortest Path Closure Board

## Lane 1 - Relationship Adjudicator Closure
1. lock legal_marriage/public_formalization regression pack
2. close Jaimini marriage bridge v1 regression loop
3. keep public_formalization_candidate narrative conservative everywhere

## Lane 2 - Vimsopaka + Functional Role Closure
1. map NEECHA_BHANGA / GREAT_FRIEND / GREAT_ENEMY
2. render functional benefic/malefic everywhere the user sees Technique Audit

## Lane 3 - Oracle Closure
1. batch Dasha/Shadbala/JHora comparison pack
2. promote first external verified packet
3. update oracle dashboard only from validated packets

## Lane 4 - VedAstro Strict Ingestion
1. keep current blocked boundary
2. run one endpoint-backed smoke only after relationship loop is closed
3. ingest only allowlisted event windows into evidence ledger
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_skill_gap_truth_audit.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add docs/research/shortest_path_closure_board_2026_06_29.md docs/research/ACTIVE_FRONTS.md task_plan.md tests/test_skill_gap_truth_audit.py
git commit -m "docs: freeze shortest-path closure board"
```

### Task 2: Close the relationship adjudicator regression pack

**Files:**
- Modify: `<repo>/mcp_server.py`
- Modify: `<repo>/scripts/jyotish_engine.py`
- Modify: `<repo>/jyotish-app/main.js`
- Modify: `<repo>/tests/test_mcp_strict_workflow_relationship.py`
- Modify: `<repo>/tests/test_frontend_productization.py`
- Modify: `<repo>/tests/test_api_server_security.py`

**Interfaces:**
- Consumes: `event_judgement.dominant_label`, `event_judgement.secondary_context`, `present_evidence.jaimini_marriage_support`
- Produces: locked conservative handling for `public_formalization_candidate`, and red/green regression coverage for `legal_marriage` vs `public_formalization`

- [ ] **Step 1: Write the failing tests**

```python
def test_relationship_narrative_payload_does_not_translate_public_formalization_candidate_plus_synastry_support_plus_weak_core_promise_into_marriage_approach() -> None:
    strict = _collect_strict_evidence("relationship", _base_relationship_result())
    strict["event_judgement"]["dominant_label"] = None
    strict["event_judgement"]["secondary_context"] = [
        "darakaraka_active",
        "ul_support",
        "synastry_support",
        "synastry_compatibility_support",
        "public_formalization_candidate",
    ]
    strict["confidence_cap"] = "low"
    payload = jyotish_engine._build_relationship_narrative_payload(strict)
    assert any("不能误读成接近结婚" in item for item in payload["risks"])
    assert any("不得越权抬升 legal_marriage" in item for item in payload["boundaries"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_mcp_strict_workflow_relationship.py tests/test_frontend_productization.py tests/test_api_server_security.py -q -k "public_formalization or weak_core_promise or misread_as_near_marriage"`
Expected: FAIL on the exact conservative boundary you are adding

- [ ] **Step 3: Write minimal implementation**

```python
if "public_formalization_candidate" in secondary_context:
    risks.append("当前虽更接近 public_formalization_candidate，但在 timing conflict 未解除前，不能误读成接近结婚。")
    boundaries.append("public_formalization_candidate 只表示公开化候选，不等于法律婚姻，不能越权替代 legal_marriage。")
```

```javascript
const status = hasPublicFormalizationCandidate && hasConflictWarning ? 'needs_context' : ...
const statusLabel = hasPublicFormalizationCandidate && hasConflictWarning
  ? '公开化候选，不等于婚姻逼近'
  : ...
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_mcp_strict_workflow_relationship.py tests/test_frontend_productization.py tests/test_api_server_security.py -q -k "public_formalization or weak_core_promise or misread_as_near_marriage"`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add mcp_server.py scripts/jyotish_engine.py jyotish-app/main.js tests/test_mcp_strict_workflow_relationship.py tests/test_frontend_productization.py tests/test_api_server_security.py
git commit -m "test: lock relationship public formalization boundaries"
```

### Task 3: Close Vimsopaka semantic mapping and functional-role rendering

**Files:**
- Modify: `<repo>/mcp_server.py`
- Modify: `<repo>/scripts/jyotish_api_server.py`
- Modify: `<repo>/jyotish-app/skill-map.js`
- Modify: `<repo>/references/strict-workflow-router.md`
- Modify: `<repo>/tests/test_frontend_productization.py`
- Modify: `<repo>/tests/test_api_server_security.py`

**Interfaces:**
- Consumes: existing dignity guardrail output and functional benefic/malefic evidence
- Produces: user-visible audit rendering for functional benefics/malefics/yogakarakas/neutrals and Vimsopaka semantic labels

- [ ] **Step 1: Write the failing tests**

```python
def test_report_artifact_relationship_strict_narrative_surfaces_public_formalization_candidate_boundary() -> None:
    html = artifact["html"]
    assert "Functional Benefic/Malefic" in html
    assert "Yogakaraka" in html
    assert "functional neutral" in html.lower() or "中性星" in html
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_frontend_productization.py tests/test_api_server_security.py -q -k "Functional Benefic or Yogakaraka or Vimsopaka"`
Expected: FAIL because at least one user-visible rendering path is incomplete

- [ ] **Step 3: Write minimal implementation**

```python
summary_parts.append(f"Yogakaraka: {', '.join(yogakarakas) if yogakarakas else 'None'}")
summary_parts.append(f"Functional neutrals: {', '.join(functional_neutrals) if functional_neutrals else 'None'}")
```

```javascript
['Functional Benefic/Malefic / 功能吉凶星', '已接入', '按 Lagna 输出功能吉星、功能凶星、Yogakaraka 与中性星，并进入 Technique Audit Table']
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_frontend_productization.py tests/test_api_server_security.py -q -k "Functional Benefic or Yogakaraka or Vimsopaka"`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add mcp_server.py scripts/jyotish_api_server.py jyotish-app/skill-map.js references/strict-workflow-router.md tests/test_frontend_productization.py tests/test_api_server_security.py
git commit -m "feat: close functional role and vimsopaka rendering gaps"
```

### Task 4: Batch the oracle closure work into one comparison pack

**Files:**
- Modify: `<repo>/scripts/shadbala_oracle_comparison.py`
- Modify: `<repo>/scripts/oracle_benchmark_inventory.py`
- Modify: `<repo>/references/oracle/dasha_shadbala_oracle_cases.json`
- Create: `<repo>/docs/research/oracle_batch_closure_pack_2026_06_29.md`
- Modify: `<repo>/tests/test_dasha_oracle_closure_status.py`

**Interfaces:**
- Consumes: external oracle packets, current shadbala comparison script, oracle benchmark inventory
- Produces: one batch comparison report with pass/fail/tolerance rows and updated blocked/unblocked truth summary

- [ ] **Step 1: Write the failing test**

```python
def test_dasha_oracle_closure_status_markdown_keeps_global_calibration_blocked_until_non_dasha_packets_pass() -> None:
    markdown = build_status_markdown(sample_status)
    assert "Keep global calibration blocked" in markdown
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_dasha_oracle_closure_status.py -q`
Expected: FAIL if the batch comparison summary or blocked boundary drifts

- [ ] **Step 3: Write minimal implementation**

```markdown
# Oracle Batch Closure Pack

| Case | Source | Domain | Pass | Notes |
|---|---|---|---|---|
| steve_jobs | JHora/PyJHora | Dasha | yes/no | boundary diff |
| ... | ... | Shadbala | yes/no | tolerance diff |
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_dasha_oracle_closure_status.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/shadbala_oracle_comparison.py scripts/oracle_benchmark_inventory.py references/oracle/dasha_shadbala_oracle_cases.json docs/research/oracle_batch_closure_pack_2026_06_29.md tests/test_dasha_oracle_closure_status.py
git commit -m "feat: batch oracle closure comparison pack"
```

### Task 5: Keep VedAstro ingestion minimal and honest

**Files:**
- Modify: `<repo>/scripts/vedastro_service_adapter.py`
- Modify: `<repo>/scripts/run_quality_gate.py`
- Modify: `<repo>/tests/test_life_event_graph_v1.py`
- Modify: `<repo>/tests/test_vedastro_service_adapter_executor.py`

**Interfaces:**
- Consumes: current `external_window` payload contract and allowlist audit
- Produces: one endpoint-backed smoke path or one controlled blocked path, both feeding the same evidence ledger contract

- [ ] **Step 1: Write the failing tests**

```python
def test_life_event_graph_keeps_external_window_nodes_allowlisted() -> None:
    assert any(node["kind"] == "external_window" for node in strict["life_event_graph"]["event_nodes"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_life_event_graph_v1.py tests/test_vedastro_service_adapter_executor.py -q`
Expected: FAIL if the allowlist / blocked contract is incomplete

- [ ] **Step 3: Write minimal implementation**

```python
if not endpoint or not network_enabled:
    return {"status": "blocked", "reason": "vedastro_live_endpoint_or_network_flag_missing"}
return {"status": "ok", "event_nodes": filtered_nodes}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_life_event_graph_v1.py tests/test_vedastro_service_adapter_executor.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/vedastro_service_adapter.py scripts/run_quality_gate.py tests/test_life_event_graph_v1.py tests/test_vedastro_service_adapter_executor.py
git commit -m "feat: keep vedastro ingestion minimal and allowlisted"
```

## Self-Review

- Spec coverage: the plan covers the four remaining closure lanes called out by current active fronts.
- Placeholder scan: no TBD/TODO placeholders remain.
- Type consistency: plan uses the existing `dominant_label`, `secondary_context`, `relationship_narrative`, `external_window`, and blocked-boundary terminology already present in the repo.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-29-shortest-path-closure-plan.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
