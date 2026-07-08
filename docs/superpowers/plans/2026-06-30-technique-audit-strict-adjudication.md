# Technique Audit Strict Adjudication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the existing `Technique Audit Table` a required compact gate inside strict adjudication for `career`, `relationship`, and `finance`.

**Architecture:** Reuse the current strict workflow contracts in `mcp_server.py` and the current prompt-pack audit table in `scripts/jyotish_engine.py`. Add one compact shared audit summary, then surface it through the existing engine/API/frontend layers without adding new compute-heavy logic.

**Tech Stack:** Python, existing strict workflow collectors, existing prompt-pack contract, pytest, existing frontend static contract tests.

## Global Constraints

- Reuse current `Technique Audit Table`; do not create a second audit table system.
- Do not add new heavy computation or new external requests.
- Keep `career`, `relationship`, and `finance` route-specific gates intact.
- Preserve honesty boundaries: `blocked`, `fallback_used`, `conflicts`, and `confidence_cap` must remain explicit.
- Functional benefic/malefic must remain visible as a first-class high-rigor gate.

---

### Task 1: Add compact technique audit summary to strict workflow contracts

**Files:**
- Modify: `<repo>/mcp_server.py`
- Test: `<repo>/tests/test_mcp_strict_workflow_career.py`
- Test: `<repo>/tests/test_mcp_strict_workflow_relationship.py`
- Test: `<repo>/tests/test_mcp_strict_workflow_finance.py`

**Interfaces:**
- Consumes:
  - `strict["present_evidence"]`
  - `strict["official_primary_evidence"]`
  - `strict["local_supplemental_evidence"]`
  - `strict["fallback_used"]`
  - `strict["blocked_items"]`
  - `strict["conflicts"]`
- Produces:
  - `strict["technique_audit_summary"]`
  - `strict["multi_reference_reading_summary"]["audit_gate_frame"]`

- [ ] **Step 1: Write the failing tests**

```python
def test_career_strict_contract_exposes_compact_technique_audit_summary() -> None:
    strict = _collect_strict_evidence("career", _sample_result())
    audit = strict["technique_audit_summary"]
    assert audit["functional_benefic_malefic"]["gate"] == "hard"
    assert audit["relevant_vargas"]["gate"] == "hard"
    assert audit["vimshottari_narayana_crosscheck"]["gate"] == "hard"
    assert audit["source_priority_boundary"]["fallback_used"] == strict["fallback_used"]
```

```python
def test_relationship_multi_reference_summary_carries_audit_gate_frame() -> None:
    strict = _collect_strict_evidence("relationship", _sample_result())
    frame = strict["multi_reference_reading_summary"]["audit_gate_frame"]
    assert frame["functional_benefic_malefic"]["used"] in {True, False}
    assert frame["source_priority_boundary"]["blocked_items"] == strict["blocked_items"]
```

```python
def test_finance_strict_contract_compact_audit_marks_dual_dasha_gate() -> None:
    strict = _collect_strict_evidence("finance", {"modules": {"source_priority": {"mode": "local_fallback_official_blocked"}}})
    audit = strict["technique_audit_summary"]
    assert audit["vimshottari_narayana_crosscheck"]["gate"] == "hard"
    assert "official_primary_chart_blocked" in audit["source_priority_boundary"]["blocked_items"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python3 -m pytest tests/test_mcp_strict_workflow_career.py tests/test_mcp_strict_workflow_relationship.py tests/test_mcp_strict_workflow_finance.py -k "compact_technique_audit_summary or audit_gate_frame or dual_dasha_gate" -q
```

Expected: FAIL with missing `technique_audit_summary` or `audit_gate_frame`.

- [ ] **Step 3: Write minimal implementation**

Add compact builders in `mcp_server.py`:

```python
def _route_varga_gate_keys(route: str) -> list[str]:
    if route == "career":
        return ["d10_dasamsa", "a10_karma_pada", "amatyakaraka", "karakamsha"]
    if route == "relationship":
        return ["d9_navamsa", "upapada_lagna", "darakaraka", "vivah_saham"]
    if route == "finance":
        return ["d2_hora", "d10_dasamsa", "shadbala", "ashtakavarga_house_scores"]
    return []

def _build_technique_audit_summary(route: str, strict: Dict[str, Any]) -> Dict[str, Any]:
    present = strict.get("present_evidence") or {}
    official = strict.get("official_primary_evidence") or {}
    local = strict.get("local_supplemental_evidence") or {}
    fallback_used = strict.get("fallback_used") or []
    blocked_items = strict.get("blocked_items") or []
    conflicts = strict.get("conflicts") or []
    return {
        "functional_benefic_malefic": {
            "gate": "hard",
            "used": bool((present.get("functional_benefic_malefic") or {}).get("status") == "used"),
            "note": (present.get("functional_benefic_malefic") or {}).get("effect_on_confidence"),
        },
        "relevant_vargas": {
            "gate": "hard",
            "required_keys": _route_varga_gate_keys(route),
            "present_keys": [key for key in _route_varga_gate_keys(route) if present.get(key)],
        },
        "vimshottari_narayana_crosscheck": {
            "gate": "hard",
            "used": bool(present.get("vimshottari_current")) and bool(present.get("narayana_current")),
            "required_timing_systems": ["Vimshottari", "Narayana"],
        },
        "source_priority_boundary": {
            "gate": "boundary",
            "official": official,
            "local": local,
            "fallback_used": fallback_used,
            "blocked_items": blocked_items,
            "conflicts": conflicts,
        },
    }
```

Attach it in `_attach_top_reader_contract(...)` and mirror it into `multi_reference_reading_summary["audit_gate_frame"]`.

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python3 -m pytest tests/test_mcp_strict_workflow_career.py tests/test_mcp_strict_workflow_relationship.py tests/test_mcp_strict_workflow_finance.py -k "compact_technique_audit_summary or audit_gate_frame or dual_dasha_gate" -q
```

Expected: PASS

### Task 2: Compact and expose the audit summary through full-reading and prompt pack

**Files:**
- Modify: `<repo>/scripts/jyotish_engine.py`
- Test: `<repo>/tests/test_cli_smoke.py`

**Interfaces:**
- Consumes:
  - `modules[*_strict_evidence]`
- Produces:
  - compact strict contracts that include `technique_audit_summary`

- [ ] **Step 1: Write the failing test**

```python
def test_full_reading_prompt_pack_carries_compact_technique_audit_summary() -> None:
    result = run_engine(...)
    career = result["ai_prompt_pack"]["evidence_snapshot"]["strict_workflow_contracts"]["career"]
    assert "technique_audit_summary" in career
    assert career["technique_audit_summary"]["functional_benefic_malefic"]["gate"] == "hard"
    assert "audit_gate_frame" in career["multi_reference_reading_summary"]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest tests/test_cli_smoke.py -k "compact_technique_audit_summary" -q
```

Expected: FAIL with missing `technique_audit_summary`.

- [ ] **Step 3: Write minimal implementation**

Extend `_compact_strict_workflow_contract(...)` in `scripts/jyotish_engine.py`:

```python
"technique_audit_summary": strict.get("technique_audit_summary") or {},
```

Do not recompute anything new; just pass through the strict contract.

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python3 -m pytest tests/test_cli_smoke.py -k "compact_technique_audit_summary" -q
```

Expected: PASS

### Task 3: Surface the same compact audit summary in API outputs

**Files:**
- Modify: `<repo>/scripts/jyotish_api_server.py`
- Test: `<repo>/tests/test_api_server_security.py`

**Interfaces:**
- Consumes:
  - strict contract from prompt pack / official full snapshot
- Produces:
  - API outputs containing `technique_audit_summary`

- [ ] **Step 1: Write the failing tests**

```python
def test_high_rigor_summary_passes_through_compact_technique_audit_summary() -> None:
    result = handler._high_rigor_vedastro_official_summary(chart)
    assert result["technique_audit_summary"]["functional_benefic_malefic"]["gate"] == "hard"
```

```python
def test_consultation_workflow_surfaces_compact_technique_audit_summary(monkeypatch) -> None:
    result = handler._compute_consultation_workflow(payload)
    assert "technique_audit_summary" in result["vedastro_official"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python3 -m pytest tests/test_api_server_security.py -k "compact_technique_audit_summary" -q
```

Expected: FAIL with missing API passthrough key.

- [ ] **Step 3: Write minimal implementation**

In `scripts/jyotish_api_server.py`, add:

```python
'technique_audit_summary': primary_contract.get('technique_audit_summary') or {},
```

to the shared official summary output path.

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python3 -m pytest tests/test_api_server_security.py -k "compact_technique_audit_summary" -q
```

Expected: PASS

### Task 4: Make frontend and AI chat consume the compact audit summary

**Files:**
- Modify: `<repo>/jyotish-app/main.js`
- Modify: `<repo>/jyotish-app/ai-chat.js`
- Test: `<repo>/tests/test_frontend_productization.py`

**Interfaces:**
- Consumes:
  - compact strict contract
- Produces:
  - UI/AI references to `technique_audit_summary`

- [ ] **Step 1: Write the failing test**

```python
def test_frontend_consumes_compact_technique_audit_summary_in_top_reader_contract() -> None:
    main = read("main.js")
    ai_chat = read("ai-chat.js")
    assert "technique_audit_summary" in main
    assert "technique_audit_summary" in ai_chat
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest tests/test_frontend_productization.py -k "compact_technique_audit_summary" -q
```

Expected: FAIL with missing frontend references.

- [ ] **Step 3: Write minimal implementation**

In `main.js` and `ai-chat.js`, read:

```javascript
const techniqueAuditSummary = topReaderContract.technique_audit_summary || {};
```

and surface only a compact summary line, not the whole raw audit table.

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python3 -m pytest tests/test_frontend_productization.py -k "compact_technique_audit_summary" -q
```

Expected: PASS

### Task 5: Run focused regression and update progress

**Files:**
- Modify: `<repo>/progress.md`

**Interfaces:**
- Consumes:
  - all changes from Tasks 1-4
- Produces:
  - verification note in `progress.md`

- [ ] **Step 1: Run focused regression**

Run:

```bash
python3 -m pytest \
  tests/test_mcp_strict_workflow_career.py \
  tests/test_mcp_strict_workflow_relationship.py \
  tests/test_mcp_strict_workflow_finance.py \
  tests/test_cli_smoke.py \
  tests/test_api_server_security.py \
  tests/test_frontend_productization.py \
  -k "compact_technique_audit_summary or audit_gate_frame" -q
```

Expected: PASS

- [ ] **Step 2: Update progress**

Add an entry that the compact `Technique Audit Table` gate now sits inside default strict adjudication.

- [ ] **Step 3: Run diff hygiene**

Run:

```bash
git diff --check
```

Expected: no output

## Self-Review

- Spec coverage: compact strict audit gate, prompt-pack passthrough, API passthrough, frontend consumption, and focused regression are all mapped to tasks.
- Placeholder scan: no TODO/TBD placeholders remain.
- Type consistency: `technique_audit_summary` and `audit_gate_frame` are used consistently across strict contract, prompt pack, API, and frontend.

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-06-30-technique-audit-strict-adjudication.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
