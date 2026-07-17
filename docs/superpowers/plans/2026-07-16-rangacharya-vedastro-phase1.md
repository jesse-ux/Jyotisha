# Rangacharya Variant + VedAstro Closure Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first safe Rangacharya variant slice: source manifest, core variant skeleton, current-vs-variant diff output, non-adjudication guard, and VedAstro raw-closure status hooks.

**Architecture:** Keep current Jaimini unchanged. Add a small `rangacharya` module that consumes the same chart inputs, emits experimental outputs, and is blocked from verdict/timing use by explicit validation status. Add source-manifest governance before importing any screenshot/archive/article rules into runtime.

**Tech Stack:** Python 3 standard library, existing `scripts/jaimini.py`, existing `scripts/jyotish_api_server.py`, existing VedAstro gateway/archive contracts, pytest.

## Global Constraints

- Do not store or echo the VedAstro key.
- Do not copy AGPL PyJHora code.
- Do not use `.workbuddy` as runtime.
- Do not change existing `calc_arudha_padas()` behavior.
- Every new Rangacharya rule starts `transcribed`, `blocked`, or `experimental_not_for_adjudication`.
- Keep unrelated dirty-tree files untouched.

## File Map

- Create `references/rangacharya_source_manifest.json`: source inventory and rule validation states.
- Create `scripts/rangacharya.py`: independent variant functions and diff helpers.
- Create `tests/test_rangacharya_source_manifest.py`: manifest schema/privacy tests.
- Create `tests/test_rangacharya_variant.py`: core variant and non-adjudication tests.
- Modify `scripts/jyotish_api_server.py`: optional `variant=rangacharya|all` in Jaimini endpoint.
- Modify `tests/test_jaimini.py` or create `tests/test_jaimini_rangacharya_api.py`: endpoint contract tests.
- Modify existing VedAstro tests only if needed to expose raw-closure status, not to run real credentials in CI.

---

### Task 1: Source Manifest

**Files:**
- Create: `references/rangacharya_source_manifest.json`
- Create: `tests/test_rangacharya_source_manifest.py`

- [ ] **Step 1: Write failing manifest tests**

Create `tests/test_rangacharya_source_manifest.py`:

```python
import json
from pathlib import Path


MANIFEST = Path("references/rangacharya_source_manifest.json")


def test_manifest_exists_and_has_required_sections():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    assert "sources" in data
    assert "rules" in data
    assert "validation_ladder" in data


def test_manifest_does_not_contain_secrets():
    text = MANIFEST.read_text(encoding="utf-8")
    assert "sk_live_" not in text
    assert "api_key" not in text.lower()


def test_rules_default_below_adjudication():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for rule in data["rules"]:
        assert rule["status"] in {
            "transcribed",
            "source_verified",
            "golden_verified",
            "engine_cross_checked",
            "case_calibrated",
            "blocked",
        }
        assert rule["status"] != "adjudication_enabled"
        assert rule["adjudication_enabled"] is False
```

- [ ] **Step 2: Run test, verify failure**

Run:

```bash
python3 -m pytest tests/test_rangacharya_source_manifest.py -q
```

Expected: FAIL because manifest is missing.

- [ ] **Step 3: Add minimal manifest**

Create `references/rangacharya_source_manifest.json` with no secrets:

```json
{
  "schema_version": 1,
  "created": "2026-07-16",
  "sources": [
    {
      "id": "uploaded_screenshots_20260716",
      "kind": "user_uploaded_screenshots",
      "paths": [
        "/Users/wuyongnaren/Downloads/IMG_3502.PNG",
        "/Users/wuyongnaren/Downloads/IMG_3503.PNG",
        "/Users/wuyongnaren/Downloads/IMG_3504.PNG",
        "/Users/wuyongnaren/Downloads/IMG_3505.PNG",
        "/Users/wuyongnaren/Downloads/IMG_3506.PNG",
        "/Users/wuyongnaren/Downloads/IMG_3507.PNG"
      ],
      "license": "user_private_reference",
      "privacy": "private",
      "runtime_use": "reference_only_until_formula_verified"
    },
    {
      "id": "local_article_warehouse_20260716",
      "kind": "local_research_archive",
      "path": "/Users/wuyongnaren/文件仓库/印度占星文章",
      "license": "unknown",
      "privacy": "local_research",
      "runtime_use": "manifest_only_until_hash_and_license_review"
    },
    {
      "id": "vedastro_official",
      "kind": "external_oracle",
      "url": "https://github.com/VedAstro/VedAstro",
      "license": "MIT",
      "privacy": "public",
      "runtime_use": "oracle_raw_reference"
    },
    {
      "id": "pyjhora_official",
      "kind": "external_oracle",
      "url": "https://github.com/naturalstupid/PyJHora",
      "license": "AGPL-3.0",
      "privacy": "public",
      "runtime_use": "isolated_external_process_only"
    }
  ],
  "validation_ladder": [
    "transcribed",
    "source_verified",
    "golden_verified",
    "engine_cross_checked",
    "case_calibrated",
    "adjudication_enabled",
    "blocked"
  ],
  "rules": [
    {
      "id": "rangacharya_core_arudha",
      "label": "Rangacharya Arudha core counting",
      "source_ids": ["uploaded_screenshots_20260716"],
      "status": "transcribed",
      "adjudication_enabled": false
    },
    {
      "id": "active_effective_lagna",
      "label": "Active Lagna and Effective Lagna",
      "source_ids": ["uploaded_screenshots_20260716"],
      "status": "transcribed",
      "adjudication_enabled": false
    },
    {
      "id": "rangacharya_named_yogas",
      "label": "Dhana/Nirdhana/Kemadruma and other named yogas",
      "source_ids": ["uploaded_screenshots_20260716"],
      "status": "blocked",
      "adjudication_enabled": false,
      "blocked_reason": "needs formula-level source cards before runtime use"
    }
  ]
}
```

- [ ] **Step 4: Run test, verify pass**

Run:

```bash
python3 -m pytest tests/test_rangacharya_source_manifest.py -q
```

- [ ] **Step 5: Commit**

Stage only manifest and its test.

---

### Task 2: Rangacharya Variant Skeleton

**Files:**
- Create: `scripts/rangacharya.py`
- Create: `tests/test_rangacharya_variant.py`

- [ ] **Step 1: Write failing core tests**

Create `tests/test_rangacharya_variant.py`:

```python
from scripts import rangacharya


SAMPLE_LONGS = {
    "Sun": 10.0,
    "Moon": 45.0,
    "Mars": 80.0,
    "Mercury": 110.0,
    "Jupiter": 145.0,
    "Venus": 200.0,
    "Saturn": 250.0,
    "Rahu": 300.0,
    "Ketu": 120.0,
}


def test_variant_result_is_experimental_and_not_for_adjudication():
    result = rangacharya.calc_rangacharya_variant(0, SAMPLE_LONGS)
    assert result["variant"] == "rangacharya"
    assert result["adjudication_enabled"] is False
    assert result["status"] == "experimental_not_for_adjudication"


def test_variant_includes_core_sections():
    result = rangacharya.calc_rangacharya_variant(0, SAMPLE_LONGS)
    assert "source_status" in result
    assert "arudha_padas" in result
    assert "active_lagna" in result
    assert "effective_lagna" in result


def test_diff_marks_algorithm_names():
    current = {"AL": {"sign": "Aries"}}
    variant = {"arudha_padas": {"AL": {"sign": "Taurus"}}}
    diff = rangacharya.diff_current_vs_rangacharya(current, variant)
    assert diff["current_algorithm"] == "current_jaimini"
    assert diff["variant_algorithm"] == "rangacharya"
    assert diff["differences"][0]["key"] == "AL.sign"
```

- [ ] **Step 2: Run test, verify failure**

Run:

```bash
python3 -m pytest tests/test_rangacharya_variant.py -q
```

Expected: FAIL because module is missing.

- [ ] **Step 3: Add minimal module**

Create `scripts/rangacharya.py`:

```python
"""Experimental Rangacharya/Jaimini variant.

All outputs are blocked from adjudication until formula-level validation passes.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping


SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def _sign_index(longitude: float) -> int:
    return int((longitude % 360) // 30)


def _sign_name(index: int) -> str:
    return SIGNS[index % 12]


def _placeholder_pada(label: str, asc_sign_idx: int, source_house: int) -> Dict[str, Any]:
    sign_idx = (asc_sign_idx + source_house - 1) % 12
    return {
        "label": label,
        "sign": _sign_name(sign_idx),
        "sign_index": sign_idx,
        "source_house": source_house,
        "validation_status": "transcribed",
        "adjudication_enabled": False,
        "note": "Rangacharya formula pending source-card implementation",
    }


def calc_rangacharya_variant(asc_sign_idx: int, planet_longitudes: Mapping[str, float]) -> Dict[str, Any]:
    asc_sign_idx %= 12
    arudha_padas = {
        "AL": _placeholder_pada("AL", asc_sign_idx, 1),
        "A7": _placeholder_pada("A7", asc_sign_idx, 7),
        "A10": _placeholder_pada("A10", asc_sign_idx, 10),
        "UL": _placeholder_pada("UL", asc_sign_idx, 12),
    }
    return {
        "variant": "rangacharya",
        "status": "experimental_not_for_adjudication",
        "adjudication_enabled": False,
        "source_status": "transcribed",
        "active_lagna": {
            "sign": _sign_name(asc_sign_idx),
            "validation_status": "transcribed",
            "adjudication_enabled": False,
        },
        "effective_lagna": {
            "sign": _sign_name(asc_sign_idx),
            "validation_status": "transcribed",
            "adjudication_enabled": False,
        },
        "arudha_padas": arudha_padas,
        "input_planets_present": sorted(planet_longitudes),
    }


def _flatten(prefix: str, value: Any) -> Dict[str, Any]:
    if not isinstance(value, dict):
        return {prefix: value}
    rows: Dict[str, Any] = {}
    for key, child in value.items():
        child_key = f"{prefix}.{key}" if prefix else str(key)
        rows.update(_flatten(child_key, child))
    return rows


def diff_current_vs_rangacharya(current: Mapping[str, Any], variant: Mapping[str, Any]) -> Dict[str, Any]:
    current_flat = _flatten("", dict(current))
    variant_flat = _flatten("", dict(variant.get("arudha_padas", variant)))
    differences = []
    for key in sorted(set(current_flat) | set(variant_flat)):
        current_value = current_flat.get(key)
        variant_value = variant_flat.get(key)
        if current_value != variant_value:
            differences.append({"key": key, "current": current_value, "rangacharya": variant_value})
    return {
        "current_algorithm": "current_jaimini",
        "variant_algorithm": "rangacharya",
        "adjudication_enabled": False,
        "differences": differences,
    }
```

- [ ] **Step 4: Run tests**

Run:

```bash
python3 -m pytest tests/test_rangacharya_variant.py -q
```

- [ ] **Step 5: Commit**

Stage only `scripts/rangacharya.py` and `tests/test_rangacharya_variant.py`.

---

### Task 3: API Exposure Without Changing Current Defaults

**Files:**
- Modify: `scripts/jyotish_api_server.py`
- Create: `tests/test_jaimini_rangacharya_api.py`

- [ ] **Step 1: Write endpoint contract tests**

Create `tests/test_jaimini_rangacharya_api.py` using the existing API test helper style in nearby tests. Assert:

```python
def test_jaimini_default_does_not_include_rangacharya(client):
    response = client.post("/api/jaimini", json={"ascendant": 0, "planets": []})
    data = response.get_json()
    assert "rangacharya" not in data["result"]


def test_jaimini_variant_all_includes_current_variant_and_diff(client):
    response = client.post("/api/jaimini", json={
        "ascendant": 0,
        "variant": "all",
        "mode": "arudha",
        "planets": [
            {"name": "Sun", "longitude": 10},
            {"name": "Moon", "longitude": 45},
            {"name": "Mars", "longitude": 80},
            {"name": "Mercury", "longitude": 110},
            {"name": "Jupiter", "longitude": 145},
            {"name": "Venus", "longitude": 200},
            {"name": "Saturn", "longitude": 250}
        ]
    })
    data = response.get_json()
    assert data["result"]["rangacharya"]["adjudication_enabled"] is False
    assert data["result"]["rangacharya_diff"]["adjudication_enabled"] is False
```

If existing test fixtures use a different client factory, copy that local pattern exactly.

- [ ] **Step 2: Run test, verify failure**

Run:

```bash
python3 -m pytest tests/test_jaimini_rangacharya_api.py -q
```

- [ ] **Step 3: Add optional variant handling**

In `scripts/jyotish_api_server.py::_compute_jaimini`:

```python
variant = body.get("variant", "current")
if not isinstance(variant, str):
    raise BadRequest("variant must be a string")
variant = variant.strip().lower() or "current"
allowed_variants = {"current", "rangacharya", "all"}
if variant not in allowed_variants:
    raise BadRequest(f'variant must be one of: {", ".join(sorted(allowed_variants))}')
```

After current arudha calculation:

```python
if variant in ("rangacharya", "all"):
    rangacharya = _load_local_module("rangacharya")
    rangacharya_result = rangacharya.calc_rangacharya_variant(asc_sign_idx, planet_lons)
    result["rangacharya"] = rangacharya_result
    current_arudha = result.get("arudha_padas") or jaimini.calc_arudha_padas(asc_sign_idx, planet_lons)
    result["rangacharya_diff"] = rangacharya.diff_current_vs_rangacharya(current_arudha, rangacharya_result)
```

Preserve default `variant=current`, so existing clients do not see new fields.

- [ ] **Step 4: Run focused tests**

Run:

```bash
python3 -m pytest tests/test_jaimini_rangacharya_api.py tests/test_jaimini.py -q
```

- [ ] **Step 5: Commit**

Stage only API/test files touched in this task.

---

### Task 4: Adjudication Guard

**Files:**
- Create: `tests/test_rangacharya_adjudication_guard.py`
- Modify: `scripts/rangacharya.py`

- [ ] **Step 1: Write guard tests**

Create `tests/test_rangacharya_adjudication_guard.py`:

```python
import pytest

from scripts import rangacharya


def test_assert_adjudication_allowed_rejects_default_variant():
    result = rangacharya.calc_rangacharya_variant(0, {"Sun": 10.0})
    with pytest.raises(rangacharya.RangacharyaValidationError):
        rangacharya.assert_adjudication_allowed(result)


def test_validation_summary_lists_blocking_rules():
    result = rangacharya.calc_rangacharya_variant(0, {"Sun": 10.0})
    summary = rangacharya.validation_summary(result)
    assert summary["adjudication_enabled"] is False
    assert summary["blocking_statuses"]
```

- [ ] **Step 2: Run test, verify failure**

Run:

```bash
python3 -m pytest tests/test_rangacharya_adjudication_guard.py -q
```

- [ ] **Step 3: Add guard functions**

Add to `scripts/rangacharya.py`:

```python
class RangacharyaValidationError(RuntimeError):
    pass


def validation_summary(result: Mapping[str, Any]) -> Dict[str, Any]:
    statuses = []
    for row in _flatten("", dict(result)).items():
        key, value = row
        if key.endswith("validation_status"):
            statuses.append(str(value))
    blocking = sorted({status for status in statuses if status != "adjudication_enabled"})
    return {
        "adjudication_enabled": bool(result.get("adjudication_enabled")) and not blocking,
        "blocking_statuses": blocking,
    }


def assert_adjudication_allowed(result: Mapping[str, Any]) -> None:
    summary = validation_summary(result)
    if not summary["adjudication_enabled"]:
        raise RangacharyaValidationError(
            "Rangacharya variant is not adjudication-enabled; validation gates are incomplete"
        )
```

- [ ] **Step 4: Run tests**

Run:

```bash
python3 -m pytest tests/test_rangacharya_adjudication_guard.py tests/test_rangacharya_variant.py -q
```

- [ ] **Step 5: Commit**

Stage only guard files.

---

### Task 5: VedAstro Closure Status Hook

**Files:**
- Modify: existing VedAstro gateway/status module found by `rg -n "official_closure_state|VedAstro Raw Archive Manifest|gateway_status" scripts tests`
- Modify/Create: focused VedAstro status test

- [ ] **Step 1: Locate existing contract**

Run:

```bash
rg -n "official_closure_state|VedAstro Raw Archive Manifest|gateway_status|official_raw_response" scripts tests
```

Use the current status function rather than adding a parallel gateway.

- [ ] **Step 2: Write failing test for env-only key and blocked raw**

In the existing VedAstro status test file, add a test equivalent to:

```python
def test_vedastro_closure_status_never_exposes_secret(monkeypatch):
    monkeypatch.setenv("VEDASTRO_API_KEY", "sk_live_test_secret")
    status = gateway_status()
    text = json.dumps(status, sort_keys=True)
    assert "sk_live_test_secret" not in text
    assert status["official_closure_state"] in {
        "official_verified",
        "official_raw_missing_or_unverified",
        "blocked",
        "not_configured",
    }
```

Adapt imports to the existing module.

- [ ] **Step 3: Implement minimal redaction/status preservation**

If status currently includes env values, replace with booleans:

```python
"credential_configured": bool(os.environ.get("VEDASTRO_API_KEY")),
```

Never include key contents. If no official raw response exists, set:

```python
"official_closure_state": "official_raw_missing_or_unverified"
```

- [ ] **Step 4: Run focused VedAstro tests**

Run:

```bash
python3 -m pytest tests/test_vedastro_service_adapter_executor.py tests/test_vedastro_official_mcp_bridge.py -q
```

If these are too broad, run only the specific test nodes touched and record that full files were not run.

- [ ] **Step 5: Commit**

Stage only VedAstro status/test files touched in this task.

---

### Task 6: Documentation And Planning Sync

**Files:**
- Modify: `.planning/rangacharya_vedastro_design_20260716/task_plan.md`
- Modify: `.planning/rangacharya_vedastro_design_20260716/progress.md`
- Modify: `.planning/rangacharya_vedastro_design_20260716/findings.md` if new facts appear

- [ ] **Step 1: Update planning state**

Mark design/planning complete and implementation pending/executing according to actual state.

- [ ] **Step 2: Run mandatory pre-work and focused tests**

Run:

```bash
python3 scripts/pre_work_check.py --remote-timeout 8 --command-timeout 45
python3 -m pytest tests/test_rangacharya_source_manifest.py tests/test_rangacharya_variant.py tests/test_rangacharya_adjudication_guard.py tests/test_jaimini_rangacharya_api.py -q
```

- [ ] **Step 3: Final verify no secret leakage**

Run:

```bash
rg -n "sk_live_|VEDASTRO_API_KEY=.*sk_|api_key.*sk_" references scripts tests docs .planning
```

Expected: no real user secret. Existing synthetic examples are acceptable only if already present and clearly fake.

- [ ] **Step 4: Commit or report uncommitted state**

If asked to commit, stage only files from this plan. Otherwise leave changes unstaged and report exact files changed.
