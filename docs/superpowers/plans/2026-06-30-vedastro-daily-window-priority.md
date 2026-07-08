# VedAstro Daily Window Priority Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote official VedAstro range-scan output into reusable day-window evidence that strict career/marriage/wealth workflows can consume directly.

**Architecture:** Reuse the existing `SearchEvents` adapter, orchestration, and strict workflow chain. Add adapter-level day-window aggregation, propagate it through `vedastro_evidence_orchestrator`, expose it inside `external_activation`, and surface it through `life_event_graph_v1` and `full-reading` outputs.

**Tech Stack:** Python 3, existing Jyotish engine, existing VedAstro service adapter, pytest.

## Global Constraints

- Reuse existing `scripts/vedastro_service_adapter.py`, `scripts/vedastro_evidence_orchestrator.py`, `mcp_server.py`, and `scripts/jyotish_engine.py`; do not create a parallel official-event stack.
- Keep official VedAstro as primary raw evidence and local Jyotish modules as adjudication/promise/timing cross-check layers.
- Do not bypass D9/D10/D2/UL/A10/Narayana/Functional Benefic-Malefic gates.
- Preserve existing response cache and free-tier queue logic.
- Keep changes focused on daily-window extraction and propagation, not a month-grid product.

---

### Task 1: Add failing adapter tests for daily-window aggregation

**Files:**
- Modify: `<repo>/tests/test_vedastro_range_scan_replay.py`
- Test: `<repo>/tests/test_vedastro_range_scan_replay.py`

**Interfaces:**
- Consumes: `scripts.vedastro_service_adapter._normalize_range_scan_success(payload, endpoint, request_preview, attempt_count=1, retry_error_codes=None) -> dict`
- Produces: adapter results with `daily_windows: list[dict]` and `top_daily_window: dict | None`

- [ ] **Step 1: Write the failing test**

```python
def test_range_scan_builds_ranked_daily_windows_from_same_day_events() -> None:
    payload = {
        "Status": "Pass",
        "Payload": [
            {
                "Name": "GocharJupiterAspect10th",
                "Description": "Career support transit.",
                "StartTime": "2026-07-18",
                "EndTime": "2026-07-18",
                "EventTags": ["Travel", "General"],
            },
            {
                "Name": "CareerExpansionWindow",
                "Description": "Strong career expansion signal.",
                "StartTime": "2026-07-18",
                "EndTime": "2026-07-18",
                "EventTags": ["career", "transit"],
            },
            {
                "Name": "GocharJupiterAspect10th",
                "Description": "Career support transit.",
                "StartTime": "2026-07-26",
                "EndTime": "2026-07-26",
                "EventTags": ["Travel", "General"],
            },
        ],
    }

    report = vedastro_service_adapter._normalize_range_scan_success(  # noqa: SLF001
        payload,
        "https://api.vedastro.org/api",
        _request_preview("career"),
    )

    assert report["daily_windows"][0]["date"] == "2026-07-18"
    assert report["daily_windows"][0]["event_count"] == 2
    assert report["top_daily_window"]["date"] == "2026-07-18"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_vedastro_range_scan_replay.py::test_range_scan_builds_ranked_daily_windows_from_same_day_events -q`

Expected: FAIL because `daily_windows` / `top_daily_window` are missing.

- [ ] **Step 3: Write minimal implementation**

Add a helper in `scripts/vedastro_service_adapter.py`:

```python
def _build_daily_windows(domain: str, evidence_ledger: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    ...
```

and call it from `_normalize_range_scan_success(...)`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_vedastro_range_scan_replay.py::test_range_scan_builds_ranked_daily_windows_from_same_day_events -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_vedastro_range_scan_replay.py scripts/vedastro_service_adapter.py
git commit -m "feat: add vedastro daily window aggregation"
```

### Task 2: Propagate daily windows through orchestrator

**Files:**
- Modify: `<repo>/scripts/vedastro_evidence_orchestrator.py`
- Modify: `<repo>/tests/test_vedastro_evidence_orchestrator.py`
- Test: `<repo>/tests/test_vedastro_evidence_orchestrator.py`

**Interfaces:**
- Consumes: `run_range_scan_for_case(...) -> dict` with `daily_windows` and `top_daily_window`
- Produces: orchestrator result keys:
  - `daily_windows_by_domain: dict[str, list[dict]]`
  - `top_daily_window_by_domain: dict[str, dict]`

- [ ] **Step 1: Write the failing test**

```python
def test_vedastro_orchestrator_surfaces_daily_windows_by_domain(monkeypatch) -> None:
    from scripts import vedastro_evidence_orchestrator as orchestrator

    monkeypatch.setattr(orchestrator, "run_official_full_snapshot_for_case", lambda *args, **kwargs: {"status": "ok", "source_metadata": {}})
    monkeypatch.setattr(
        orchestrator,
        "run_range_scan_for_case",
        lambda *args, **kwargs: {
            "status": "ok",
            "available": True,
            "event_count": 2,
            "daily_windows": [{"date": "2026-07-18", "domain": "career", "score": 5, "event_count": 2}],
            "top_daily_window": {"date": "2026-07-18", "domain": "career", "score": 5, "event_count": 2},
            "evidence_ledger": [],
        },
    )

    result = orchestrator.orchestrate_vedastro_evidence(
        {"year": 1955, "month": 2, "day": 24, "hour": 19, "minute": 15, "lat": 37.7749, "lon": -122.4194, "tz": 8},
        route="career",
        reference_date="2026-06-30",
    )

    assert result["daily_windows_by_domain"]["career"][0]["date"] == "2026-07-18"
    assert result["top_daily_window_by_domain"]["career"]["score"] == 5
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_vedastro_evidence_orchestrator.py::test_vedastro_orchestrator_surfaces_daily_windows_by_domain -q`

Expected: FAIL because orchestrator does not yet expose these keys.

- [ ] **Step 3: Write minimal implementation**

In `scripts/vedastro_evidence_orchestrator.py`, collect from each domain report:

```python
daily_windows_by_domain[domain] = report.get("daily_windows") or []
if isinstance(report.get("top_daily_window"), dict):
    top_daily_window_by_domain[domain] = report["top_daily_window"]
```

and return them in the final payload.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_vedastro_evidence_orchestrator.py::test_vedastro_orchestrator_surfaces_daily_windows_by_domain -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/vedastro_evidence_orchestrator.py tests/test_vedastro_evidence_orchestrator.py
git commit -m "feat: propagate vedastro daily windows through orchestrator"
```

### Task 3: Promote daily windows into strict workflow external activation

**Files:**
- Modify: `<repo>/mcp_server.py`
- Modify: `<repo>/tests/test_mcp_strict_workflow_career.py`
- Modify: `<repo>/tests/test_mcp_strict_workflow_relationship.py`
- Modify: `<repo>/tests/test_mcp_strict_workflow_finance.py`
- Test: same files

**Interfaces:**
- Consumes: `modules.vedastro_range_scan_result.daily_windows` / `top_daily_window`
- Produces: `present_evidence.external_activation.daily_windows` and `present_evidence.external_activation.top_daily_window`

- [ ] **Step 1: Write the failing test**

```python
def test_relationship_external_activation_exposes_top_daily_window() -> None:
    result = {
        "modules": {
            "vedastro_range_scan_result": {
                "backend": "vedastro_service_adapter_candidate",
                "status": "ok",
                "operation": "range_scan",
                "domain": "marriage",
                "evidence_ledger": [],
                "daily_windows": [{"date": "2026-08-02", "domain": "marriage", "score": 5, "event_count": 2}],
                "top_daily_window": {"date": "2026-08-02", "domain": "marriage", "score": 5, "event_count": 2},
                "source_metadata": {},
            },
        }
    }

    strict = _collect_strict_evidence("relationship", result)
    external = strict["present_evidence"]["external_activation"]

    assert external["top_daily_window"]["date"] == "2026-08-02"
    assert external["daily_windows"][0]["score"] == 5
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_mcp_strict_workflow_relationship.py::test_relationship_external_activation_exposes_top_daily_window -q`

Expected: FAIL because `external_activation` does not yet carry day-window fields.

- [ ] **Step 3: Write minimal implementation**

Extend `_derive_external_activation_support(...)` in `mcp_server.py` to read:

```python
daily_windows = adapter_result.get("daily_windows") or []
top_daily_window = adapter_result.get("top_daily_window")
```

and include them in the returned dict.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_mcp_strict_workflow_relationship.py::test_relationship_external_activation_exposes_top_daily_window -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add mcp_server.py tests/test_mcp_strict_workflow_relationship.py tests/test_mcp_strict_workflow_career.py tests/test_mcp_strict_workflow_finance.py
git commit -m "feat: expose vedastro daily windows in strict workflow"
```

### Task 4: Surface official day windows in life event graph

**Files:**
- Modify: `<repo>/mcp_server.py`
- Modify: `<repo>/tests/test_life_event_graph_v1.py`
- Test: `<repo>/tests/test_life_event_graph_v1.py`

**Interfaces:**
- Consumes: `present_evidence.external_activation.daily_windows`
- Produces: `life_event_graph.event_nodes[]` entries with `kind: "official_day_window"`

- [ ] **Step 1: Write the failing test**

```python
def test_life_event_graph_surfaces_ranked_official_day_window_nodes() -> None:
    strict = {
        "event_judgement": {"event_family": "career", "verdict": "moderate_probability_window", "score": 74},
        "present_evidence": {
            "external_activation": {
                "level": "moderate",
                "source": "vedastro_service_adapter_candidate",
                "daily_windows": [
                    {
                        "date": "2026-07-18",
                        "domain": "career",
                        "score": 5,
                        "confidence": "medium_high",
                        "event_count": 2,
                        "signal_families": ["career_trigger"],
                        "event_ids": ["GocharJupiterAspect10th", "CareerExpansionWindow"],
                        "top_signal_label": "Career expansion window",
                    }
                ],
            }
        },
        "confidence_cap": "medium",
        "missing_evidence": [],
        "blocked": False,
    }

    graph = _build_life_event_graph("career", strict)

    assert any(node["kind"] == "official_day_window" and node["date"] == "2026-07-18" for node in graph["event_nodes"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_life_event_graph_v1.py::test_life_event_graph_surfaces_ranked_official_day_window_nodes -q`

Expected: FAIL because no `official_day_window` nodes exist yet.

- [ ] **Step 3: Write minimal implementation**

In `_build_life_event_graph(...)`, after `external_window` nodes, append:

```python
{
    "kind": "official_day_window",
    "date": window.get("date"),
    "domain": window.get("domain"),
    "score": window.get("score"),
    "confidence": window.get("confidence"),
    "event_count": window.get("event_count"),
    "top_signal_label": window.get("top_signal_label"),
    "signal_families": window.get("signal_families") or [],
    "event_ids": window.get("event_ids") or [],
    "source": external_activation.get("source"),
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_life_event_graph_v1.py::test_life_event_graph_surfaces_ranked_official_day_window_nodes -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add mcp_server.py tests/test_life_event_graph_v1.py
git commit -m "feat: show official vedastro day windows in life event graph"
```

### Task 5: Attach daily-window expansion to full-reading and verify output contract

**Files:**
- Modify: `<repo>/scripts/jyotish_engine.py`
- Modify: `<repo>/tests/test_cli_smoke.py`
- Test: `<repo>/tests/test_cli_smoke.py`

**Interfaces:**
- Consumes: existing `modules.vedastro_range_scan_result`
- Produces: `modules.vedastro_range_scan_result.daily_windows`, `summary.guided_topics`, and strict contracts that can reach day-window evidence through downstream modules

- [ ] **Step 1: Write the failing test**

```python
def test_full_reading_preserves_official_daily_window_fields_in_range_scan_result() -> None:
    result = run_engine(
        "full-reading",
        "--year", "1955",
        "--month", "2",
        "--day", "24",
        "--hour", "19",
        "--minute", "15",
        "--lat", "37.7749",
        "--lon", "-122.4194",
        "--tz", "8",
        "--today", "2026-06-30",
        "--transit-date", "2026-06-30",
    )

    vedastro = result["modules"]["vedastro_range_scan_result"]
    assert "daily_windows" in vedastro
    assert "top_daily_window" in vedastro
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_cli_smoke.py::test_full_reading_preserves_official_daily_window_fields_in_range_scan_result -q`

Expected: FAIL if full-reading path still attaches only overview fields.

- [ ] **Step 3: Write minimal implementation**

Ensure `scripts/jyotish_engine.py` keeps adapter-derived daily-window fields intact when composing:

- `modules.vedastro_range_scan_result`
- `ai_prompt_pack.evidence_snapshot.vedastro_overview`

No reformatting layer should drop them.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_cli_smoke.py::test_full_reading_preserves_official_daily_window_fields_in_range_scan_result -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/jyotish_engine.py tests/test_cli_smoke.py
git commit -m "feat: preserve vedastro daily window evidence in full reading"
```

## Self-Review

- Spec coverage: adapter aggregation, orchestrator propagation, strict workflow promotion, graph exposure, full-reading preservation are all covered.
- Placeholder scan: no TBD/TODO placeholders remain.
- Type consistency: `daily_windows` is always `list[dict]`; `top_daily_window` is always `dict | None`; `official_day_window` is the graph node name across tasks.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-30-vedastro-daily-window-priority.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
