# Top Reader Adjudication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the default `career`, `relationship`, and `finance` reading workflows to use a shared top-reader-style adjudication skeleton with multi-reference summaries and selected modifier bridges, while reusing existing strict workflow code and minimizing extra compute.

**Architecture:** Reuse the current strict workflow builders in `mcp_server.py` as the primary evidence source, normalize them through a shared adjudication helper, and surface the reshaped contract through `jyotish_engine.py`, `jyotish_api_server.py`, and the existing prompt-pack/frontend consumer layers. Do not introduce a second engine or a full 641-callable VedAstro execution path; instead, reshape current evidence into a common four-stage contract plus a lightweight `multi_reference_reading_summary`.

**Tech Stack:** Python, existing strict workflow collectors, pytest, existing frontend productization tests, existing prompt-pack evidence snapshot contract.

## Global Constraints

- Reuse current strict workflow collectors before adding new collectors.
- Reuse existing bridge helpers before creating new scoring paths.
- Reuse current full-reading/module outputs by reference where possible.
- Do not add all-method VedAstro execution to the default path.
- Prefer small contract reshaping over new compute-heavy logic.
- Keep official calls cached and reused; do not add new heavyweight request fans.
- Preserve the existing honesty boundaries: emit `blocked`, `conflicts`, and `confidence_cap` instead of smoothing over missing layers.
- Keep `career`, `relationship`, and `finance` domain-specific evidence requirements intact while sharing structure.

---

### Task 1: Add the shared adjudication contract builder in `mcp_server.py`

**Files:**
- Modify: `/Users/wuyongnaren/Documents/印度占星/mcp_server.py`
- Test: `/Users/wuyongnaren/Documents/印度占星/tests/test_mcp_strict_workflow_career.py`
- Test: `/Users/wuyongnaren/Documents/印度占星/tests/test_mcp_strict_workflow_relationship.py`
- Test: `/Users/wuyongnaren/Documents/印度占星/tests/test_mcp_strict_workflow_finance.py`

**Interfaces:**
- Consumes:
  - existing strict route `present_evidence`
  - existing `event_judgement`
  - existing `official_primary_evidence`
  - existing `local_supplemental_evidence`
  - existing `conflicts`
  - existing `confidence_cap`
- Produces:
  - `_build_adjudication_stages(route: str, present: Dict[str, Any], event_judgement: Dict[str, Any]) -> Dict[str, Any]`
  - `_build_multi_reference_reading_summary(route: str, present: Dict[str, Any], strict: Dict[str, Any]) -> Dict[str, Any]`
  - strict contract keys:
    - `adjudication_stages`
    - `multi_reference_reading_summary`
    - `verdict`
    - `dominant_label`
    - `main_conflicts`

- [ ] **Step 1: Write the failing tests**

Add assertions to each strict workflow domain test file for the new shared fields:

```python
def test_career_strict_contract_exposes_adjudication_stages() -> None:
    result = mcp_server._collect_strict_evidence("career", modules)
    assert result["adjudication_stages"]["promise"]["status"] in {"present", "weak", "missing"}
    assert result["adjudication_stages"]["activation"]["required_timing_systems"] == ["Vimshottari", "Narayana"]
    assert "multi_reference_reading_summary" in result
    assert "root_frame" in result["multi_reference_reading_summary"]
```

Repeat the same shape expectation for `relationship` and `finance`, adapted to each route.

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python3 -m pytest tests/test_mcp_strict_workflow_career.py tests/test_mcp_strict_workflow_relationship.py tests/test_mcp_strict_workflow_finance.py -k "adjudication_stages or multi_reference_reading_summary" -q
```

Expected: FAIL with missing strict contract keys such as `adjudication_stages` or `multi_reference_reading_summary`.

- [ ] **Step 3: Write the minimal implementation**

Implement shared helpers near the existing strict helper section in `mcp_server.py`:

```python
def _build_adjudication_stages(route: str, present: Dict[str, Any], event_judgement: Dict[str, Any]) -> Dict[str, Any]:
    dominant_label = event_judgement.get("dominant_label")
    return {
        "promise": {
            "status": "present" if _has_promise_evidence(route, present) else "weak",
            "drivers": _promise_drivers(route, present),
        },
        "activation": {
            "status": "present" if _has_activation_evidence(route, present) else "weak",
            "required_timing_systems": ["Vimshottari", "Narayana"],
            "drivers": _activation_drivers(route, present),
        },
        "manifestation": {
            "status": "present" if dominant_label else "weak",
            "drivers": event_judgement.get("secondary_context") or [],
        },
        "label": {
            "status": "present" if dominant_label else "missing",
            "value": dominant_label,
            "verdict": event_judgement.get("verdict"),
        },
    }
```

Also add a small route-aware summary builder:

```python
def _build_multi_reference_reading_summary(route: str, present: Dict[str, Any], strict: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "root_frame": _summary_root_frame(route, present),
        "divisional_frame": _summary_divisional_frame(route, present),
        "visibility_frame": _summary_visibility_frame(route, present),
        "karaka_frame": _summary_karaka_frame(route, present),
        "timing_frame": _summary_timing_frame(route, present),
        "modifier_frame": _summary_modifier_frame(route, present),
        "conflict_frame": {
            "conflicts": strict.get("conflicts") or [],
            "confidence_cap": strict.get("confidence_cap"),
        },
    }
```

Attach these fields inside each strict route result, reusing the current per-route `present` and `event_judgement`.

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python3 -m pytest tests/test_mcp_strict_workflow_career.py tests/test_mcp_strict_workflow_relationship.py tests/test_mcp_strict_workflow_finance.py -k "adjudication_stages or multi_reference_reading_summary" -q
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add mcp_server.py tests/test_mcp_strict_workflow_career.py tests/test_mcp_strict_workflow_relationship.py tests/test_mcp_strict_workflow_finance.py
git commit -m "feat: add shared top-reader adjudication contract"
```

### Task 2: Promote selected bridge layers into the shared modifier frame

**Files:**
- Modify: `/Users/wuyongnaren/Documents/印度占星/mcp_server.py`
- Test: `/Users/wuyongnaren/Documents/印度占星/tests/test_mcp_strict_workflow_finance.py`
- Test: `/Users/wuyongnaren/Documents/印度占星/tests/test_mcp_strict_workflow_relationship.py`
- Test: `/Users/wuyongnaren/Documents/印度占星/tests/test_mcp_strict_workflow_functional_layer.py`

**Interfaces:**
- Consumes:
  - `present["functional_benefic_malefic"]`
  - `present["ashtakavarga_finance_support"]`
  - `present["wealth_promise_strength"]`
  - marriage route evidence already emitted into `present`
  - `yogi_active` in finance `event_judgement.secondary_context`
- Produces:
  - `multi_reference_reading_summary["modifier_frame"]`
  - `adjudication_stages["manifestation"]["bridge_modifiers"]`

- [ ] **Step 1: Write the failing tests**

Add focused bridge promotion assertions:

```python
def test_finance_summary_modifier_frame_includes_yogi_and_ashtakavarga_only_as_modifiers() -> None:
    strict = mcp_server._collect_strict_evidence("finance", modules)
    modifier = strict["multi_reference_reading_summary"]["modifier_frame"]
    assert "functional_benefic_malefic" in modifier
    assert modifier["ashtakavarga_finance_support"]["source"] == "ashtakavarga_house_scores_bridge_v1"
    assert modifier["yogi_support"]["role"] == "modifier_only"
```

```python
def test_relationship_summary_modifier_frame_surfaces_label_lift_related_modifiers() -> None:
    strict = mcp_server._collect_strict_evidence("relationship", modules)
    modifier = strict["multi_reference_reading_summary"]["modifier_frame"]
    assert "functional_benefic_malefic" in modifier
    assert "manifestation_split" in modifier
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python3 -m pytest tests/test_mcp_strict_workflow_finance.py tests/test_mcp_strict_workflow_relationship.py tests/test_mcp_strict_workflow_functional_layer.py -k "modifier_frame or yogi or manifestation_split" -q
```

Expected: FAIL with missing modifier-frame keys.

- [ ] **Step 3: Write the minimal implementation**

Extend the summary helpers in `mcp_server.py`:

```python
def _summary_modifier_frame(route: str, present: Dict[str, Any]) -> Dict[str, Any]:
    frame = {
        "functional_benefic_malefic": present.get("functional_benefic_malefic"),
        "shadbala": present.get("shadbala"),
        "argala_support": present.get("argala_support"),
    }
    if route == "finance":
        frame["ashtakavarga_finance_support"] = present.get("ashtakavarga_finance_support")
        frame["yogi_support"] = {
            "role": "modifier_only",
            "value": present.get("wealth_promise_strength"),
        }
    if route == "relationship":
        frame["manifestation_split"] = {
            "role": "modifier_only",
            "signals": [
                "relationship_formation",
                "legal_marriage",
                "public_formalization",
            ],
        }
    return frame
```

Do not create new calculators here; only repackage current evidence and known route-specific bridge metadata.

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python3 -m pytest tests/test_mcp_strict_workflow_finance.py tests/test_mcp_strict_workflow_relationship.py tests/test_mcp_strict_workflow_functional_layer.py -k "modifier_frame or yogi or manifestation_split" -q
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add mcp_server.py tests/test_mcp_strict_workflow_finance.py tests/test_mcp_strict_workflow_relationship.py tests/test_mcp_strict_workflow_functional_layer.py
git commit -m "feat: promote selected bridge layers into shared modifiers"
```

### Task 3: Compact and expose the new contract through `jyotish_engine.py`

**Files:**
- Modify: `/Users/wuyongnaren/Documents/印度占星/scripts/jyotish_engine.py`
- Test: `/Users/wuyongnaren/Documents/印度占星/tests/test_cli_smoke.py`
- Test: `/Users/wuyongnaren/Documents/印度占星/tests/test_vedastro_official_full_snapshot.py`

**Interfaces:**
- Consumes:
  - strict workflow contracts embedded in `modules`
- Produces:
  - `_compact_strict_workflow_contract(strict: Dict[str, Any]) -> Dict[str, Any]`
  - `ai_prompt_pack["evidence_snapshot"]["strict_workflow_contracts"][route]["adjudication_stages"]`
  - `ai_prompt_pack["evidence_snapshot"]["strict_workflow_contracts"][route]["multi_reference_reading_summary"]`

- [ ] **Step 1: Write the failing tests**

Add prompt-pack expectations:

```python
def test_full_reading_prompt_pack_carries_adjudication_stages_and_multi_reference_summary() -> None:
    result = run_full_reading(...)
    strict = result["ai_prompt_pack"]["evidence_snapshot"]["strict_workflow_contracts"]["career"]
    assert "adjudication_stages" in strict
    assert "multi_reference_reading_summary" in strict
    assert "modifier_frame" in strict["multi_reference_reading_summary"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python3 -m pytest tests/test_cli_smoke.py tests/test_vedastro_official_full_snapshot.py -k "adjudication_stages or multi_reference_reading_summary" -q
```

Expected: FAIL with missing keys in compact strict workflow contract or evidence snapshot.

- [ ] **Step 3: Write the minimal implementation**

Extend the strict contract compactor in `scripts/jyotish_engine.py`:

```python
def _compact_strict_workflow_contract(strict):
    return {
        "confidence_cap": strict.get("confidence_cap"),
        "blocked": strict.get("blocked"),
        "blocked_items": strict.get("blocked_items") or [],
        "conflicts": strict.get("conflicts") or [],
        "official_primary_evidence": strict.get("official_primary_evidence") or {},
        "local_supplemental_evidence": strict.get("local_supplemental_evidence") or {},
        "adjudication_stages": strict.get("adjudication_stages") or {},
        "multi_reference_reading_summary": strict.get("multi_reference_reading_summary") or {},
        "verdict": strict.get("verdict"),
        "dominant_label": strict.get("dominant_label"),
        "main_conflicts": strict.get("main_conflicts") or [],
    }
```

Also ensure the prompt-pack evidence snapshot reuses this compacted form instead of recomputing anything heavy.

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python3 -m pytest tests/test_cli_smoke.py tests/test_vedastro_official_full_snapshot.py -k "adjudication_stages or multi_reference_reading_summary" -q
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/jyotish_engine.py tests/test_cli_smoke.py tests/test_vedastro_official_full_snapshot.py
git commit -m "feat: expose top-reader contract in prompt pack"
```

### Task 4: Surface the reshaped contract in API outputs with no extra heavy recompute

**Files:**
- Modify: `/Users/wuyongnaren/Documents/印度占星/scripts/jyotish_api_server.py`
- Test: `/Users/wuyongnaren/Documents/印度占星/tests/test_api_server_security.py`
- Test: `/Users/wuyongnaren/Documents/印度占星/tests/test_historical_event_backtest.py`

**Interfaces:**
- Consumes:
  - prompt-pack `evidence_snapshot`
  - existing consultation workflow contract
  - strict workflow contract summary
- Produces:
  - consultation/high-rigor API outputs that include:
    - `adjudication_stages`
    - `multi_reference_reading_summary`
    - `verdict`
    - `dominant_label`
    - `main_conflicts`

- [ ] **Step 1: Write the failing tests**

Add API-level shape assertions:

```python
def test_consultation_workflow_passes_through_top_reader_contract(monkeypatch) -> None:
    result = handler._compute_consultation_workflow(payload)
    guided = result["guided_topics"][0]
    assert "adjudication_stages" in guided
    assert "multi_reference_reading_summary" in guided
```

```python
def test_high_rigor_summary_passes_through_multi_reference_summary(monkeypatch) -> None:
    summary = handler._high_rigor_vedastro_official_summary(prompt_official, range_scan, range_metadata)
    assert "multi_reference_reading_summary" in summary
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python3 -m pytest tests/test_api_server_security.py tests/test_historical_event_backtest.py -k "top_reader_contract or multi_reference_reading_summary" -q
```

Expected: FAIL with missing API passthrough keys.

- [ ] **Step 3: Write the minimal implementation**

Update `scripts/jyotish_api_server.py` to reuse existing prompt-pack or strict contract nodes:

```python
strict_contract = prompt_official.get("strict_workflow_contracts", {}).get(route_key, {})
summary["adjudication_stages"] = strict_contract.get("adjudication_stages") or {}
summary["multi_reference_reading_summary"] = strict_contract.get("multi_reference_reading_summary") or {}
summary["verdict"] = strict_contract.get("verdict")
summary["dominant_label"] = strict_contract.get("dominant_label")
summary["main_conflicts"] = strict_contract.get("main_conflicts") or strict_contract.get("conflicts") or []
```

Where guided topic objects are built, attach the same already-computed contract by reference or compact copy; do not call full-reading again.

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python3 -m pytest tests/test_api_server_security.py tests/test_historical_event_backtest.py -k "top_reader_contract or multi_reference_reading_summary" -q
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/jyotish_api_server.py tests/test_api_server_security.py tests/test_historical_event_backtest.py
git commit -m "feat: surface top-reader adjudication contract in api outputs"
```

### Task 5: Keep the frontend and user-facing surfaces simple while consuming the richer contract

**Files:**
- Modify: `/Users/wuyongnaren/Documents/印度占星/jyotish-app/main.js`
- Modify: `/Users/wuyongnaren/Documents/印度占星/jyotish-app/ai-chat.js`
- Test: `/Users/wuyongnaren/Documents/印度占星/tests/test_frontend_productization.py`

**Interfaces:**
- Consumes:
  - consultation workflow output
  - prompt-pack evidence snapshot
  - compact strict contract
- Produces:
  - visible simple user summaries
  - AI chat context that includes the new top-reader contract

- [ ] **Step 1: Write the failing tests**

Add frontend token tests:

```python
def test_ai_chat_and_complete_reading_surface_top_reader_contract_tokens() -> None:
    main = read_main_js()
    ai_chat = read_ai_chat_js()
    assert "multi_reference_reading_summary" in main
    assert "adjudication_stages" in main
    assert "multi_reference_reading_summary" in ai_chat
    assert "adjudication_stages" in ai_chat
```

Also add one test that the UI still prefers compact summaries rather than dumping raw full evidence.

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python3 -m pytest tests/test_frontend_productization.py -k "top_reader_contract or multi_reference_reading_summary or adjudication_stages" -q
```

Expected: FAIL with missing frontend references to the new contract.

- [ ] **Step 3: Write the minimal implementation**

Update frontend readers to expose only compact user-facing summaries and AI context:

```javascript
const topReaderContract = chartData?.ai_prompt_pack?.evidence_snapshot?.strict_workflow_contracts?.[routeKey] || {};
const adjudicationStages = topReaderContract.adjudication_stages || {};
const multiReferenceSummary = topReaderContract.multi_reference_reading_summary || {};
```

Use these to:

- show a compact “how this conclusion was formed” section
- append structured context to AI chat
- avoid rendering the full raw evidence tree unless already needed in an audit panel

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python3 -m pytest tests/test_frontend_productization.py -k "top_reader_contract or multi_reference_reading_summary or adjudication_stages" -q
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add jyotish-app/main.js jyotish-app/ai-chat.js tests/test_frontend_productization.py
git commit -m "feat: consume top-reader adjudication contract in frontend"
```

### Task 6: Run the focused regression bundle and then the broader verification pass

**Files:**
- Modify: `/Users/wuyongnaren/Documents/印度占星/progress.md`

**Interfaces:**
- Consumes:
  - all modified code from Tasks 1-5
- Produces:
  - recorded verification summary in `progress.md`

- [ ] **Step 1: Run the focused contract regressions**

Run:

```bash
python3 -m pytest \
  tests/test_mcp_strict_workflow_career.py \
  tests/test_mcp_strict_workflow_relationship.py \
  tests/test_mcp_strict_workflow_finance.py \
  tests/test_mcp_strict_workflow_functional_layer.py \
  tests/test_cli_smoke.py \
  tests/test_vedastro_official_full_snapshot.py \
  tests/test_api_server_security.py \
  tests/test_historical_event_backtest.py \
  tests/test_frontend_productization.py \
  -k "adjudication_stages or multi_reference_reading_summary or top_reader_contract or modifier_frame" -q
```

Expected: PASS

- [ ] **Step 2: Run the broader targeted verification**

Run:

```bash
python3 -m pytest tests/test_mcp_strict_workflow_career.py tests/test_mcp_strict_workflow_relationship.py tests/test_mcp_strict_workflow_finance.py tests/test_api_server_security.py tests/test_cli_smoke.py tests/test_frontend_productization.py -q
```

Expected: PASS

- [ ] **Step 3: Update `progress.md` with the landed contract and verification notes**

Add an entry similar to:

```markdown
- 2026-06-30 Top-reader adjudication contract landed:
  - shared `promise -> activation -> manifestation -> label`
  - `multi_reference_reading_summary`
  - bridge promotion kept modifier-only
  - prompt-pack/API/frontend all consume the same compact contract
  - focused and targeted regressions passed
```

- [ ] **Step 4: Run diff hygiene checks**

Run:

```bash
git diff --check
```

Expected: no output

- [ ] **Step 5: Commit**

```bash
git add progress.md
git commit -m "docs: record top-reader adjudication verification"
```

## Self-Review

### Spec coverage

- Shared four-stage skeleton: covered by Task 1
- Multi-reference summary: covered by Tasks 1, 3, 4, and 5
- Selected bridge promotion: covered by Task 2
- Prompt-pack/API/frontend consumption: covered by Tasks 3, 4, and 5
- Compute minimization and reuse constraints: enforced in every task through existing-contract reuse and no new engine work

### Placeholder scan

- No `TODO`, `TBD`, or “implement later” placeholders remain.
- Each task includes exact files, exact commands, and exact expected behavior.

### Type consistency

- `adjudication_stages` and `multi_reference_reading_summary` are introduced first in `mcp_server.py`, then compacted in `jyotish_engine.py`, then consumed in `jyotish_api_server.py` and frontend.
- `verdict`, `dominant_label`, and `main_conflicts` are named consistently across all tasks.

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-06-30-top-reader-adjudication.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
