# Divisional Dignity Context Repair Audit (2026-06-28)

## What Landed

This pass repairs a specific boundary bug in `/Users/wuyongnaren/Documents/印度占星/scripts/jyotish_engine.py`:

- `full-reading.modules.d9_navamsa_expanded[*].dignity`
- `full-reading.modules.jaimini.darakaraka.d9_dignity`
- `full-reading.modules.vimsopaka[*].varga_scores.Navamsa.dignity`

were previously calling `_get_dignity_level(...)` with natal `D1 planets` as `planets_data`, even when the dignity being judged belonged to `D9` or another varga.

This pass adds `_build_dignity_context(chart_data)` and routes divisional dignity calls through the current chart context instead of borrowing `D1`.

## Root Cause

The helper `_get_dignity_level(planet, sign, deg_in_sign, planets_data)` was already context-sensitive:

- temporary friendship (`Tatkalika Maitri`)
- compound friendship (`Panchadha Maitri`)
- `Neecha Bhanga`

all depend on the `planets_data` passed in.

The bug was not in the helper itself. The bug was in the callers that fed `D1 planets` into divisional dignity paths.

## Regression Cases Locked

### 1. D9 expanded dignity uses D9 context

Case:

- `1990-01-01 12:00`
- `lat=39.9`
- `lon=116.4`
- `tz=8`

Expected:

- `modules.d9_navamsa_expanded.Jupiter.sign == Capricorn`
- `modules.d9_navamsa_expanded.Jupiter.dignity == NEECHA_BHANGA`

Before fix:

- dignity incorrectly surfaced as `DEBILITATED`

### 2. Darakaraka D9 dignity uses D9 context

Case:

- `1992-08-25 23:10`
- `lat=35.6895`
- `lon=139.6917`
- `tz=9`

Expected:

- `modules.jaimini.darakaraka.dk_planet == Sun`
- `modules.jaimini.darakaraka.d9_sign == Gemini`
- `modules.jaimini.darakaraka.d9_dignity == ENEMY`

Before fix:

- dignity incorrectly surfaced as `FRIEND`

### 3. Vimsopaka Navamsa dignity uses D9 context

Same `1992-08-25 23:10` case:

Expected:

- `modules.vimsopaka.Sun.varga_scores.Navamsa.dignity == Enemy`

Before fix:

- dignity incorrectly surfaced as `Friend`

## Tests Added / Updated

- `/Users/wuyongnaren/Documents/印度占星/tests/test_dasha.py`
  - helper-level context-sensitive dignity regression tests
- `/Users/wuyongnaren/Documents/印度占星/tests/test_cli_smoke.py`
  - D9 expanded dignity regression
  - Darakaraka D9 dignity regression
  - Vimsopaka Navamsa dignity regression
  - updated D1 smoke expectation for richer `Great Enemy` output

## Verification

Ran:

```bash
python3 -m pytest tests/test_dasha.py tests/test_cli_smoke.py tests/test_mcp_strict_workflow_relationship.py tests/test_mcp_strict_workflow_finance.py -q
```

Result:

- `75 passed`

## Boundary Notes

This pass **does fix**:

- divisional dignity borrowing `D1` context
- D9 exposed dignity fields in `full-reading`
- Navamsa dignity inside Vimsopaka when the dignity category already maps cleanly to the current `DignityLevel` enum

This pass **does not fix**:

- full semantic mapping of `NEECHA_BHANGA`, `GREAT_FRIEND`, `GREAT_ENEMY` into Vimsopaka virupa policy
- broader D10/D12/D60 dignity benchmark closure
- any adjudicator logic that consumes divisional dignity later
- historical P0/P1 items unrelated to this context bug

## Fragment Reuse / Traceability

This repair closes one concrete slice of the earlier audit trail in:

- `/Users/wuyongnaren/Documents/印度占星/references/audit-deep-data-audit-2026-05-04.md`

where Vimsopaka and divisional dignity context leakage had already been identified as a high-severity trust issue.
