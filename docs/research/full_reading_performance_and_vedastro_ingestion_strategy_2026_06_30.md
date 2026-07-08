# Full Reading Performance And VedAstro Ingestion Strategy (2026-06-30)

## Scope

This note records one strict round of:

1. whole-repo workflow review,
2. external-source grounding,
3. real `full-reading` stage timing collection,
4. API strategy changes based on measured bottlenecks.

It is intended to prevent future work from drifting back into intuition-only performance decisions.

## High-Level Conclusion

The current project is **not bottlenecked by local Jyotish computation**.

The dominant runtime cost for real user-facing `full-reading` is:

1. `vedastro_official_snapshot`
2. `vedastro_main_entry_overview`

Therefore, the highest-value optimization order is:

1. preserve the existing local-native calculation path,
2. reuse existing `vedastro_service_adapter` request caching,
3. add **API-level final chart response caching** for the normal `/api/chart` path,
4. keep `high_rigor_workflow` explicitly marked as the lane that should move toward queue/async execution,
5. do **not** spend engineering cycles micro-optimizing local Dasha/Varga/Yoga layers before fixing official-evidence ingestion cost.

## Repo Facts Confirmed

### Active closure lanes

`docs/research/ACTIVE_FRONTS.md` keeps work constrained to four fronts:

1. Relationship adjudicator closure
2. Vimsopaka + functional-role closure
3. Oracle closure batch
4. VedAstro strict ingestion

This means performance/productization work should be treated as support for the fourth lane, not as an unrelated new product surface.

### Existing reusable building blocks

The repo already contains the main pieces required for an official-first architecture:

- `scripts/vedastro_service_adapter.py`
- `scripts/vedastro_evidence_orchestrator.py`
- `scripts/vedastro_priority.py`
- `scripts/jyotish_engine.py`
- `scripts/jyotish_api_server.py`
- `mcp_server.py`

The correct strategy is to **reuse and tighten** these boundaries, not to create a second orchestration stack.

## External-Source Grounding

### Python performance measurement

The Python standard library documents `time.perf_counter()` as the high-resolution timer appropriate for measuring short durations and performance intervals.  
Source: [Python `time` documentation](https://docs.python.org/3/library/time.html)

The Python profiling documentation distinguishes deterministic profiling (`cProfile` / `profile`) from ad hoc guessing and supports evidence-first investigation of runtime cost.  
Source: [Python profiling documentation](https://docs.python.org/3/library/profile.html)

### Task-queue direction

FastAPI documents `BackgroundTasks` for simple post-response work, but this pattern is not a substitute for durable heavy workflow execution when requests are long-running.  
Source: [FastAPI BackgroundTasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)

RQ documents a Redis-backed background job queue suitable for Python jobs that should leave the request path.  
Source: [RQ documentation](https://python-rq.org/docs/)

### Interpretation for this project

These sources support a two-layer discipline:

1. first instrument real runtime stages with in-code timers,
2. then move only the truly expensive request-path layers to cache or queue.

For this repository, that means:

- measure `full-reading` stages before architectural change,
- keep local chart math synchronous,
- protect heavy VedAstro official ingestion behind cache and later queue/async boundaries.

## Real Timing Evidence

### Sample used

Real sample run:

- birth: `private birth datetime`
- location: `36.4467, 114.2`
- tz: `UTC+8`
- reference date: `2026-06-30`

Command:

```bash
python3 scripts/jyotish_engine.py full-reading \
  --year REDACTED_YEAR --month 4 --day 17 \
  --hour 14 --minute 49 \
  --lat 36.4467 --lon 114.2 --tz 8 \
  --today 2026-06-30 \
  --transit-date 2026-06-30 \
  --profile-stages
```

### First measured run

Observed summary:

- total elapsed: `181.0154s`
- modules: `57`
- errors: `0`

Stage timings:

- `core_chart_and_setup`: `0.0036s`
- `dasha_and_core_varga_stack`: `0.8380s`
- `advanced_interpretation_and_timing_layers`: `0.4753s`
- `dynamic_hooks`: `0.0001s`
- `vedastro_official_snapshot`: `133.7938s`
- `strict_contracts`: `3.5107s`
- `vedastro_main_entry_overview`: `41.5806s`
- `guided_topics`: `0.0003s`
- `ai_prompt_pack`: `0.8122s`

### Second measured run with existing caches warmed

Same command, same birth payload, same reference date.

Observed stage timings:

- `core_chart_and_setup`: `0.0029s`
- `dasha_and_core_varga_stack`: `0.9145s`
- `advanced_interpretation_and_timing_layers`: `0.5279s`
- `vedastro_official_snapshot`: `112.0435s`
- `strict_contracts`: `2.9865s`
- `vedastro_main_entry_overview`: `0.0735s`
- `guided_topics`: `0.0003s`
- `ai_prompt_pack`: `0.6211s`

### What the second run proves

The second run proves two different things:

1. `vedastro_main_entry_overview` is already benefiting from existing lower-level caching.
2. `vedastro_official_snapshot` remains overwhelmingly expensive even after a warm rerun.

So the adapter cache is **useful but insufficient** at the user-visible workflow level.

## Root-Cause Interpretation

### What is not the bottleneck

The following are not the dominant latency problem:

- local Dasha
- local Varga
- Yoga / Ashtakavarga / Shadbala orchestration
- strict workflow contract assembly
- prompt pack generation

All of these are materially small relative to official evidence ingestion.

### What is the bottleneck

The dominant cost is the official evidence layer itself, especially:

- `run_official_full_snapshot_for_case(...)`
- official full-snapshot section fanout and retry path

The repo also shows a second pattern difference:

- CLI `full-reading` attaches overview by directly calling `run_range_scan_for_case(...)`
- API chart attaches overview through `orchestrate_vedastro_evidence(...)`, which already bundles official full snapshot and route-scoped scans

This means there are still opportunities to reduce duplication by reusing higher-level official results more aggressively.

## Strategy Decision

### Decision A: Normal chart path gets API-level final result caching

Why:

- `/api/chart` is the normal synchronous user path.
- It packages chart + official evidence + prompt pack together.
- The user cares about final response latency, not just adapter request latency.

Therefore a **final chart response cache** is justified at API level.

### Decision B: High-rigor workflow is the queue/async candidate lane

Why:

- `high_rigor_workflow` composes chart + rectification + historical backtest + thematic report.
- It is heavier than normal chart consumption by design.
- This lane is the correct place to expose queue/async execution strategy in future work.

### Decision C: Do not optimize local Jyotish math first

Why:

- measured evidence shows local-native layers are cheap relative to official ingestion.
- optimizing them first would spend effort where the user does not feel the delay.

## Implementation Landed In This Round

### `scripts/jyotish_engine.py`

Landed:

- stage timing instrumentation for `full-reading`
- `--profile-stages` CLI flag
- summary output containing:
  - `stage_timing_enabled`
  - `stage_timings`
  - `slowest_stages`

This is now the baseline tool for future performance decisions.

### `scripts/jyotish_api_server.py`

Landed:

- API chart final-response cache helpers:
  - `_build_api_chart_cache_payload`
  - `_api_chart_cache_key`
  - `_load_api_chart_response_cache`
  - `_store_api_chart_response_cache`
- runtime cache metadata attached to cached responses:
  - `scope`
  - `cache_hit`
  - `cache_key`
  - `cache_created_at`
  - `cache_expires_at`
  - `cache_ttl_seconds`
- `_compute_chart(...)` now checks API-level cache before recomputing
- `_high_rigor_workflow_plan_only(...)` now exposes execution strategy:
  - normal chart path uses sync chart response cache
  - high-rigor lane is the queue recommendation target

### Tests landed

Added/updated tests in `tests/test_api_server_security.py` to verify:

- API chart response cache contract exists and round-trips
- cache key changes with VedAstro runtime state
- high-rigor plan-only output explicitly surfaces chart-cache and queue strategy

## What Is Still Not Closed

1. The current official full snapshot still does not have an equivalent high-level final cache strong enough to collapse the `112s+` cost on rerun.
2. `high_rigor_workflow` exposes queue recommendation metadata, but no durable job runner or polling endpoint is landed yet.
3. CLI `full-reading` and API chart still do not fully unify around one deduplicated “official snapshot + overview reuse” path.

## Recommended Next Implementation Order

1. Add **official full snapshot result caching** at a higher semantic level than raw request caching.
2. Make API chart reuse that official full snapshot cache before rebuilding the same evidence package.
3. Introduce a minimal asynchronous lane for `high_rigor_workflow`:
   - enqueue request
   - return job id
   - poll result
   - keep synchronous mode for debug/local use
4. Only after those are landed, decide whether deeper profiler work is still needed.

## Honesty Boundary

This document does **not** claim:

- that the entire full-reading path is now fast,
- that all VedAstro-heavy routes are production-grade for synchronous use,
- that queue/async execution is already complete,
- that local and official evidence are fully deduplicated.

What it does claim is narrower and evidenced:

- stage timing is now real and reproducible,
- the main bottleneck has been identified with measured data,
- API-level final chart response caching is now partially landed,
- the repo now has a documented, evidence-backed strategy for the next optimization steps.
