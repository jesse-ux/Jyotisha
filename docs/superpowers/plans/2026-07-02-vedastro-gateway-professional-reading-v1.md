# VedAstro Gateway + Web Professional Reading v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a China-friendly VedAstro-compatible gateway and a web professional reading flow that exposes the same high-rigor reading contract as the Jyotish skill without making users directly call VedAstro.

**Architecture:** Reuse the existing local Jyotish engine as the primary calculation path, and add a small gateway layer above `vedastro_service_adapter.py` that routes through self-hosted VedAstro, official VedAstro, cache, queue, and local fallback. Add a web professional reading endpoint that composes existing `chart`, `high_rigor_workflow`, `strict_workflow_contracts`, `ai_prompt_pack`, MEVG status, real-case calibration status, and user-led calibration controls into one product-ready response. Do not run all 641 VedAstro methods by default; use the existing official capability catalog and dynamic selection.

**Tech Stack:** Python 3 standard library HTTP server, existing `scripts/jyotish_api_server.py`, existing `scripts/vedastro_service_adapter.py`, existing `scripts/vedastro_user_entrypoint.py`, vanilla JS frontend in `jyotish-app`, pytest, existing quality gate.

## Global Constraints

- Mainland China users must not need to directly access `vedastro.org` or `api.vedastro.org`.
- Local Jyotish computation remains authoritative and must continue when VedAstro is blocked.
- VedAstro-compatible evidence may enter `official_primary_evidence`, `secondary_context`, `technique_audit`, `source_metadata`, and evidence packets, but must not silently override local adjudicator labels.
- Default CI must not require live network or a real VedAstro key.
- No API keys, full upstream URLs, or private source artifacts may be rendered in the browser.
- The gateway must report `cached`, `queued`, `blocked`, `self_host`, `official`, or `local_fallback` explicitly.
- Web Professional Reading v1 must support career, relationship, finance, health, education, property, children, migration, prashna, rectification, and timing as routed themes.
- Web Professional Reading v1 must expose Technique Audit Table, MEVG status, Real Case Calibration status, confidence boundary, source governance, and user-led calibration controls.
- Use TDD: failing test first, then minimal implementation.
- Keep edits small and reuse existing helper functions before adding new ones.

---

## File Structure

- Create: `scripts/vedastro_gateway.py`  
  Single gateway orchestrator. Reads CN mode env, selects self-host/official/cache/queue/fallback, calls existing VedAstro adapter/user entrypoint helpers, and returns a stable gateway packet.

- Modify: `scripts/jyotish_api_server.py`  
  Adds `/api/vedastro_gateway/status`, `/api/vedastro_gateway/run`, `/api/vedastro_gateway/jobs/<job_id>`, and `/api/professional_reading`. Reuses existing chart/high-rigor/thematic report code paths.

- Modify: `jyotish-app/api-bridge.js` and `jyotish-app/public/api-bridge.js`  
  Adds `getVedAstroGatewayStatus`, `runVedAstroGateway`, and `runProfessionalReading`.

- Create: `jyotish-app/professional-reading.js`  
  Small UI module for professional reading controls and result rendering. Keeps `main.js` from growing further.

- Modify: `jyotish-app/main.js`  
  Mounts the professional reading panel, shows gateway status in Trust Center, and wires buttons to the API bridge.

- Modify: `jyotish-app/ai-chat.js`  
  Lets AI Chat consume professional reading packets as first-class prompt context.

- Create: `.env.cn.example`  
  Documents CN Gateway Mode without committing secrets.

- Modify: `README.md`  
  Adds ordinary-user deployment path for Mainland China users.

- Test: `tests/test_vedastro_gateway.py`  
  Gateway unit/contract tests.

- Test: `tests/test_api_server_security.py`  
  API route and security tests.

- Test: `tests/test_frontend_productization.py`  
  Frontend static/productization tests.

---

### Task 1: Add VedAstro Gateway Config And Status Contract

**Files:**
- Create: `scripts/vedastro_gateway.py`
- Test: `tests/test_vedastro_gateway.py`

**Interfaces:**
- Produces: `build_gateway_config() -> dict[str, Any]`
- Produces: `gateway_status() -> dict[str, Any]`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_vedastro_gateway.py` with:

```python
from __future__ import annotations

import os


def test_gateway_status_defaults_to_local_first_cn_safe(monkeypatch):
    from scripts import vedastro_gateway

    monkeypatch.delenv("VEDASTRO_GATEWAY_MODE", raising=False)
    monkeypatch.delenv("VEDASTRO_SELF_HOST_ENDPOINT", raising=False)
    monkeypatch.delenv("VEDASTRO_API_ENDPOINT", raising=False)

    status = vedastro_gateway.gateway_status()

    assert status["scope"] == "vedastro_gateway"
    assert status["mode"] == "local_first"
    assert status["direct_browser_access_allowed"] is False
    assert status["frontend_secret_safe"] is True
    assert status["backend_priority"] == ["self_host", "official", "cache", "queue", "local_fallback"]
    assert status["active_backend"] == "local_fallback"
    assert status["boundary"] == "Users never call VedAstro directly; backend gateway owns cache, queue, and fallback."


def test_gateway_status_reports_cn_gateway_self_host(monkeypatch):
    from scripts import vedastro_gateway

    monkeypatch.setenv("VEDASTRO_GATEWAY_MODE", "cn_gateway")
    monkeypatch.setenv("VEDASTRO_SELF_HOST_ENDPOINT", "https://jyotish-gateway.example.com/vedastro")
    monkeypatch.setenv("VEDASTRO_CACHE_TTL_SECONDS", "604800")
    monkeypatch.setenv("VEDASTRO_GATEWAY_QUEUE_ENABLED", "1")

    status = vedastro_gateway.gateway_status()

    assert status["mode"] == "cn_gateway"
    assert status["self_host_configured"] is True
    assert status["active_backend"] == "self_host"
    assert status["cache_ttl_seconds"] == 604800
    assert status["queue_enabled"] is True
```

- [ ] **Step 2: Run red test**

Run:

```bash
python3 -m pytest tests/test_vedastro_gateway.py -q
```

Expected: FAIL with `ImportError: cannot import name 'vedastro_gateway'`.

- [ ] **Step 3: Implement minimal config/status**

Create `scripts/vedastro_gateway.py`:

```python
#!/usr/bin/env python3
"""China-friendly VedAstro-compatible gateway orchestration."""

from __future__ import annotations

import os
from typing import Any


BACKEND_PRIORITY = ["self_host", "official", "cache", "queue", "local_fallback"]


def _bool_env(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int = 0) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(float(raw))
    except ValueError:
        return default


def build_gateway_config() -> dict[str, Any]:
    mode = os.environ.get("VEDASTRO_GATEWAY_MODE", "local_first").strip() or "local_first"
    self_host = os.environ.get("VEDASTRO_SELF_HOST_ENDPOINT", "").strip()
    official = os.environ.get("VEDASTRO_API_ENDPOINT", "").strip()
    return {
        "mode": mode,
        "self_host_endpoint_configured": bool(self_host),
        "official_endpoint_configured": bool(official),
        "cache_ttl_seconds": _int_env("VEDASTRO_CACHE_TTL_SECONDS", 0),
        "queue_enabled": _bool_env("VEDASTRO_GATEWAY_QUEUE_ENABLED") or _bool_env("VEDASTRO_QUEUE_ENABLED"),
        "fail_open_local": os.environ.get("VEDASTRO_FAIL_OPEN_LOCAL", "1").strip().lower() not in {"0", "false", "no"},
    }


def _active_backend(config: dict[str, Any]) -> str:
    if config["self_host_endpoint_configured"]:
        return "self_host"
    if config["official_endpoint_configured"] and _bool_env("VEDASTRO_ENABLE_NETWORK"):
        return "official"
    if config["cache_ttl_seconds"] > 0:
        return "cache"
    if config["queue_enabled"]:
        return "queue"
    return "local_fallback"


def gateway_status() -> dict[str, Any]:
    config = build_gateway_config()
    return {
        "scope": "vedastro_gateway",
        "mode": config["mode"],
        "backend_priority": BACKEND_PRIORITY,
        "active_backend": _active_backend(config),
        "self_host_configured": config["self_host_endpoint_configured"],
        "official_configured": config["official_endpoint_configured"],
        "cache_ttl_seconds": config["cache_ttl_seconds"],
        "queue_enabled": config["queue_enabled"],
        "fail_open_local": config["fail_open_local"],
        "direct_browser_access_allowed": False,
        "frontend_secret_safe": True,
        "boundary": "Users never call VedAstro directly; backend gateway owns cache, queue, and fallback.",
    }
```

- [ ] **Step 4: Run green test**

Run:

```bash
python3 -m pytest tests/test_vedastro_gateway.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/vedastro_gateway.py tests/test_vedastro_gateway.py
git commit -m "Add VedAstro gateway status contract"
```

---

### Task 2: Add Gateway Run Packet With Cache/Queue/Fallback Boundaries

**Files:**
- Modify: `scripts/vedastro_gateway.py`
- Test: `tests/test_vedastro_gateway.py`

**Interfaces:**
- Consumes: `scripts.vedastro_user_entrypoint.build_report(args_like)`
- Produces: `run_gateway_packet(case: dict, question: str, themes: list[str], reference_date: str) -> dict[str, Any]`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_vedastro_gateway.py`:

```python
def test_gateway_run_packet_uses_user_entrypoint_and_marks_not_all_641(monkeypatch):
    from scripts import vedastro_gateway

    monkeypatch.setenv("VEDASTRO_GATEWAY_MODE", "cn_gateway")
    monkeypatch.setenv("VEDASTRO_CACHE_TTL_SECONDS", "604800")
    monkeypatch.setenv("VEDASTRO_GATEWAY_QUEUE_ENABLED", "1")

    packet = vedastro_gateway.run_gateway_packet(
        {
            "year": 1955,
            "month": 2,
            "day": 24,
            "hour": 19,
            "minute": 15,
            "second": 0,
            "lat": 37.7749,
            "lon": -122.4194,
            "tz": 8,
        },
        question="事业机会什么时候出现",
        themes=["career", "health"],
        reference_date="2026-07-02",
    )

    assert packet["scope"] == "vedastro_gateway_run"
    assert packet["status"] in {"ok", "partial", "queued", "blocked", "local_fallback"}
    assert packet["gateway_status"]["mode"] == "cn_gateway"
    assert packet["official_capability_catalog"]["summary"]["catalog_method_count"] >= 0
    assert packet["honesty_boundary"]["all_641_methods_executed"] is False
    assert packet["user_visibility"]["mainland_cn_safe"] is True
```

- [ ] **Step 2: Run red test**

Run:

```bash
python3 -m pytest tests/test_vedastro_gateway.py::test_gateway_run_packet_uses_user_entrypoint_and_marks_not_all_641 -q
```

Expected: FAIL because `run_gateway_packet` is missing.

- [ ] **Step 3: Implement minimal gateway packet**

Add to `scripts/vedastro_gateway.py`:

```python
from types import SimpleNamespace


def _entrypoint_args(case: dict[str, Any], question: str, themes: list[str], reference_date: str) -> SimpleNamespace:
    return SimpleNamespace(
        year=int(case["year"]),
        month=int(case["month"]),
        day=int(case["day"]),
        hour=int(case["hour"]),
        minute=int(case["minute"]),
        second=int(case.get("second", 0)),
        lat=float(case["lat"]),
        lon=float(case["lon"]),
        tz=float(case["tz"]),
        question=question,
        themes=",".join(themes),
        reference_date=reference_date,
        ayanamsa=case.get("ayanamsa_policy") or "lahiri",
        node_mode=case.get("node_policy") or "mean",
        format="json",
    )


def run_gateway_packet(case: dict[str, Any], question: str, themes: list[str], reference_date: str) -> dict[str, Any]:
    try:
        from scripts.vedastro_user_entrypoint import build_report as build_user_entrypoint_report
    except ModuleNotFoundError:  # pragma: no cover
        from vedastro_user_entrypoint import build_report as build_user_entrypoint_report

    gateway = gateway_status()
    entrypoint = build_user_entrypoint_report(_entrypoint_args(case, question, themes, reference_date))
    catalog = entrypoint.get("official_capability_catalog") or {}
    status = catalog.get("status") or "blocked"
    if gateway["active_backend"] in {"cache", "queue", "local_fallback"} and status in {"blocked", "partial"}:
        status = gateway["active_backend"]
    return {
        "scope": "vedastro_gateway_run",
        "status": status,
        "gateway_status": gateway,
        "runtime_mode": entrypoint.get("runtime_mode") or {},
        "official_capability_catalog": catalog,
        "strict_workflow": entrypoint.get("strict_workflow") or {},
        "cache_and_queue": entrypoint.get("cache_and_queue") or {},
        "honesty_boundary": entrypoint.get("honesty_boundary") or {"all_641_methods_executed": False},
        "user_visibility": {
            "mainland_cn_safe": True,
            "message": "本地完整解盘不中断；VedAstro 通过后端网关缓存、排队或降级。",
        },
    }
```

- [ ] **Step 4: Run green tests**

Run:

```bash
python3 -m pytest tests/test_vedastro_gateway.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/vedastro_gateway.py tests/test_vedastro_gateway.py
git commit -m "Add VedAstro gateway run packet"
```

---

### Task 3: Expose Gateway API Routes

**Files:**
- Modify: `scripts/jyotish_api_server.py`
- Test: `tests/test_api_server_security.py`

**Interfaces:**
- Produces: `GET /api/vedastro_gateway/status`
- Produces: `POST /api/vedastro_gateway/run`

- [ ] **Step 1: Write failing API tests**

Add to `tests/test_api_server_security.py`:

```python
def test_vedastro_gateway_status_route_is_cn_safe(monkeypatch):
    handler = _handler()
    monkeypatch.setenv("VEDASTRO_GATEWAY_MODE", "cn_gateway")

    result = handler._compute_vedastro_gateway_status()

    assert result["scope"] == "vedastro_gateway"
    assert result["mode"] == "cn_gateway"
    assert result["direct_browser_access_allowed"] is False
    assert result["frontend_secret_safe"] is True


def test_vedastro_gateway_run_route_returns_gateway_packet(monkeypatch):
    handler = _handler()
    monkeypatch.setenv("VEDASTRO_GATEWAY_MODE", "cn_gateway")

    result = handler._compute_vedastro_gateway_run({
        "year": 1955,
        "month": 2,
        "day": 24,
        "hour": 19,
        "minute": 15,
        "lat": 37.7749,
        "lon": -122.4194,
        "tz": 8,
        "question": "事业机会什么时候出现",
        "themes": ["career"],
        "reference_date": "2026-07-02",
    })

    assert result["scope"] == "vedastro_gateway_run"
    assert result["gateway_status"]["mode"] == "cn_gateway"
    assert result["honesty_boundary"]["all_641_methods_executed"] is False
```

- [ ] **Step 2: Run red test**

Run:

```bash
python3 -m pytest tests/test_api_server_security.py -k "vedastro_gateway" -q
```

Expected: FAIL because handler methods/routes are missing.

- [ ] **Step 3: Implement API methods and route mapping**

In `scripts/jyotish_api_server.py`, add helper methods near existing VedAstro route helpers:

```python
def _compute_vedastro_gateway_status(self):
    from scripts.vedastro_gateway import gateway_status
    return gateway_status()


def _compute_vedastro_gateway_run(self, body):
    from scripts.vedastro_gateway import run_gateway_packet
    birth = self._high_rigor_birth_payload(body)
    themes = self._high_rigor_requested_themes(body)
    reference_date = body.get("reference_date") or body.get("transit_date") or datetime.now().strftime("%Y-%m-%d")
    return run_gateway_packet(
        birth,
        question=str(body.get("question") or ""),
        themes=themes,
        reference_date=reference_date,
    )
```

Add routing in `_handle_get` / `_handle_post` style sections following current route patterns:

```python
if path == "/api/vedastro_gateway/status":
    return self._send_json(self._compute_vedastro_gateway_status())
```

and in the POST dispatch dictionary:

```python
"/api/vedastro_gateway/run": self._compute_vedastro_gateway_run,
```

- [ ] **Step 4: Run green tests**

Run:

```bash
python3 -m pytest tests/test_api_server_security.py -k "vedastro_gateway or vedastro_status" -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/jyotish_api_server.py tests/test_api_server_security.py
git commit -m "Expose VedAstro gateway API routes"
```

---

### Task 4: Add Web Professional Reading Backend Endpoint

**Files:**
- Modify: `scripts/jyotish_api_server.py`
- Test: `tests/test_api_server_security.py`

**Interfaces:**
- Produces: `POST /api/professional_reading`
- Response keys: `professional_reading_contract`, `raw_evidence`, `technique_audit_table`, `mevg_status`, `real_case_calibration`, `user_led_calibration_controls`, `chinese_narrative`, `gateway_packet`

- [ ] **Step 1: Write failing API test**

Add to `tests/test_api_server_security.py`:

```python
def test_professional_reading_endpoint_reuses_existing_high_rigor_layers(monkeypatch):
    handler = _handler()

    monkeypatch.setattr(handler, "_compute_high_rigor_workflow", lambda body: {
        "endpoint": "high_rigor_workflow",
        "chart": {"ai_prompt_pack": {"evidence_snapshot": {"strict_workflow_contracts": {"career": {"confidence_cap": "medium"}}}}},
        "vedastro_official": {"status": "partial"},
        "thematic_report": {"theme": "career", "final_markdown": "事业解读"},
        "rectification_gate": {"status": "not_requested"},
        "historical_backtest": {"status": "not_provided"},
    })
    monkeypatch.setattr(handler, "_compute_vedastro_gateway_run", lambda body: {
        "scope": "vedastro_gateway_run",
        "status": "local_fallback",
        "honesty_boundary": {"all_641_methods_executed": False},
    })

    result = handler._compute_professional_reading({
        "year": 1955,
        "month": 2,
        "day": 24,
        "hour": 19,
        "minute": 15,
        "lat": 37.7749,
        "lon": -122.4194,
        "tz": 8,
        "question": "事业机会什么时候出现",
        "theme": ["career"],
        "blind_mode": True,
    })

    assert result["endpoint"] == "professional_reading"
    assert result["professional_reading_contract"]["evidence_first_conclusion_last"] is True
    assert result["professional_reading_contract"]["blind_mode"] is True
    assert result["gateway_packet"]["scope"] == "vedastro_gateway_run"
    assert "Technique Audit Table" in result["required_visible_sections"]
    assert "MEVG / Global Web Evidence" in result["required_visible_sections"]
    assert "Real Case Calibration" in result["required_visible_sections"]
    assert result["user_led_calibration_controls"]["concrete_time_event_options"] is True
```

- [ ] **Step 2: Run red test**

Run:

```bash
python3 -m pytest tests/test_api_server_security.py::test_professional_reading_endpoint_reuses_existing_high_rigor_layers -q
```

Expected: FAIL because `_compute_professional_reading` is missing.

- [ ] **Step 3: Implement backend composer**

Add to `scripts/jyotish_api_server.py`:

```python
def _compute_professional_reading(self, body):
    high_rigor = self._compute_high_rigor_workflow({**body, "dry_run": False})
    gateway = self._compute_vedastro_gateway_run(body)
    blind_mode = bool(body.get("blind_mode"))
    return {
        "success": True,
        "endpoint": "professional_reading",
        "professional_reading_contract": {
            "version": "professional_reading_v1",
            "evidence_first_conclusion_last": True,
            "blind_mode": blind_mode,
            "uses_existing_high_rigor_workflow": True,
            "uses_vedastro_gateway": True,
            "does_not_require_browser_direct_vedastro": True,
        },
        "gateway_packet": gateway,
        "raw_evidence": {
            "chart": high_rigor.get("chart") or {},
            "vedastro_official": high_rigor.get("vedastro_official") or {},
            "thematic_report": high_rigor.get("thematic_report") or {},
        },
        "technique_audit_table": high_rigor.get("technique_audit_table") or {},
        "mevg_status": high_rigor.get("mevg_status") or {"status": "queued_or_blocked"},
        "real_case_calibration": high_rigor.get("real_case_calibration") or {"status": "case_gap_or_pending"},
        "user_led_calibration_controls": {
            "blind_mode": blind_mode,
            "concrete_time_event_options": True,
            "similarity_weighted_case_calibration": True,
            "transferability_boundary": True,
            "counterexample_handling": True,
        },
        "chinese_narrative": high_rigor.get("thematic_report", {}).get("final_markdown") or "",
        "required_visible_sections": [
            "Technique Audit Table",
            "MEVG / Global Web Evidence",
            "Real Case Calibration",
            "VedAstro Gateway Boundary",
            "User Feedback Isolation",
            "Confidence Boundary",
        ],
    }
```

Add POST route:

```python
"/api/professional_reading": self._compute_professional_reading,
```

- [ ] **Step 4: Run green tests**

Run:

```bash
python3 -m pytest tests/test_api_server_security.py -k "professional_reading or high_rigor_workflow" -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/jyotish_api_server.py tests/test_api_server_security.py
git commit -m "Add professional reading backend endpoint"
```

---

### Task 5: Add Frontend API Bridge And Professional Reading Panel

**Files:**
- Modify: `jyotish-app/api-bridge.js`
- Modify: `jyotish-app/public/api-bridge.js`
- Create: `jyotish-app/professional-reading.js`
- Modify: `jyotish-app/main.js`
- Test: `tests/test_frontend_productization.py`

**Interfaces:**
- Produces: `window.JyotishAPI.getVedAstroGatewayStatus()`
- Produces: `window.JyotishAPI.runVedAstroGateway(payload)`
- Produces: `window.JyotishAPI.runProfessionalReading(payload)`
- Produces: `renderProfessionalReadingPanel(container, chartData)`

- [ ] **Step 1: Write failing frontend static test**

Add to `tests/test_frontend_productization.py`:

```python
def test_professional_reading_web_surface_uses_gateway_and_backend_agent() -> None:
    bridge = read("api-bridge.js")
    main = read("main.js")
    professional = read("professional-reading.js")

    assert "getVedAstroGatewayStatus" in bridge
    assert "postJson('/api/vedastro_gateway/run'" in bridge
    assert "postJson('/api/professional_reading'" in bridge
    assert "renderProfessionalReadingPanel" in professional
    assert "Technique Audit Table" in professional
    assert "MEVG / Global Web Evidence" in professional
    assert "Real Case Calibration" in professional
    assert "VedAstro Gateway Boundary" in professional
    assert "renderProfessionalReadingPanel" in main
```

- [ ] **Step 2: Run red test**

Run:

```bash
python3 -m pytest tests/test_frontend_productization.py::test_professional_reading_web_surface_uses_gateway_and_backend_agent -q
```

Expected: FAIL because bridge functions and panel module are missing.

- [ ] **Step 3: Add API bridge functions**

Add to both `jyotish-app/api-bridge.js` and `jyotish-app/public/api-bridge.js`:

```javascript
async function getVedAstroGatewayStatus() {
  return fetchJson('/api/vedastro_gateway/status');
}

async function runVedAstroGateway(payload) {
  return postJson('/api/vedastro_gateway/run', payload);
}

async function runProfessionalReading(payload) {
  return postJson('/api/professional_reading', payload);
}
```

Export them in the existing `window.JyotishAPI` object.

- [ ] **Step 4: Create professional reading panel**

Create `jyotish-app/professional-reading.js`:

```javascript
import { escapeHtml } from './ui-utils.js';

export function renderProfessionalReadingPanel(container, chartData = {}) {
  if (!container) return;
  container.innerHTML = `
    <section class="professional-reading-panel">
      <h3>专业解盘代理</h3>
      <div class="professional-reading-actions">
        <button type="button" data-action="professional-reading-run">运行专业解盘</button>
        <label><input type="checkbox" data-field="professional-blind-mode" checked> 盲推隔离</label>
      </div>
      <div class="professional-reading-result" data-role="professional-reading-result">
        <p>Technique Audit Table、MEVG / Global Web Evidence、Real Case Calibration、VedAstro Gateway Boundary 会在这里显示。</p>
      </div>
    </section>
  `;
}

export function renderProfessionalReadingResult(result = {}) {
  const sections = result.required_visible_sections || [];
  return `
    <div class="professional-reading-output">
      <h4>专业解盘结果</h4>
      <p>${escapeHtml(result.chinese_narrative || '专业解盘已返回结构化证据，等待中文 narrative。')}</p>
      <ul>${sections.map(section => `<li>${escapeHtml(section)}</li>`).join('')}</ul>
    </div>
  `;
}
```

If `ui-utils.js` does not export `escapeHtml`, use the existing escape helper already imported by `main.js` or add a local minimal escape function in this module.

- [ ] **Step 5: Mount the panel in `main.js`**

Import:

```javascript
import { renderProfessionalReadingPanel, renderProfessionalReadingResult } from './professional-reading.js';
```

Mount near existing guided topics / Trust Center rendering:

```javascript
renderProfessionalReadingPanel(document.getElementById('professional-reading-section'), chartData);
```

Add click handling:

```javascript
if (action === 'professional-reading-run') {
  const payload = buildCurrentBirthPayload();
  payload.question = '专业解盘';
  payload.theme = ['career', 'marriage', 'wealth'];
  payload.blind_mode = Boolean(document.querySelector('[data-field="professional-blind-mode"]')?.checked);
  const result = await window.JyotishAPI.runProfessionalReading(payload);
  document.querySelector('[data-role="professional-reading-result"]').innerHTML = renderProfessionalReadingResult(result);
}
```

Use the existing birth-payload builder in `main.js`; if the function has a different name, call the existing helper rather than duplicating parsing.

- [ ] **Step 6: Run green frontend tests**

Run:

```bash
python3 -m pytest tests/test_frontend_productization.py::test_professional_reading_web_surface_uses_gateway_and_backend_agent -q
npm run build --prefix jyotish-app
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add jyotish-app/api-bridge.js jyotish-app/public/api-bridge.js jyotish-app/professional-reading.js jyotish-app/main.js tests/test_frontend_productization.py
git commit -m "Add web professional reading panel"
```

---

### Task 6: Make AI Chat Prefer Professional Reading Packets

**Files:**
- Modify: `jyotish-app/ai-chat.js`
- Test: `tests/test_frontend_productization.py`

**Interfaces:**
- Consumes: `chartData.professional_reading`
- Produces: AI chat context section `【Professional Reading Packet】`

- [ ] **Step 1: Write failing test**

Add to `tests/test_frontend_productization.py`:

```python
def test_ai_chat_consumes_professional_reading_packet() -> None:
    ai_chat = read("ai-chat.js")

    assert "【Professional Reading Packet】" in ai_chat
    assert "professional_reading" in ai_chat
    assert "user_led_calibration_controls" in ai_chat
    assert "VedAstro Gateway Boundary" in ai_chat
```

- [ ] **Step 2: Run red test**

Run:

```bash
python3 -m pytest tests/test_frontend_productization.py::test_ai_chat_consumes_professional_reading_packet -q
```

Expected: FAIL.

- [ ] **Step 3: Add AI context block**

In `jyotish-app/ai-chat.js`, near existing `ai_prompt_pack` context assembly, add:

```javascript
if (cd.professional_reading) {
  contextParts.push(
    '【Professional Reading Packet】',
    JSON.stringify(cd.professional_reading, null, 2),
    '【VedAstro Gateway Boundary】',
    JSON.stringify(cd.professional_reading.gateway_packet || {}, null, 2),
    '【User-Led Calibration Controls】',
    JSON.stringify(cd.professional_reading.user_led_calibration_controls || {}, null, 2)
  );
}
```

- [ ] **Step 4: Run green test**

Run:

```bash
python3 -m pytest tests/test_frontend_productization.py::test_ai_chat_consumes_professional_reading_packet -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add jyotish-app/ai-chat.js tests/test_frontend_productization.py
git commit -m "Add professional reading packet to AI chat context"
```

---

### Task 7: Add Mainland China Deployment Config And Docs

**Files:**
- Create: `.env.cn.example`
- Modify: `README.md`
- Test: `tests/test_frontend_productization.py`

**Interfaces:**
- Produces documented env contract:
  - `VEDASTRO_GATEWAY_MODE=cn_gateway`
  - `VEDASTRO_SELF_HOST_ENDPOINT`
  - `VEDASTRO_OFFICIAL_DIRECT=0`
  - `VEDASTRO_CACHE_TTL_SECONDS=604800`
  - `VEDASTRO_GATEWAY_QUEUE_ENABLED=1`
  - `VEDASTRO_FAIL_OPEN_LOCAL=1`

- [ ] **Step 1: Write failing docs/config test**

Add to `tests/test_frontend_productization.py`:

```python
def test_cn_gateway_docs_and_env_example_exist() -> None:
    env = (ROOT / ".env.cn.example").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    for token in [
        "VEDASTRO_GATEWAY_MODE=cn_gateway",
        "VEDASTRO_SELF_HOST_ENDPOINT=",
        "VEDASTRO_OFFICIAL_DIRECT=0",
        "VEDASTRO_CACHE_TTL_SECONDS=604800",
        "VEDASTRO_GATEWAY_QUEUE_ENABLED=1",
        "VEDASTRO_FAIL_OPEN_LOCAL=1",
    ]:
        assert token in env
    assert "中国大陆用户" in readme
    assert "VedAstro Gateway" in readme
    assert "不要让浏览器直连 VedAstro" in readme
```

- [ ] **Step 2: Run red test**

Run:

```bash
python3 -m pytest tests/test_frontend_productization.py::test_cn_gateway_docs_and_env_example_exist -q
```

Expected: FAIL because `.env.cn.example` or README section is missing.

- [ ] **Step 3: Add `.env.cn.example`**

Create `.env.cn.example`:

```bash
# Mainland China friendly mode: browser -> our backend -> VedAstro gateway/cache/queue/fallback
VEDASTRO_GATEWAY_MODE=cn_gateway
VEDASTRO_SELF_HOST_ENDPOINT=
VEDASTRO_API_ENDPOINT=https://api.vedastro.org/api
VEDASTRO_ENABLE_NETWORK=1
VEDASTRO_OFFICIAL_DIRECT=0
VEDASTRO_CACHE_TTL_SECONDS=604800
VEDASTRO_OFFICIAL_FULL_SNAPSHOT_CACHE_TTL_SECONDS=604800
VEDASTRO_GATEWAY_QUEUE_ENABLED=1
VEDASTRO_FAIL_OPEN_LOCAL=1
VEDASTRO_TIMEOUT_SECONDS=20
```

- [ ] **Step 4: Add README section**

Add a section after the current VedAstro user entrypoint docs:

```markdown
### 中国大陆用户：VedAstro Gateway 模式

普通用户不要让浏览器直连 VedAstro。部署时复制 `.env.cn.example` 为 `.env.local`，让网页只访问我们的后端，由后端统一执行 VedAstro Gateway、缓存、队列和本地 fallback。
```

Include the exact startup path:

```bash
cp .env.cn.example .env.local
python3 scripts/jyotish_api_server.py --host 127.0.0.1 --port 5200
cd jyotish-app && npm run dev -- --host 127.0.0.1 --port 5173
```

- [ ] **Step 5: Run green test**

Run:

```bash
python3 -m pytest tests/test_frontend_productization.py::test_cn_gateway_docs_and_env_example_exist -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add .env.cn.example README.md tests/test_frontend_productization.py
git commit -m "Document China-friendly VedAstro gateway mode"
```

---

### Task 8: Verification, Quality Gate, And Release Hygiene

**Files:**
- Modify: `progress.md`
- Modify: `findings.md`

**Interfaces:**
- Produces: verified local branch ready to push

- [ ] **Step 1: Run gateway and API tests**

Run:

```bash
python3 -m pytest tests/test_vedastro_gateway.py tests/test_vedastro_user_entrypoint.py tests/test_vedastro_official_capability_runner.py tests/test_api_server_security.py -k "vedastro_gateway or professional_reading or vedastro_user_entrypoint or official_capability" -q
```

Expected: all selected tests pass.

- [ ] **Step 2: Run frontend productization tests**

Run:

```bash
python3 -m pytest tests/test_frontend_productization.py -k "professional_reading or cn_gateway or ai_chat_consumes_professional" -q
```

Expected: all selected tests pass.

- [ ] **Step 3: Run frontend build**

Run:

```bash
npm run build --prefix jyotish-app
```

Expected: build exits 0.

- [ ] **Step 4: Run smoke command**

Run:

```bash
python3 scripts/vedastro_user_entrypoint.py \
  --year 1955 --month 2 --day 24 --hour 19 --minute 15 \
  --lat 37.7749 --lon -122.4194 --tz -8 \
  --question "事业机会什么时候出现" \
  --themes career,marriage,wealth \
  --reference-date 2026-07-02 \
  --format markdown
```

Expected: prints `VedAstro 用户级入口`, `catalog_method_count`, `strict workflow triggered`, and the 641-method execution boundary.

- [ ] **Step 5: Run quick gate**

Run:

```bash
python3 scripts/run_quality_gate.py --profile quick --skip-frontend-runtime
```

Expected: exits 0 or reports only documented live-network skips. If unrelated existing dirty files block the gate, record exact filenames and do not auto-revert user changes.

- [ ] **Step 6: Update project records**

Append to `progress.md`:

```markdown
## 2026-07-02 - VedAstro Gateway + Web Professional Reading v1

- Added CN Gateway mode so Mainland China users do not call VedAstro directly from the browser.
- Added `/api/vedastro_gateway/status`, `/api/vedastro_gateway/run`, and `/api/professional_reading`.
- Added web Professional Reading panel and AI Chat packet context.
- Verification: [paste exact commands and pass/fail results].
```

Append to `findings.md`:

```markdown
## VedAstro Gateway Boundary

- Gateway mode uses self-host/official/cache/queue/local fallback priority.
- 641 official capability catalog remains classification and dynamic-selection evidence, not proof that all 641 methods executed.
- Mainland China users can receive full local Jyotish readings even when VedAstro is cached, queued, or blocked.
```

- [ ] **Step 7: Commit verification records**

```bash
git add progress.md findings.md
git commit -m "Record VedAstro gateway professional reading verification"
```

- [ ] **Step 8: Push branch**

Run:

```bash
git push origin codex/release-hygiene-ci
```

Expected: push succeeds.

## Self-Review

- Spec coverage: self-host-compatible gateway, China-friendly backend access, web professional reading, skill-level audit visibility, user-led calibration controls, docs, and verification are each covered by tasks.
- Placeholder scan: no `TBD`, `TODO`, or "implement later" placeholders remain.
- Type consistency: gateway functions return `dict[str, Any]`; API methods consume the existing handler body dicts and reuse existing `_high_rigor_birth_payload` / `_high_rigor_requested_themes`; frontend bridge functions map one-to-one to backend endpoints.
- Scope control: v1 does not attempt to clone all 641 VedAstro calculators. It makes them classifiable, routable, cacheable, queueable, and visible through the gateway boundary.
- Compute control: default tests use stubs and local fallback. Live VedAstro remains optional and explicit.
