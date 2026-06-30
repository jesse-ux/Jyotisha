# VedAstro Official Hard-Override Design

Date: 2026-06-30
Status: Draft for user review
Scope: `relationship + career + wealth` default workflow

## Decision

Use方案 C: `VedAstro official -> local supplemental -> local fallback`.

This design changes the default data authority of the project:

1. If VedAstro official data exists for a field or section, it becomes the primary user-visible source.
2. Local modules may supplement, cross-check, or explain official data, but may not silently overwrite it.
3. Local fallback is allowed only when the official section is blocked, missing, or explicitly partial for that specific requirement.

This is a workflow decision, not a claim that every one of the 641 catalogued VedAstro callables runs on every chart.

## Goal

Make the `relationship`, `career`, and `wealth` workflows default to VedAstro official evidence first, while still preserving the project's high-rigor local layers:

- marriage: `D9 + UL + DK + Vimshottari + Narayana + Functional Benefic/Malefic`
- career: `D10 + A10 + Vimshottari + Narayana + Functional Benefic/Malefic`
- wealth: `D2 / D11 + Vimshottari + Narayana + Functional Benefic/Malefic`

The user should be able to provide birth data once and receive a report that clearly distinguishes:

- official primary evidence
- local supplemental evidence
- local fallback use
- blocked items
- conflicts
- confidence cap

## Current State

The repository already contains real VedAstro integration building blocks:

- `scripts/vedastro_python_bridge.py`
  - lists the official callable catalog and can execute official point methods
- `scripts/vedastro_service_adapter.py`
  - executes official snapshot and range-scan requests with cache/limits
- `scripts/vedastro_evidence_orchestrator.py`
  - orchestrates official full snapshot plus domain scans
- `scripts/vedastro_priority.py`
  - applies project-wide source priority metadata
- `scripts/jyotish_engine.py`
  - attaches official full snapshot into `full-reading`
- `scripts/jyotish_api_server.py`
  - exposes chart/high-rigor routes and some source-priority metadata

However, the current state is still not a closed official-first product workflow:

1. `relationship`, `career`, and `wealth` are not yet all driven through one enforced official-first adjudication contract.
2. official vs local conflicts are not consistently surfaced as first-class output.
3. local timing and interpretation modules can still appear as if they are primary even when official data exists.
4. theme-specific required layers are not uniformly hard-gated with `blocked` or `confidence_cap` downgrade.

## Problem Statement

The project currently risks three kinds of misleading output:

1. **silent override**
   - local values or narratives appear to replace official results without explicitly saying so
2. **incomplete rigor**
   - a workflow returns a theme conclusion without all required local high-rigor layers attached
3. **hidden conflict**
   - official and local systems materially disagree, but the user only sees one side

Examples already observed in this repo context include:

- official `DasaAtTime` vs local Vimshottari timeline disagreement
- Darakaraka disagreement across different local calculation paths
- official event radar being partial/blocked while the user-visible analysis still reads too definitive

## Non-Goals

This design explicitly does not do the following:

- claim that all 641 VedAstro catalog items are executed for every single question
- expose hundreds of raw official nodes directly to ordinary end users
- replace local Narayana Dasha, UL, A10, D11, or Functional Benefic/Malefic with official stubs when VedAstro does not provide equivalent structure
- hide or smooth over official/local disagreement to make reports sound cleaner
- treat internal consistency alone as proof of external correctness

## Section 1: Authority Model

### Global Priority Rule

Every default workflow must use this exact priority order:

1. `vedastro_official_primary`
2. `local_supplemental`
3. `local_fallback_only_when_official_blocked`

### Hard Rules

- If the official section exists and is usable, local output may not replace its numeric or structural value.
- If the local system adds interpretation, that interpretation must point back to the official source section it depends on.
- If the official section is blocked, the workflow may fall back locally, but must say so explicitly.
- If the official section is partial, the workflow may combine official and local output, but must label the local contribution as supplemental or fallback per field.

### Required User-Visible Metadata

Each theme result must expose at least:

```json
{
  "source_priority_mode": "vedastro_official_primary | local_fallback_official_blocked",
  "official_primary_evidence": {},
  "local_supplemental_evidence": {},
  "fallback_used": [],
  "blocked_items": [],
  "conflicts": [],
  "confidence_cap": "high | medium | low | blocked"
}
```

## Section 2: High-Rigor Constraints

This design must obey the repository hard constraints in `AGENTS.md`.

### Theme Requirements

**Relationship**

- required official-first layers:
  - official D1/D9 core when available
  - official current Dasha/timing section when available
  - official relationship event radar when available
- required local layers:
  - `UL`
  - `DK`
  - `Narayana Dasha`
  - `Functional Benefic/Malefic`

**Career**

- required official-first layers:
  - official D1/D10 core when available
  - official current Dasha/timing section when available
  - official career event radar when available
- required local layers:
  - `A10`
  - `Narayana Dasha`
  - `Functional Benefic/Malefic`

**Wealth**

- required official-first layers:
  - official D1/D2/D11 core when available
  - official current Dasha/timing section when available
  - official wealth event radar when available
- required local layers:
  - `D11 income-structure explanation`
  - `Narayana Dasha`
  - `Functional Benefic/Malefic`

### Hard-Gate Rule

If a required local high-rigor layer is missing, the workflow may still return a structured response, but it may not present the theme as fully rigorous.

Minimum rule:

- required official layer blocked + no valid local fallback => `confidence_cap = blocked`
- official layer partial + required local supplement missing => `confidence_cap = low`
- official layer present + local supplement present + no unresolved conflict => confidence may rise above `low`

## Section 3: Shared Orchestration Contract

### Single Entry Point

The project should stop letting each theme silently assemble evidence in separate ways.

A shared official-first orchestration layer will:

1. fetch or reuse the official full snapshot
2. carry official capability catalog metadata
3. resolve theme-specific official dynamic selections
4. attach domain radar / range-scan evidence
5. hand the result to theme adjudicators
6. append local supplemental layers
7. compute conflict and confidence state

### Intended File Roles

- `scripts/vedastro_evidence_orchestrator.py`
  - official-first orchestration root
- `scripts/vedastro_priority.py`
  - source-priority metadata and official/fallback chart policy
- `scripts/jyotish_engine.py`
  - strict evidence collectors and user-visible narrative payloads
- `scripts/jyotish_api_server.py`
  - default API entrypoints for `relationship`, `career`, `wealth`, and `high_rigor_workflow`

## Section 4: Theme Adjudication Model

### Relationship

Primary rule:

- official relationship data leads
- local marriage-specific structure supplements

Expected result shape:

```json
{
  "theme": "relationship",
  "official_primary_evidence": {
    "chart_core": "official",
    "d9": "official_when_available",
    "dasha": "official_when_available",
    "event_radar": "official_when_available"
  },
  "local_supplemental_evidence": {
    "upapada_lagna": "required",
    "darakaraka": "required",
    "narayana_dasha": "required",
    "functional_benefic_malefic": "required"
  }
}
```

### Career

Primary rule:

- official career timing and chart structure lead
- local A10 and career interpretation explain the official window

Expected result shape:

```json
{
  "theme": "career",
  "official_primary_evidence": {
    "chart_core": "official",
    "d10": "official_when_available",
    "dasha": "official_when_available",
    "event_radar": "official_when_available"
  },
  "local_supplemental_evidence": {
    "a10": "required",
    "narayana_dasha": "required",
    "functional_benefic_malefic": "required"
  }
}
```

### Wealth

Primary rule:

- official wealth timing and divisional structure lead
- local D11-style income explanation and second-track timing supplement the meaning

Expected result shape:

```json
{
  "theme": "wealth",
  "official_primary_evidence": {
    "chart_core": "official",
    "d2_d11": "official_when_available",
    "dasha": "official_when_available",
    "event_radar": "official_when_available"
  },
  "local_supplemental_evidence": {
    "narayana_dasha": "required",
    "functional_benefic_malefic": "required",
    "wealth_structure_explainer": "required"
  }
}
```

## Section 5: Conflict Arbitration

### Rule

The workflow must not silently choose one side when official and local evidence materially disagree.

Instead, it must record:

- which side is primary
- which side is supplemental
- whether the disagreement affects timing, event class, or structural interpretation
- whether confidence must be downgraded

### Initial Conflict Classes

1. `official_local_dasha_conflict`
2. `darakaraka_method_conflict`
3. `official_local_divisional_conflict`
4. `official_event_radar_missing_or_partial`
5. `functional_natural_malefic_conflict`

### Minimum Conflict Payload

```json
{
  "type": "official_local_dasha_conflict",
  "primary_source": "vedastro_official",
  "supplemental_source": "local_module",
  "impact": "timing",
  "resolution": "keep_official_primary_and_downgrade_confidence",
  "details": {}
}
```

### Confidence Rules

- official blocked + no adequate fallback => `blocked`
- official present but major unresolved conflict => at most `low`
- official present + supplemental present + minor conflict only => at most `medium`
- only when official present and required local rigor layers are present and coherent may the theme exceed `medium`

This design intentionally prefers honesty over certainty inflation.

## Section 6: Report And API Contract

### API

The `relationship`, `career`, `wealth`, and `high_rigor_workflow` outputs must expose a consistent evidence contract.

At minimum:

```json
{
  "theme": "relationship",
  "source_priority": {
    "mode": "vedastro_official_primary",
    "priority": [
      "vedastro_official_snapshot",
      "local_supplemental_modules",
      "local_fallback_only_when_official_blocked"
    ]
  },
  "official_primary_evidence": {},
  "local_supplemental_evidence": {},
  "fallback_used": [],
  "blocked_items": [],
  "conflicts": [],
  "confidence_cap": "low"
}
```

### Frontend

The frontend should not merely display a summary sentence.

It must be able to show:

- official source used
- local supplemental modules used
- fallback items
- blocked items
- conflict list
- confidence cap

This is required so a user can tell whether a conclusion is fully official-led, mixed, or mostly fallback.

## Section 7: Reuse Strategy

This design should reuse existing project code first.

Preferred reuse targets include:

- `scripts/vedastro_evidence_orchestrator.py`
- `scripts/vedastro_priority.py`
- `scripts/jyotish_engine.py`
- `scripts/jyotish_api_server.py`
- existing strict evidence collectors
- existing `historical_event_backtest.py`
- existing theme/report orchestration files

Avoid introducing a second parallel official-first workflow if the existing files can be extended safely.

## Section 8: Testing Requirements

Implementation must start with failing tests first.

### Required Verification Areas

1. **Official-first routing**
   - each theme uses official primary evidence when available
2. **No silent overwrite**
   - local modules do not replace official values when official sections exist
3. **Supplement labeling**
   - local layers are marked supplemental rather than primary
4. **Fallback honesty**
   - blocked official sections trigger explicit fallback labels
5. **Conflict honesty**
   - major disagreements lower confidence and surface conflict rows
6. **Theme hard-gates**
   - missing UL/A10/D11/Narayana/Functional Benefic-Malefic lowers or blocks rigor state as designed
7. **User evidence trail**
   - the final response can show where each major conclusion came from

### Out of Scope For This Design

- full global calibration of every VedAstro event method
- proving historical accuracy across all 641 official capabilities
- completing every unresolved external oracle closure

## Section 9: Release Boundary

This design is considered complete only when:

1. the three default theme workflows are consistently official-first
2. local modules are labeled supplemental or fallback correctly
3. major conflicts are surfaced instead of hidden
4. `blocked` and `confidence_cap` states are honest
5. API and frontend can both consume the same evidence contract

This design is not complete merely because:

- the official capability catalog is listed
- a backend script can call some official methods
- a route returns source-priority metadata without enforcing it through the theme outputs

## Open Risks

- VedAstro official sections may remain partial for some charts or some timing/event layers
- official and local dasha methods may continue to disagree until deeper alignment work is done
- some local modules may rely on legacy assumptions that were acceptable in local-first mode but become misleading in official-first mode

Those risks must remain visible in the product output until resolved. They may not be hidden behind a polished narrative.
