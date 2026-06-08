# Jyotish Benchmark Suite

This directory contains the public benchmark material recovered and sanitized in v6.1.9.

## Scope

- Samples: 10 fictional/public smoke cases in `data/benchmark_samples.json`.
- Scripts: reproducible comparison scripts under `scripts/`.
- Reports: markdown summary reports under `reports/`.

Raw JSON/CSV outputs are intentionally not committed. Re-run the scripts locally to regenerate them under `benchmarks/jyotish/outputs/`.

## Privacy rule

All committed samples are marked `fictional_or_public_test`. Do not add real user birth data, private chart output, personal life events, PDF extraction text, or private full-reading JSON to this directory.

## Running

From the repository root:

```bash
python3 benchmarks/jyotish/scripts/run_skill_baseline.py
python3 benchmarks/jyotish/scripts/run_swiss_direct_compare.py
python3 benchmarks/jyotish/scripts/run_transit_true_compare.py
python3 benchmarks/jyotish/scripts/run_shadbala_invariants.py
```

Some scripts require optional local dependencies such as PyJHora or pyswisseph. If PyJHora is installed outside the default environment, set `PYJHORA_SITE` or `PYJHORA_PATH` as needed.

## Historical benchmark rounds

The recovered reports document the benchmark sequence used to harden the engine:

1. Local full-reading baseline
2. Swiss direct planetary comparison
3. Swiss extended comparison
4. PyJHora comparison
5. Mean/True node arbitration
6. Arudha/A10 comparison
7. Ashtakavarga comparison and book-example arbitration
8. Chara Dasha comparison
9. True transit comparison
10. Shadbala internal invariants
11. Explanation regression notes
