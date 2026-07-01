# VedAstro Official Hard-Override Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `relationship`, `career`, and `wealth` default workflows enforce `VedAstro official -> local supplemental -> local fallback`, with honest `blocked`, `conflicts`, and `confidence_cap` output.

**Architecture:** Reuse the existing `vedastro_evidence_orchestrator`, `vedastro_priority`, `mcp_server` strict evidence collectors, `jyotish_engine`, and `jyotish_api_server` rather than creating a second workflow. Promote official-first evidence into a shared strict contract, then expose that same contract through API and report surfaces.

**Tech Stack:** Python standard library, existing MCP strict workflow, pytest, existing API/frontend static tests.

## Global Constraints

- Official VedAstro data is primary when available.
- Local modules may supplement, cross-check, or fallback, but may not silently overwrite official values.
- Timing and event outputs must keep `Vimshottari + Narayana` dual-track rigor.
- Relationship must keep `D9 + UL`.
- Career must keep `D10 + A10`.
- Wealth must keep `D2 / D11`.
- Functional Benefic/Malefic must remain explicit in high-rigor outputs.
- New behavior must be introduced with failing tests first.
- Do not create a parallel orchestration stack when existing files can be extended safely.

---

### Task 1: Add Red Tests For The Shared Official-First Strict Contract

**Files:**
- Modify: `tests/test_mcp_strict_workflow_relationship.py`
- Modify: `tests/test_mcp_strict_workflow_career.py`
- Modify: `tests/test_mcp_strict_workflow_finance.py`
- Modify: `tests/test_historical_event_backtest.py`

**Interfaces:**
- Produces strict fields:
  - `official_primary_evidence: dict`
  - `local_supplemental_evidence: dict`
  - `fallback_used: list[str]`
  - `blocked_items: list[str]`
  - `conflicts: list[dict]`
  - `confidence_cap: str`

- [ ] **Step 1: Write the failing relationship test**

```python
def test_relationship_strict_contract_exposes_official_primary_and_local_supplemental_layers() -> None:
    result = _base_relationship_result()
    result["modules"]["source_priority"] = {"mode": "vedastro_official_primary"}
    result["modules"]["vedastro_official_full_snapshot"] = {
        "status": "partial",
        "available": True,
        "official_chart": {"planets": {"Sun": {}}, "ascendant": {"sign": "Leo"}},
        "section_statuses": {"chart_core": "ok", "dasha_all": "ok", "events_overview": "partial"},
    }

    strict = _collect_strict_evidence("relationship", result)

    assert strict["official_primary_evidence"]["chart_core"]["status"] == "ok"
    assert strict["local_supplemental_evidence"]["upapada_lagna"]["role"] == "required_local_supplement"
    assert isinstance(strict["blocked_items"], list)
    assert isinstance(strict["fallback_used"], list)
    assert isinstance(strict["conflicts"], list)
```

- [ ] **Step 2: Write the failing career and finance tests**

```python
def test_career_strict_contract_marks_a10_as_local_supplement_to_official_primary() -> None:
    result = _base_career_result()
    result["modules"]["source_priority"] = {"mode": "vedastro_official_primary"}
    result["modules"]["vedastro_official_full_snapshot"] = {
        "status": "partial",
        "available": True,
        "official_chart": {"planets": {"Sun": {}}, "ascendant": {"sign": "Leo"}},
        "section_statuses": {"chart_core": "ok", "dasha_all": "ok"},
    }
    strict = _collect_strict_evidence("career", result)
    assert strict["official_primary_evidence"]["dasha"]["status"] == "ok"
    assert strict["local_supplemental_evidence"]["a10_karma_pada"]["role"] == "required_local_supplement"


def test_finance_strict_contract_surfaces_official_block_and_local_fallback_usage() -> None:
    result = {"modules": {"source_priority": {"mode": "local_fallback_official_blocked"}}}
    strict = _collect_strict_evidence("finance", result)
    assert "official_primary_chart_blocked" in strict["blocked_items"]
    assert isinstance(strict["fallback_used"], list)
```

- [ ] **Step 3: Write the failing backtest test**

```python
def test_backtest_carries_conflicts_and_blocked_items_from_strict_contract(monkeypatch) -> None:
    def fake_strict_workflow(**kwargs):
        packet = _strict_packet("career", verdict="high_probability_window", dominant_label="career_status", score=84)
        packet["strict_workflow"]["blocked_items"] = ["official_event_radar_partial"]
        packet["strict_workflow"]["conflicts"] = [{"type": "official_local_dasha_conflict"}]
        return packet

    monkeypatch.setattr(backtest.mcp_server, "strict_workflow", fake_strict_workflow)
    report = backtest.build_report(_payload([{"id": "career_turn_2019", "date": "2019-12-15", "domain": "career"}]))
    assert report["events"][0]["evidence"]["blocked_items"] == ["official_event_radar_partial"]
    assert report["events"][0]["evidence"]["conflicts"] == [{"type": "official_local_dasha_conflict"}]
```

- [ ] **Step 4: Run tests to verify they fail**

Run:
`python3 -m pytest tests/test_mcp_strict_workflow_relationship.py tests/test_mcp_strict_workflow_career.py tests/test_mcp_strict_workflow_finance.py tests/test_historical_event_backtest.py -k "strict_contract or conflicts_and_blocked_items" -q`

Expected: FAIL because the strict contract fields do not yet exist.

### Task 2: Implement Shared Official-First Strict Contract In MCP Strict Workflow

**Files:**
- Modify: `mcp_server.py`
- Test: `tests/test_mcp_strict_workflow_relationship.py`
- Test: `tests/test_mcp_strict_workflow_career.py`
- Test: `tests/test_mcp_strict_workflow_finance.py`

**Interfaces:**
- Produces:
  - `_build_official_primary_evidence(route: str, modules: dict, present: dict) -> dict`
  - `_build_local_supplemental_evidence(route: str, present: dict) -> dict`
  - `_build_fallback_and_blocked(route: str, present: dict, missing: list[str]) -> tuple[list[str], list[str]]`
  - `_build_conflicts(route: str, present: dict, missing: list[str]) -> list[dict]`

- [ ] **Step 1: Implement helper skeletons in `mcp_server.py`**

```python
def _build_official_primary_evidence(route: str, modules: Dict[str, Any], present: Dict[str, Any]) -> Dict[str, Any]:
    snapshot = present.get("vedastro_official_snapshot") or {}
    section_statuses = snapshot.get("section_statuses") or {}
    base = {
        "chart_core": {"source": "vedastro_official", "status": section_statuses.get("chart_core", "blocked")},
        "dasha": {"source": "vedastro_official", "status": section_statuses.get("dasha_all", "blocked")},
        "event_radar": {"source": "vedastro_official", "status": section_statuses.get("events_overview", "blocked")},
    }
    if route == "relationship":
        base["d9"] = {"source": "vedastro_official", "status": section_statuses.get("varga_d9", "unknown")}
    elif route == "career":
        base["d10"] = {"source": "vedastro_official", "status": section_statuses.get("varga_d10", "unknown")}
    elif route == "finance":
        base["d2_d11"] = {"source": "vedastro_official", "status": section_statuses.get("varga_d2_d11", "unknown")}
    return base
```

- [ ] **Step 2: Implement local supplemental mapping**

```python
def _build_local_supplemental_evidence(route: str, present: Dict[str, Any]) -> Dict[str, Any]:
    if route == "relationship":
        keys = ("upapada_lagna", "darakaraka", "narayana_current", "functional_benefic_malefic")
    elif route == "career":
        keys = ("a10_karma_pada", "narayana_current", "functional_benefic_malefic")
    else:
        keys = ("wealth_promise_strength", "narayana_current", "functional_benefic_malefic")
    return {
        key: {
            "role": "required_local_supplement",
            "present": bool(present.get(key)),
        }
        for key in keys
    }
```

- [ ] **Step 3: Implement blocked, fallback, and conflict derivation**

```python
def _build_fallback_and_blocked(route: str, present: Dict[str, Any], missing: List[str]) -> tuple[List[str], List[str]]:
    blocked_items: List[str] = []
    fallback_used: List[str] = []
    official = present.get("vedastro_official_snapshot") or {}
    if official.get("level") != "primary":
        blocked_items.append("official_primary_chart_blocked")
        fallback_used.append("local_chart_fallback")
    if "external_activation" in present and (present.get("external_activation") or {}).get("level") == "missing_required_external_radar":
        blocked_items.append("official_event_radar_partial")
    for key in missing:
        blocked_items.append(f"missing_required_{key}")
    return fallback_used, blocked_items


def _build_conflicts(route: str, present: Dict[str, Any], missing: List[str]) -> List[Dict[str, Any]]:
    conflicts: List[Dict[str, Any]] = []
    dignity = present.get("dignity_guardrail") or {}
    if dignity.get("status") == "conflict":
        conflicts.append({
            "type": "official_local_divisional_conflict",
            "primary_source": "vedastro_official",
            "supplemental_source": "local_module",
            "impact": "interpretation",
            "resolution": "keep_official_primary_and_downgrade_confidence",
            "details": {"dignity_guardrail": dignity},
        })
    return conflicts
```

- [ ] **Step 4: Attach the new contract fields to each strict route**

```python
strict["official_primary_evidence"] = _build_official_primary_evidence(route, modules, present)
strict["local_supplemental_evidence"] = _build_local_supplemental_evidence(route, present)
strict["fallback_used"], strict["blocked_items"] = _build_fallback_and_blocked(route, present, missing)
strict["conflicts"] = _build_conflicts(route, present, missing)
```

- [ ] **Step 5: Run tests to verify they pass**

Run:
`python3 -m pytest tests/test_mcp_strict_workflow_relationship.py tests/test_mcp_strict_workflow_career.py tests/test_mcp_strict_workflow_finance.py tests/test_historical_event_backtest.py -k "strict_contract or conflicts_and_blocked_items" -q`

Expected: PASS for the new contract tests.

### Task 3: Promote Official Snapshot Section Status Into Shared Orchestration Metadata

**Files:**
- Modify: `scripts/vedastro_evidence_orchestrator.py`
- Modify: `scripts/vedastro_priority.py`
- Modify: `tests/test_vedastro_evidence_orchestrator.py`
- Modify: `tests/test_vedastro_official_full_snapshot.py`

**Interfaces:**
- Produces:
  - `source_metadata.official_section_statuses`
  - `source_metadata.theme_requirements`
  - `official_snapshot_evidence(...).section_statuses`

- [ ] **Step 1: Write the failing orchestrator test**

```python
def test_vedastro_orchestrator_surfaces_official_section_statuses_and_theme_requirements(monkeypatch) -> None:
    from scripts import vedastro_evidence_orchestrator as orchestrator

    monkeypatch.setattr(orchestrator, "run_official_full_snapshot_for_case", lambda *args, **kwargs: {
        "status": "partial",
        "available": True,
        "official_chart": {"planets": {"Sun": {}}, "ascendant": {"sign": "Leo"}},
        "section_statuses": {"chart_core": "ok", "dasha_all": "ok", "events_overview": "partial"},
        "source_metadata": {},
    })
    monkeypatch.setattr(orchestrator, "run_range_scan_for_case", lambda *args, **kwargs: {
        "status": "ok",
        "available": True,
        "event_count": 1,
        "evidence_ledger": [],
    })

    result = orchestrator.orchestrate_vedastro_evidence({"year": REDACTED_YEAR, "month": 4, "day": 17, "hour": 14, "minute": 49, "lat": 36.42, "lon": 114.2, "tz": 8}, route="relationship", reference_date="2026-06-29")
    assert result["source_metadata"]["official_section_statuses"]["dasha_all"] == "ok"
    assert result["source_metadata"]["theme_requirements"]["route"] == "relationship"
```

- [ ] **Step 2: Run test to verify it fails**

Run:
`python3 -m pytest tests/test_vedastro_evidence_orchestrator.py -k official_section_statuses -q`

Expected: FAIL because the metadata keys are missing.

- [ ] **Step 3: Implement minimal metadata propagation**

```python
official_section_statuses = official_full_snapshot.get("section_statuses") if isinstance(official_full_snapshot, dict) else {}
theme_requirements = {
    "route": route,
    "domains": domains,
    "requires_dual_dasha": True,
}
```

Add both into the orchestrator `source_metadata` and keep `official_snapshot_evidence()` returning `section_statuses`.

- [ ] **Step 4: Run tests to verify they pass**

Run:
`python3 -m pytest tests/test_vedastro_evidence_orchestrator.py tests/test_vedastro_official_full_snapshot.py -k "official_section_statuses or official_full_snapshot" -q`

Expected: PASS for the new metadata contract.

### Task 4: Surface The Shared Contract Through API And Report Payloads

**Files:**
- Modify: `scripts/jyotish_api_server.py`
- Modify: `scripts/jyotish_engine.py`
- Modify: `tests/test_api_server_security.py`

**Interfaces:**
- Produces:
  - API theme outputs that include `official_primary_evidence`, `local_supplemental_evidence`, `fallback_used`, `blocked_items`, `conflicts`
  - prompt/report payloads that carry the same structure

- [ ] **Step 1: Write the failing API test**

```python
def test_high_rigor_workflow_plan_only_exposes_official_hard_override_contract() -> None:
    handler = _handler()
    result = handler._high_rigor_workflow_plan_only(
        {"year": REDACTED_YEAR, "month": 4, "day": 17, "hour": 14, "minute": 49, "lat": 36.42, "lon": 114.2, "tz": 8},
        ["career", "marriage", "wealth"],
        [],
    )
    assert result["source_priority"]["mode"] == "vedastro_official_snapshot_first"
    assert result["execution_plan"][-1] == "return_official_primary_supplemental_fallback_conflict_contract"
```

- [ ] **Step 2: Run test to verify it fails**

Run:
`python3 -m pytest tests/test_api_server_security.py -k hard_override_contract -q`

Expected: FAIL because the execution plan and API contract are not yet updated.

- [ ] **Step 3: Implement API/report passthrough**

```python
result["contract"] = {
    "official_primary_evidence": strict.get("official_primary_evidence") if isinstance(strict, dict) else {},
    "local_supplemental_evidence": strict.get("local_supplemental_evidence") if isinstance(strict, dict) else {},
    "fallback_used": strict.get("fallback_used") if isinstance(strict, dict) else [],
    "blocked_items": strict.get("blocked_items") if isinstance(strict, dict) else [],
    "conflicts": strict.get("conflicts") if isinstance(strict, dict) else [],
}
```

Update prompt/report payload builders to include the same keys when strict evidence exists.

- [ ] **Step 4: Run test to verify it passes**

Run:
`python3 -m pytest tests/test_api_server_security.py -k hard_override_contract -q`

Expected: PASS.

### Task 5: Verify The Closed Path And Update Project Logs

**Files:**
- Modify: `progress.md`
- Modify: `findings.md`

**Interfaces:**
- Produces:
  - final verification log for the official hard-override path

- [ ] **Step 1: Run focused strict-workflow verification**

Run:
`python3 -m pytest tests/test_mcp_strict_workflow_relationship.py tests/test_mcp_strict_workflow_career.py tests/test_mcp_strict_workflow_finance.py tests/test_historical_event_backtest.py -q`

Expected: PASS.

- [ ] **Step 2: Run orchestration verification**

Run:
`python3 -m pytest tests/test_vedastro_evidence_orchestrator.py tests/test_vedastro_official_full_snapshot.py tests/test_vedastro_python_bridge.py -q`

Expected: PASS.

- [ ] **Step 3: Run API/static verification**

Run:
`python3 -m pytest tests/test_api_server_security.py tests/test_frontend_productization.py -k "vedastro or hard_override_contract or source_priority" -q`

Expected: PASS.

- [ ] **Step 4: Update project logs**

Record:
- files changed
- official-first contract now enforced where implemented
- remaining blocked boundaries
- exact verification commands and results

## Self-Review

- Spec coverage: official-first authority, shared contract, conflict honesty, blocked honesty, API/report propagation, and verification each map to a task.
- Placeholder scan: no TBD/TODO placeholders remain.
- Type consistency: the same contract keys are used across strict workflow, backtest, API, and report surfaces.
