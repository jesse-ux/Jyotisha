# Chart Async And Unified Stage Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a reusable lightweight async `job_id + poll` lane for normal `/api/chart` while promoting `full-reading` stage timings into a clearer unified contract.

**Architecture:** Reuse the existing file-backed high-rigor job runner by extracting shared chart/high-rigor job helpers inside `scripts/jyotish_api_server.py`. Reuse the existing `full-reading` stage timing instrumentation in `scripts/jyotish_engine.py` and only reshape it into grouped stage metadata instead of adding new heavy computation.

**Tech Stack:** Python, existing HTTPServer API server, existing file-backed scratch job records, pytest.

## Global Constraints

- Reuse current job runner; do not add Redis, Celery, RQ, or a second queue.
- Keep sync `/api/chart` behavior unchanged unless `async`/`enqueue` is explicitly requested.
- Keep completed chart async result identical to sync chart payload.
- Do not add new heavy computation for stage grouping; reshape existing timing only.
- Preserve current honesty boundaries around VedAstro partial/blocked states.

---

### Task 1: Promote full-reading stage timings into a unified stage contract

**Files:**
- Modify: `<repo>/scripts/jyotish_engine.py`
- Test: `<repo>/tests/test_cli_smoke.py`

**Interfaces:**
- Consumes:
  - `summary["stage_timings"]: list[dict]`
- Produces:
  - `summary["stage_contract_version"]: int`
  - `summary["stage_groups"]: list[dict]`
  - `summary["cache_recommendations"]: dict`
  - `summary["async_recommendations"]: dict`

- [ ] **Step 1: Write the failing test**

Add a focused test in `tests/test_cli_smoke.py` asserting the new contract fields:

```python
def test_full_reading_summary_exposes_unified_stage_groups() -> None:
    result = run_engine(
        "full-reading",
        "--year", "1990",
        "--month", "1",
        "--day", "1",
        "--hour", "12",
        "--minute", "0",
        "--lat", "39.9",
        "--lon", "116.4",
        "--tz", "8",
        "--today", "2026-01-01",
        "--transit-date", "2026-01-01",
    )

    summary = result["summary"]
    assert summary["stage_contract_version"] == 1
    assert isinstance(summary["stage_groups"], list)
    assert any(group["group"] == "official_evidence" for group in summary["stage_groups"])
    assert summary["cache_recommendations"]["api_chart_response"] == "recommended"
    assert summary["async_recommendations"]["chart_async_optional"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest tests/test_cli_smoke.py::test_full_reading_summary_exposes_unified_stage_groups -q
```

Expected: FAIL with missing `stage_contract_version` or `stage_groups`.

- [ ] **Step 3: Write minimal implementation**

In `scripts/jyotish_engine.py`, add a small helper near the stage-timing helpers:

```python
def _build_unified_stage_contract(stage_timings):
    groups = {
        'local_core': ['core_chart_and_setup', 'dasha_and_core_varga_stack', 'advanced_interpretation_and_timing_layers', 'dynamic_hooks'],
        'official_evidence': ['vedastro_official_snapshot', 'vedastro_main_entry_overview'],
        'contract_and_prompt': ['strict_contracts', 'guided_topics', 'ai_prompt_pack'],
    }
    rows = []
    for group_name, stage_names in groups.items():
        matched = [row for row in stage_timings if row.get('stage') in stage_names]
        rows.append({
            'group': group_name,
            'stages': [row.get('stage') for row in matched],
            'elapsed_seconds': round(sum(float(row.get('elapsed_seconds', 0) or 0) for row in matched), 4),
            'execution_mode': (
                'sync_remote_heavy' if group_name == 'official_evidence'
                else 'sync_structuring' if group_name == 'contract_and_prompt'
                else 'sync_local'
            ),
        })
    return {
        'stage_contract_version': 1,
        'stage_groups': rows,
        'cache_recommendations': {
            'api_chart_response': 'recommended',
            'official_full_snapshot_semantic': 'recommended',
        },
        'async_recommendations': {
            'chart_async_optional': True,
            'high_rigor_async_recommended': True,
        },
    }
```

Then merge that helper output into `report['summary']` after `stage_timings` and `slowest_stages` are computed.

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python3 -m pytest tests/test_cli_smoke.py::test_full_reading_summary_exposes_unified_stage_groups -q
```

Expected: PASS

### Task 2: Generalize the file-backed async job runner for chart and high-rigor scopes

**Files:**
- Modify: `<repo>/scripts/jyotish_api_server.py`
- Test: `<repo>/tests/test_api_server_security.py`

**Interfaces:**
- Consumes:
  - existing `_write_high_rigor_job_record(job_id, payload)`
  - existing `_load_high_rigor_job_record(job_id)`
- Produces:
  - shared `_enqueue_async_job(...)`
  - shared `_get_async_job(...)`
  - chart scope job records

- [ ] **Step 1: Write the failing tests**

Add tests in `tests/test_api_server_security.py`:

```python
def test_chart_async_submit_returns_job_id(monkeypatch: pytest.MonkeyPatch) -> None:
    handler = _handler()
    monkeypatch.setattr(handler, '_enqueue_chart_job', lambda body: {
        'success': True,
        'endpoint': 'chart_async',
        'mode': 'async_submitted',
        'job_id': 'chart_test_job_1',
        'status': 'queued',
        'poll_path': '/api/chart/jobs/chart_test_job_1',
        'scope': 'api_chart_response',
    })

    result = handler._compute_chart({'async': True, 'year': REDACTED_YEAR, 'month': 4, 'day': 17, 'hour': 14, 'minute': 49, 'lat': 36.42, 'lon': 114.2, 'tz': 8})

    assert result['mode'] == 'async_submitted'
    assert result['job_id'] == 'chart_test_job_1'
    assert result['poll_path'].endswith('/chart_test_job_1')
```

```python
def test_chart_job_poll_endpoint_returns_cached_job_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(jyotish_api_server, '_load_async_job_record', lambda scope, job_id: {
        'success': True,
        'endpoint': 'chart_async',
        'mode': 'async_result',
        'job_id': job_id,
        'status': 'completed',
        'result': {'success': True, 'runtime_cache': {'scope': 'api_chart_response'}},
    })
    handler = _HighRigorJobCaptureHandler('/api/chart/jobs/chart_test_job_2')
    handler.do_GET()
    payload = handler.payload()
    assert payload['job_id'] == 'chart_test_job_2'
    assert payload['result']['runtime_cache']['scope'] == 'api_chart_response'
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python3 -m pytest tests/test_api_server_security.py -k "chart_async_submit_returns_job_id or chart_job_poll_endpoint_returns_cached_job_payload" -q
```

Expected: FAIL because `/api/chart` has no async branch and `/api/chart/jobs/...` is not routed.

- [ ] **Step 3: Write minimal implementation**

In `scripts/jyotish_api_server.py`:

1. Add a generic job storage layer:

```python
def _job_dir(scope: str) -> Path:
    path = Path(REPO_ROOT) / 'scratch' / 'local' / f'{scope}_jobs'
    path.mkdir(parents=True, exist_ok=True)
    return path

def _job_path(scope: str, job_id: str) -> Path:
    return _job_dir(scope) / f'{job_id}.json'

def _load_async_job_record(scope: str, job_id: str) -> dict | None:
    path = _job_path(scope, job_id)
    ...

def _write_async_job_record(scope: str, job_id: str, payload: dict) -> dict:
    ...
```

2. Keep high-rigor wrappers calling the shared helpers.
3. Add `_enqueue_chart_job(body)` that runs `_compute_chart_sync(body_without_async_flags)` in a background thread.
4. Add `_compute_chart_sync(body)` by moving current synchronous `_compute_chart` body there.
5. Make `_compute_chart(body)` return `_enqueue_chart_job(body)` when `async` or `enqueue` is set.
6. Add `GET /api/chart/jobs/{job_id}` in `do_GET`.

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python3 -m pytest tests/test_api_server_security.py -k "chart_async_submit_returns_job_id or chart_job_poll_endpoint_returns_cached_job_payload" -q
```

Expected: PASS

### Task 3: Make chart async completion return the normal chart payload unchanged

**Files:**
- Modify: `<repo>/scripts/jyotish_api_server.py`
- Test: `<repo>/tests/test_api_server_security.py`

**Interfaces:**
- Consumes:
  - `_compute_chart_sync(body: dict) -> dict`
- Produces:
  - async chart completed record with `result` equal to normal chart payload shape

- [ ] **Step 1: Write the failing test**

Add:

```python
def test_chart_async_job_executes_in_background(monkeypatch: pytest.MonkeyPatch) -> None:
    handler = _handler()
    writes = []

    def fake_write(scope: str, job_id: str, payload: dict) -> dict:
        writes.append((scope, job_id, dict(payload)))
        return payload

    def fake_sync(body: dict) -> dict:
        time.sleep(0.05)
        return {'success': True, 'modules': {'chart': {'planets': {}, 'ascendant': {}}}, 'runtime_cache': {'scope': 'api_chart_response'}}

    monkeypatch.setattr(jyotish_api_server, '_write_async_job_record', fake_write)
    monkeypatch.setattr(handler, '_compute_chart_sync', fake_sync)

    result = handler._enqueue_chart_job({'async': True, 'year': REDACTED_YEAR, 'month': 4, 'day': 17, 'hour': 14, 'minute': 49, 'lat': 36.42, 'lon': 114.2, 'tz': 8})

    assert result['endpoint'] == 'chart_async'
    assert result['status'] == 'queued'

    deadline = time.time() + 1.0
    while len(writes) < 3 and time.time() < deadline:
        time.sleep(0.01)

    assert writes[-1][2]['status'] == 'completed'
    assert writes[-1][2]['result']['runtime_cache']['scope'] == 'api_chart_response'
    assert 'modules' in writes[-1][2]['result']
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest tests/test_api_server_security.py::test_chart_async_job_executes_in_background -q
```

Expected: FAIL because chart async job path does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Implement `_enqueue_chart_job(body)` as a thin wrapper around the shared async runner:

```python
def _enqueue_chart_job(self, body):
    body_copy = dict(body or {})
    body_copy.pop('async', None)
    body_copy.pop('enqueue', None)
    return self._enqueue_async_job(
        scope='api_chart_response',
        endpoint='chart_async',
        job_prefix='chart',
        poll_base='/api/chart/jobs',
        compute_fn=lambda: self._compute_chart_sync(body_copy),
    )
```

Keep completed `result` untouched.

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python3 -m pytest tests/test_api_server_security.py::test_chart_async_job_executes_in_background -q
```

Expected: PASS

### Task 4: Keep existing high-rigor async path working on top of the shared helper

**Files:**
- Modify: `<repo>/scripts/jyotish_api_server.py`
- Test: `<repo>/tests/test_api_server_security.py`

**Interfaces:**
- Consumes:
  - shared async helper
- Produces:
  - backward-compatible high-rigor async submit and polling

- [ ] **Step 1: Re-run existing high-rigor async tests as regression guards**

Run:

```bash
python3 -m pytest tests/test_api_server_security.py -k "high_rigor_async_submit_returns_job_id or high_rigor_job_poll_endpoint_returns_cached_job_payload or high_rigor_async_job_executes_in_background" -q
```

Expected: If this fails after Task 2/3 changes, fix compatibility before proceeding.

- [ ] **Step 2: Minimal compatibility implementation**

Keep wrappers like:

```python
def _enqueue_high_rigor_job(self, body):
    ...
    return self._enqueue_async_job(
        scope=_HIGH_RIGOR_JOB_SCOPE,
        endpoint='high_rigor_workflow_async',
        job_prefix='hrw',
        poll_base='/api/high_rigor_workflow/jobs',
        compute_fn=lambda: self._compute_high_rigor_workflow_sync(body_copy),
    )
```

And route `GET /api/high_rigor_workflow/jobs/{job_id}` through the shared loader.

- [ ] **Step 3: Run regression tests to verify they pass**

Run:

```bash
python3 -m pytest tests/test_api_server_security.py -k "high_rigor_async_submit_returns_job_id or high_rigor_job_poll_endpoint_returns_cached_job_payload or high_rigor_async_job_executes_in_background" -q
```

Expected: PASS

### Task 5: Run focused regression bundle and update progress

**Files:**
- Modify: `<repo>/progress.md`

**Interfaces:**
- Consumes:
  - all prior tasks
- Produces:
  - verification record in `progress.md`

- [ ] **Step 1: Run focused regression bundle**

Run:

```bash
python3 -m pytest \
  tests/test_cli_smoke.py::test_full_reading_summary_exposes_stage_timing_contract \
  tests/test_cli_smoke.py::test_full_reading_summary_exposes_unified_stage_groups \
  tests/test_api_server_security.py -k "chart_async or high_rigor_async or runtime_cache or fragment_audit_blocks_registry_surface_drift" \
  tests/test_mcp_strict_workflow_career.py \
  tests/test_mcp_strict_workflow_relationship.py \
  tests/test_mcp_strict_workflow_finance.py \
  -q
```

Expected: PASS

- [ ] **Step 2: Run chart/high-rigor API regression bundle**

Run:

```bash
python3 -m pytest tests/test_api_server_security.py tests/test_historical_event_backtest.py -q
```

Expected: PASS

- [ ] **Step 3: Update progress.md**

Add an entry covering:

- unified stage contract added to `full-reading`
- `/api/chart` async submit + poll landed
- shared async helper now serves chart + high-rigor
- focused verification results
