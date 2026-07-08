# Dignity Guardrail v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a domain-aware `dignity_guardrail` to `relationship` and `finance` strict workflows, while also freezing a fragment-source map so high-value orphaned materials do not stay scattered across repo drafts, Gemini brain notes, and synced copies.

**Architecture:** First, write a small source-of-truth artifact that records where high-value fragments live and which locations are authoritative versus draft-only. Then replace the current full-chart dignity broadcast in `mcp_server.py` with a helper-driven `dignity_guardrail` that reads only D1 `chart.planets.status`, uses route-specific relevant planets, and applies at most one bounded score adjustment. Finally, verify that strict workflow outputs still preserve existing label boundaries.

**Tech Stack:** Python, pytest, Markdown design/research docs, existing `mcp_server.py` strict workflow helpers

## Global Constraints

- Follow `<repo>/docs/superpowers/specs/2026-06-28-dignity-guardrail-v1-design.md` exactly.
- Do not use D9, D10, Vimsopaka, or any divisional dignity in v1.
- Do not let dignity logic change `dominant_label`, `primary_drivers`, `wealth_promise_strength`, `jaimini_marriage_support`, or `avayogi_risk`.
- Keep dignity score impact bounded to a single `-5 | 0 | +5`.
- Do not leave “whole-chart dignity scan” logic inline in `_derive_event_judgement`.
- Use `apply_patch` for file edits.
- Do not disturb unrelated dirty-worktree files.

---

### Task 1: Freeze The Fragment Source Map

**Files:**
- Create: `<repo>/docs/research/high_value_fragment_source_map_2026_06_28.md`
- Modify: `<repo>/docs/research/ACTIVE_FRONTS.md`
- Test: none

**Interfaces:**
- Consumes: current repo research docs, `<home>/.gemini/antigravity-ide/brain/*`, `<home>/.workbuddy/skills/jyotish-vedic-astrology`, and existing sweep/audit reports
- Produces: a documented source hierarchy with four buckets: `main_repo_truth`, `repo_local_drafts`, `external_work_brain`, `synced_distribution_copy`

- [ ] **Step 1: Write the fragment map document**

```markdown
# High-Value Fragment Source Map - 2026-06-28

## Goal

Prevent high-value Jyotish research and implementation notes from remaining scattered across multiple work surfaces.

## Authority Tiers

### 1. Main Repo Truth

- `<repo>/SKILL.md`
- `<repo>/AGENTS.md`
- `<repo>/references/`
- `<repo>/scripts/`
- `<repo>/tests/`
- `<repo>/docs/research/` (committed reports only)

Rule:
- This is the only layer allowed to define current product truth.

### 2. Repo Local Drafts

- `<repo>/docs/research/local_drafts/2026-06/`

Rule:
- High-value but draft-only. Must be promoted deliberately into committed docs or code.

### 3. External Work Brain

- `<home>/.gemini/antigravity-ide/brain/*`
- `<home>/.codex/attachments/*`

Rule:
- Useful for recovery, comparison, and archaeology. Never authoritative by default.

### 4. Synced Distribution Copy

- `<home>/.workbuddy/skills/jyotish-vedic-astrology`

Rule:
- Distribution target only. Must never be reverse-copied over repo truth.

## Highest-Value Orphaned Assets Identified

- VedAstro capability audit notes in Gemini brain
- local draft Yogi/Tajika/oracle closure packs
- WorkBuddy-only benchmark references that need parity checks
- pending oracle case packets under `references/oracle/artifacts/pending_packets/`

## Required Working Rule

Before feature work, scan:

1. repo truth
2. repo local drafts
3. Gemini brain / Codex attachments
4. WorkBuddy copy

Then record whether any high-value fragment needs promotion.
```

- [ ] **Step 2: Add a short operator reminder to ACTIVE_FRONTS**

```markdown
## Fragment Discipline

- Before touching strict workflow or adjudicator logic, check the fragment source map:
  - `<repo>/docs/research/high_value_fragment_source_map_2026_06_28.md`
- Treat repo truth as authoritative.
- Treat `docs/research/local_drafts`, Gemini brain notes, and WorkBuddy copies as candidate sources only.
```

- [ ] **Step 3: Review the new doc for contradictions**

Run a manual read of:
- `<repo>/docs/research/high_value_fragment_source_map_2026_06_28.md`
- `<repo>/docs/research/ACTIVE_FRONTS.md`

Expected:
- The authority tiers do not conflict with the existing sweep/audit reports.

- [ ] **Step 4: Commit the fragment-map task**

```bash
git add <repo>/docs/research/high_value_fragment_source_map_2026_06_28.md <repo>/docs/research/ACTIVE_FRONTS.md
git commit -m "Document high-value fragment source map"
```

### Task 2: Add Failing Tests For Dignity Guardrail Boundaries

**Files:**
- Modify: `<repo>/tests/test_mcp_strict_workflow_relationship.py`
- Modify: `<repo>/tests/test_mcp_strict_workflow_finance.py`
- Test: same files

**Interfaces:**
- Consumes: `_collect_strict_evidence`, `_derive_event_judgement`
- Produces: regression coverage for `dignity_guardrail`

- [ ] **Step 1: Add relationship non-relevant-planet failing test**

```python
def test_relationship_dignity_guardrail_ignores_non_relevant_planets() -> None:
    result = _base_relationship_result()
    result["modules"]["chart"] = {
        "ascendant": {"sign": "Leo"},
        "planets": {
            "Mars": {"status": "落陷取消(Neecha Bhanga)"},
            "Venus": {"status": "中性(Neutral)"},
            "Jupiter": {"status": "中性(Neutral)"},
            "Saturn": {"status": "极敌(Great Enemy)"},
        },
    }

    strict = _collect_strict_evidence("relationship", result)

    assert strict["present_evidence"]["dignity_guardrail"]["score_delta"] == 0
    assert strict["event_judgement"]["dominant_label"] == "legal_marriage"
```

- [ ] **Step 2: Add relationship relevant-signal failing test**

```python
def test_relationship_dignity_guardrail_uses_relevant_planets_only() -> None:
    result = _base_relationship_result()
    result["modules"]["chart"] = {
        "ascendant": {"sign": "Aries"},
        "planets": {
            "Venus": {"status": "落陷取消(Neecha Bhanga)"},
            "Jupiter": {"status": "中性(Neutral)"},
            "Saturn": {"status": "极敌(Great Enemy)"},
        },
    }

    strict = _collect_strict_evidence("relationship", result)

    assert strict["present_evidence"]["dignity_guardrail"]["score_delta"] == 5
    assert "dignity_supportive_recovery" in strict["event_judgement"]["secondary_context"]
```

- [ ] **Step 3: Add finance guardrail conflict failing test**

```python
def test_finance_dignity_guardrail_conflict_caps_to_zero_delta() -> None:
    result = {
        "modules": {
            "varga_full": {"D2_Hora": {"summary": "ok"}, "D10_Dasamsa": {"summary": "ok"}},
            "shadbala": {"planets": {"Venus": {"total_rupa": 8.2}}},
            "ashtakavarga": {"house_scores": {"2": 31, "11": 36}},
            "chart": {
                "ascendant": {"sign": "Leo"},
                "planets": {
                    "Mercury": {"status": "落陷取消(Neecha Bhanga)"},
                    "Moon": {"status": "极敌(Great Enemy)"},
                    "Venus": {"status": "中性(Neutral)"},
                    "Jupiter": {"status": "中性(Neutral)"},
                },
            },
            "dasha": {"current_dasha": {"mahadasha": "Venus", "antardasha": "Mercury"}},
            "narayana_dasha": {"current_dasha": {"sign": "Taurus", "lord": "Venus"}},
            "dasa_convergence": {
                "domain_activations": {
                    "wealth_family": {"convergence_level": "L1", "probability": "+15-20%"},
                    "gains_wishes": {"convergence_level": "L1", "probability": "+15-20%"},
                    "career_status": {"convergence_level": "L1", "probability": "+15-20%"},
                }
            },
        }
    }

    strict = _collect_strict_evidence("finance", result)

    assert strict["present_evidence"]["dignity_guardrail"]["status"] == "conflict"
    assert strict["present_evidence"]["dignity_guardrail"]["score_delta"] == 0
    assert "dignity_conflict" in strict["event_judgement"]["secondary_context"]
```

- [ ] **Step 4: Run targeted tests and confirm failure**

Run:
`pytest tests/test_mcp_strict_workflow_relationship.py tests/test_mcp_strict_workflow_finance.py -q`

Expected:
- FAIL because `dignity_guardrail` does not exist yet and current code still applies whole-chart scan.

- [ ] **Step 5: Commit failing tests**

```bash
git add <repo>/tests/test_mcp_strict_workflow_relationship.py <repo>/tests/test_mcp_strict_workflow_finance.py
git commit -m "Add dignity guardrail boundary tests"
```

### Task 3: Implement `_derive_dignity_guardrail`

**Files:**
- Modify: `<repo>/mcp_server.py`
- Test: `<repo>/tests/test_mcp_strict_workflow_relationship.py`
- Test: `<repo>/tests/test_mcp_strict_workflow_finance.py`

**Interfaces:**
- Consumes: route string, `present` evidence, D1 chart status
- Produces: `dict` shaped like `dignity_guardrail` contract

- [ ] **Step 1: Add helper skeleton near other evidence bridges**

```python
def _derive_dignity_guardrail(route: str, present: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "route": route,
        "status": "blocked",
        "score_delta": 0,
        "source": "chart.planets.status",
        "relevant_planets": [],
        "ignored_planets": [],
        "conflict_flags": [],
        "notes": ["Only domain-relevant planets are allowed to affect score."],
    }
```

- [ ] **Step 2: Add route-specific lord resolution helpers**

```python
def _sign_to_index(sign: str) -> int | None:
    try:
        return _SIGNS.index(sign)
    except ValueError:
        return None


def _lord_for_house_from_lagna(asc_sign: str, house_num: int) -> Optional[str]:
    asc_idx = _sign_to_index(asc_sign)
    if asc_idx is None:
        return None
    sign = _SIGNS[(asc_idx + house_num - 1) % 12]
    return _SIGN_LORDS.get(sign)
```

- [ ] **Step 3: Implement relevant-planet selection**

```python
if route == "relationship":
    names = {lord_7, "Venus", "Jupiter"}
    darakaraka = present.get("darakaraka")
    if isinstance(darakaraka, dict) and darakaraka.get("planet"):
        names.add(darakaraka["planet"])
elif route == "finance":
    names = {lord_2, lord_11, "Venus", "Jupiter"}
    if present.get("career_convergence"):
        names.add(lord_10)
else:
    names = set()
```

- [ ] **Step 4: Implement score-resolution rules from the spec**

```python
supportive = []
friction = []
for planet_name, pdata in planets.items():
    if planet_name not in names:
        ignored.append({"planet": planet_name, "reason": "not_domain_relevant"})
        continue
    status = str(pdata.get("status", ""))
    code = "NEECHA_BHANGA" if "Neecha Bhanga" in status or "落陷取消" in status else \
           "GREAT_ENEMY" if "Great Enemy" in status or "极敌" in status else None
    if code == "NEECHA_BHANGA":
        supportive.append(planet_name)
    elif code == "GREAT_ENEMY":
        friction.append(planet_name)
```

- [ ] **Step 5: Return final contract structure**

```python
if supportive and friction:
    status = "conflict"
    score_delta = 0
elif supportive:
    status = "caution"
    score_delta = 5
elif friction:
    status = "caution"
    score_delta = -5
else:
    status = "ok"
    score_delta = 0
```

- [ ] **Step 6: Run targeted tests and confirm partial pass**

Run:
`pytest tests/test_mcp_strict_workflow_relationship.py tests/test_mcp_strict_workflow_finance.py -q`

Expected:
- Some tests still fail until integration removes the old whole-chart scan.

- [ ] **Step 7: Commit helper implementation**

```bash
git add <repo>/mcp_server.py
git commit -m "Add dignity guardrail helper"
```

### Task 4: Wire `dignity_guardrail` Into Strict Evidence And Judgement

**Files:**
- Modify: `<repo>/mcp_server.py`
- Test: `<repo>/tests/test_mcp_strict_workflow_relationship.py`
- Test: `<repo>/tests/test_mcp_strict_workflow_finance.py`

**Interfaces:**
- Consumes: `present["dignity_guardrail"]`
- Produces: bounded score impact and bounded `secondary_context`

- [ ] **Step 1: Add `dignity_guardrail` to relationship evidence collection**

```python
present["dignity_guardrail"] = _derive_dignity_guardrail(route, present)
```

- [ ] **Step 2: Add `dignity_guardrail` to finance evidence collection**

```python
present["dignity_guardrail"] = _derive_dignity_guardrail(route, present)
```

- [ ] **Step 3: Remove inline whole-chart dignity scan from relationship judgement**

```python
guardrail = present.get("dignity_guardrail") or {}
score += guardrail.get("score_delta", 0)
```

- [ ] **Step 4: Remove inline whole-chart dignity scan from finance judgement**

```python
guardrail = present.get("dignity_guardrail") or {}
score += guardrail.get("score_delta", 0)
```

- [ ] **Step 5: Add bounded context strings**

```python
if guardrail.get("status") == "conflict":
    secondary_context.append("dignity_conflict")
elif guardrail.get("score_delta") == 5:
    secondary_context.append("dignity_supportive_recovery")
elif guardrail.get("score_delta") == -5:
    secondary_context.append("dignity_high_friction")
```

- [ ] **Step 6: Apply confidence-cap downgrade for conflict**

```python
if present.get("dignity_guardrail", {}).get("status") == "conflict":
    confidence_cap = "low" if confidence_cap != "low" else confidence_cap
```

- [ ] **Step 7: Verify labels stay untouched**

Run:
`pytest tests/test_mcp_strict_workflow_relationship.py tests/test_mcp_strict_workflow_finance.py -q`

Expected:
- PASS, with `dominant_label` and payout logic unchanged except bounded context/score updates.

- [ ] **Step 8: Commit the route integration**

```bash
git add <repo>/mcp_server.py <repo>/tests/test_mcp_strict_workflow_relationship.py <repo>/tests/test_mcp_strict_workflow_finance.py
git commit -m "Wire dignity guardrail into strict workflows"
```

### Task 5: Verify Engine Boundary And Record Follow-Up

**Files:**
- Create: `<repo>/docs/research/dignity_guardrail_v1_boundary_audit_2026_06_28.md`
- Modify: `<repo>/docs/research/ACTIVE_FRONTS.md`
- Test: optional targeted engine sanity commands

**Interfaces:**
- Consumes: final implementation and current engine state
- Produces: audit note plus explicit follow-up that divisional dignity and functional-role bridge remain separate work

- [ ] **Step 1: Write the boundary audit**

```markdown
# Dignity Guardrail v1 Boundary Audit - 2026-06-28

## What Landed

- `dignity_guardrail` added to `relationship` and `finance`
- D1 `chart.planets.status` only
- route-relevant planets only
- bounded `-5 | 0 | +5`

## What Did Not Land

- no D9/D10/Vimsopaka dignity scoring
- no dominant label lifting
- no Functional Benefic/Malefic merge

## Known Follow-Ups

1. Fix divisional dignity data-flow separately in `scripts/jyotish_engine.py`
2. Build `functional_role_guardrail`
3. Review whether `GREAT_FRIEND` deserves bounded context-only semantics later
```

- [ ] **Step 2: Add the follow-up item to ACTIVE_FRONTS**

```markdown
- Dignity guardrail v1 landed as D1-only route guardrail; divisional dignity repair and functional-role bridge remain separate fronts.
```

- [ ] **Step 3: Run verification commands**

Run:
- `pytest tests/test_mcp_strict_workflow_relationship.py -q`
- `pytest tests/test_mcp_strict_workflow_finance.py -q`

Expected:
- PASS

- [ ] **Step 4: Commit the audit**

```bash
git add <repo>/docs/research/dignity_guardrail_v1_boundary_audit_2026_06_28.md <repo>/docs/research/ACTIVE_FRONTS.md
git commit -m "Audit dignity guardrail v1 boundary"
```
