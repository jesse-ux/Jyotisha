# PyJHora Same-Chart Parity: Public Smoke Batch

Date: 2026-07-12

## Scope

Ten public/synthetic smoke birth records were replayed through the local
canonical baseline and an isolated PyJHora comparison runner. Both sides used
Lahiri ayanamsa and Mean Node mode. No user birth record or private event data
was used.

## Result

| Field status | Count |
|---|---:|
| `match` | 836 |
| `boundary_sensitive` | 4 |
| `mismatch` | 0 |
| Total compared | 840 |

The four boundary-sensitive rows are D10 values at divisional boundaries. They
are retained as downgraded evidence, not silently counted as exact matches.

Covered outputs:

- D1: ascendant and nine planetary rows
- D9
- D10
- current Vimshottari boundaries

Not yet compared:

- D2 / D4
- Shadbala
- Ashtakavarga
- VedAstro official raw snapshot
- JHora desktop export
- jyotishganit outside its Panchanga-oriented raw coverage

## Reproduction

Use `benchmarks/jyotish/scripts/run_pyjhora_compare.py` with explicit
`--build-local --node-mode mean`. Use `--output-prefix` for resumable batches.
Summarize each matrix through `scripts/pyjhora_parity_summary.py`.

## Boundary

This is partial external verification for the listed outputs only. It does not
establish full three-engine parity, global algorithmic accuracy, or event
prediction accuracy. VedAstro remains `official_blocked` until an official raw
response is captured and normalized.
