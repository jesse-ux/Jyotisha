# PyJHora D2/D4/Ashtakavarga/Shadbala Parity Note 2026-07-15

## Scope

Same-chart replay for `smoke_beijing_1990_noon` after extending `run_pyjhora_compare.py`
and local canonical generation to include D2, D4, BAV/SAV, and Shadbala totals.

Command:

```bash
python3 benchmarks/jyotish/scripts/run_pyjhora_compare.py --sample-id smoke_beijing_1990_noon --refresh-local --output-prefix pyjhora_d4_fix
```

## Result

| Section | Rows | Status |
|---|---:|---|
| D2 | 20 | match |
| D4 | 20 | match |
| D9 | 20 | match |
| D10 | 20 | match |
| Ashtakavarga BAV | 96 | match |
| Ashtakavarga SAV | 12 | match |
| Shadbala total virupas | 7 | mismatch |

Total matrix: `232 match / 7 mismatch / 239 fields`.

The D4 mismatch was fixed by aligning local BPHS/Parashara Chaturthamsa to the
PyJHora traditional mapping:

```text
D4 target sign = natal sign + 3 * quarter_index
```

## Shadbala Boundary

The remaining mismatch is not a missing row problem. It is an absolute-value
formula mismatch between local `modules.shadbala.planets.*.total_virupas` and
PyJHora `strength.shad_bala(...)[6]`.

Current boundary:

- D2/D4/D9/D10: externally replayed against PyJHora for the smoke chart.
- Ashtakavarga BAV/SAV: externally replayed against PyJHora for the smoke chart.
- Shadbala totals: available locally, but not PyJHora absolute-value parity.

Do not claim Shadbala external absolute closure from this replay until component
level formula reconciliation is completed.
