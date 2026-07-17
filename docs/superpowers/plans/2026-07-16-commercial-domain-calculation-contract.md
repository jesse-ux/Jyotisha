# Commercial Domain Calculation Contract Implementation Plan
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Port the mature research-domain calculation service into `jesse-ux/Jyotisha` so commercial API chart responses carry effective parameters and a stable result hash.

**Architecture:** Keep the two repositories independent. Copy the self-contained research `scripts/domain_calculation_service.py` into the commercial repository, then make the commercial API chart endpoint delegate local chart calculation to that service while preserving commercial auth/deployment code.

**Tech Stack:** Python stdlib, Swiss Ephemeris-backed existing `jyotish_engine.py`, pytest.

### Task 1: Add Commercial Regression Tests
**Files:**
- Create: `/tmp/Jyotisha-jesse-ux/tests/test_commercial_domain_calculation_contract.py`

- [ ] **Step 1: Write failing tests**
Test direct service import and API `_compute_chart_sync()` response fields:
```python
def test_domain_chart_exposes_effective_parameters_and_result_hash():
    from domain_calculation_service import compute_chart
    result = compute_chart(...)
    assert result["calculation_contract"]["effective"]["node_mode"] == "true"
    assert result["result_hash"]
```

- [ ] **Step 2: Run test to verify it fails**
Run: `python3 -m pytest -q tests/test_commercial_domain_calculation_contract.py`
Expected: fail because `domain_calculation_service` is absent or API omits `calculation_contract`.

### Task 2: Port Minimal Service and API Delegation
**Files:**
- Create: `/tmp/Jyotisha-jesse-ux/scripts/domain_calculation_service.py`
- Modify: `/tmp/Jyotisha-jesse-ux/scripts/jyotish_api_server.py`

- [ ] **Step 1: Copy the mature research service**
Copy only `/Users/wuyongnaren/Documents/印度占星/scripts/domain_calculation_service.py`.

- [ ] **Step 2: Replace duplicated commercial chart calculation**
In `JyotishAPIHandler._compute_chart_sync()`, call `domain_calculation_service.compute_chart(...)`.

- [ ] **Step 3: Preserve existing response shape**
Return planets, ascendant, houses, divisional data and existing fields; add `calculation_contract` and `result_hash`.

### Task 3: Verify, Ledger, Push
**Files:**
- Modify both repos: `references/cross_project_contract/sync_ledger.json`

- [ ] **Step 1: Run focused tests**
Run commercial:
```bash
python3 -m pytest -q tests/test_commercial_domain_calculation_contract.py tests/test_cross_project_contract.py tests/test_cross_project_sync_status.py
```

- [ ] **Step 2: Run privacy and sync checks**
Run both repositories' privacy scans and cross-project sync status checks.

- [ ] **Step 3: Commit and push**
Commit commercial feature branch only. Update research ledger with the exact commercial commit. Push both feature branches.
