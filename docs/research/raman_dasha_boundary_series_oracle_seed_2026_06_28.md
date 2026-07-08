# Raman Dasha Boundary Series Oracle Seed - 2026-06-28

## Scope

This pass converts the untracked `test_dasha_raman_truth.py` placeholder idea into a formal external-oracle seed.

## Source Value Recovered

The useful fragment was not the mocked `xfail` test. The valuable part was the B.V. Raman Vimshottari Mahadasha boundary series:

- Mars: `1912-08-08`
- Rahu: `1918-09-21`
- Jupiter: `1936-09-21`
- Saturn: `1952-09-21`
- Mercury: `1971-09-21`
- Ketu: `1988-09-21`

## Promoted Asset

Added a new template row:

- `template_bv_raman_vimshottari_boundary_series`
- file: `<repo>/references/oracle/dasha_shadbala_oracle_cases.json`

The oracle queue now recognizes:

- `target.vimshottari_mahadasa_boundaries`
- target module: `dasha`

## Boundary

- Status remains `template_only`.
- It is not production calibration evidence.
- It does not prove local Raman ayanamsa or Vimshottari year-length alignment.
- It must not replace an external source artifact or screenshot.

## Why Not Keep The Old Test

The untracked `tests/test_dasha_raman_truth.py` used mocked calculation and ended with `pytest.xfail`. Keeping that test would create a false sense of executable coverage. The oracle seed is more honest: it preserves the reference value while keeping calibration blocked until metadata and external capture are complete.

## Regression Coverage

- `<repo>/tests/test_oracle_collection_queue.py`
