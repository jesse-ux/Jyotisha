# Local Reuse Candidate Index Round 28 (2026-06-26)

## Purpose

Before adding or rewriting Jyotish features, Codex must first check whether the capability already exists in:

- the current repo,
- the older WorkBuddy skill copy,
- historical benchmark scripts,
- local open-source mirrors,
- Antigravity research reports.

This file turns that requirement into a concrete reuse index.

## Hard Rule

For every future core Jyotish feature, use this order:

1. Current repo implementation.
2. Current repo benchmark / oracle / test asset.
3. Older WorkBuddy skill copy.
4. Local open-source mirror with clear MIT / Apache / BSD / ISC / CC0 license.
5. External open-source project after fresh license check.
6. GPL / AGPL / closed software only as black-box benchmark or manual oracle.
7. New implementation only after the above are checked.

## Direct Current Repo Reuse

| Area | Existing files | Reuse action |
|---|---|---|
| Shadbala | `scripts/shadbala.py`, `scripts/shadbala_advanced.py`, `tests/test_shadbala_complete.py`, `tests/test_shadbala_jhora_benchmark.py` | Reuse engine and tests; continue external oracle validation instead of rewriting. |
| Ashtakoot | `scripts/ashtakoot.py`, `tests/test_ashtakoot.py`, `references/oracle/ashtakoot_oracle_cases.json` | Reuse current 36-point engine; add external oracle and MIT matrix comparison. |
| Panchanga / Muhurta | `scripts/muhurta.py`, `scripts/cmd_muhurta.py`, API tests and README entries | Reuse existing range solver; productize UI and external benchmark. |
| Tajika / Varshaphala | `scripts/tajika.py`, `jyotish-app/tajika.js`, `tests/test_tajika.py` | Reuse calculation layer; expose missing API/UI paths if blackbox confirms gap. |
| Jaimini / Chara Dasha | `scripts/jaimini.py`, `benchmarks/jyotish/scripts/run_chara_dasha_knrao.py`, `tests/test_jaimini.py` | Reuse engine and KN Rao benchmark assets; improve frontend visibility. |
| KP / Prashna | `scripts/kp_system.py`, `scripts/prashna.py`, `tests/test_kp_system.py` | Reuse current KP/Prashna code; audit 249 sublord completeness before extending. |
| Deep Varga / Avastha | `scripts/deep_varga_avastha.py`, `scripts/avastha_calculator.py`, `tests/test_deep_varga_avastha.py` | Reuse backend aggregation; add user-facing controls/export surface. |
| Accuracy gates | `scripts/local_accuracy_report.py`, `scripts/run_quality_gate.py`, `references/validation_logic_report.json` | Reuse for every accuracy claim; do not replace with ad hoc metrics. |

## Older WorkBuddy Skill Reuse

The older copy at `/Users/wuyongnaren/.workbuddy/skills/jyotish-vedic-astrology` is a high-value source, but it must not blindly overwrite current files.

| Area | Useful files | Reuse action |
|---|---|---|
| Technique docs | `references/*complete*.md`, `references/strict-workflow-router.md`, `references/technique_registry.json` | Compare against current repo docs and import missing route/rubric content. |
| Benchmarks | `benchmarks/jyotish/scripts/*`, `benchmarks/jyotish/reports/*` | Reuse as benchmark assets or parity scripts after path cleanup. |
| Tests | `tests/test_shadbala_jhora_benchmark.py`, `tests/test_chara_dasha_precision_v6910.py`, `tests/test_kp_system.py` | Port tests first, then code only if needed. |
| Frontend fragments | `jyotish-app/tajika.js` | Compare with current `jyotish-app/tajika.js`; reuse only missing UI behavior. |

## Local Open-Source Mirrors

These are local mirrors under `references/open_source_sources/` or the WorkBuddy copy. License must be checked at exact file/project level before reuse.

| Candidate | Local path | License status from existing notes | Reuse category |
|---|---|---|---|
| `dashaflow` | `references/open_source_sources/dashaflow/` | Existing notes say MIT | `copy_allowed_after_exact_license_check` |
| `vedic-astro-skills` | `references/open_source_sources/vedic-astro-skills/` | Existing notes say MIT | `copy_allowed_after_exact_license_check` |
| `rishi-ai-mcp` | `references/open_source_sources/rishi-ai-mcp/` | MIT license file present | `copy_allowed_after_exact_license_check` |
| `panchanga_api` | `references/open_source_sources/panchanga_api/` | Existing notes say MIT / MIT-0, needs exact source check | `quarantine_until_exact_license_verified` |
| `jaimini-tropical` | `references/open_source_sources/jaimini-tropical/` | Existing notes say MIT | `copy_allowed_after_exact_license_check` |

## Benchmark-Only Sources

These must not be copied into this repo:

| Source | Reason | Allowed use |
|---|---|---|
| PyJHora | AGPL-3.0 in existing research notes | Black-box output, screenshots, manual oracle only. |
| kunjara/jyotish | GPL-2.0+ in existing research notes | Behavioral comparison only. |
| JHora desktop | Closed/proprietary | Manual screenshot oracle only. |
| AstroSage / Drik Panchang / Prokerala | Closed web calculators | Manual screenshot/API output as external oracle only. |

## Immediate Reuse Priorities

1. Kuja / Manglik enum: inspect `scripts/ashtakoot.py`, `tests/test_ashtakoot.py`, and MIT `dashaflow/matchmaking.py` before implementing.
2. Panchanga commercial UI: reuse current `/api/panchanga_range`, `scripts/muhurta.py`, `cmd_muhurta.py`; only borrow UI ideas from MIT/RoxyAPI after license check.
3. Tajika endpoint: reuse `scripts/tajika.py` and `tests/test_tajika.py`; do not write a new Tajika engine.
4. Chara Dasha frontend: reuse `scripts/jaimini.py` and KN Rao benchmark outputs.
5. Prompt Pack safety: reuse current `ai_prompt_pack` evidence snapshot and WorkBuddy `prediction-boundary-protocol.md` / `prediction-output-protocol.md`.

## Verification Note

This index was generated after scanning:

- `/Users/wuyongnaren/Documents/印度占星`
- `/Users/wuyongnaren/.workbuddy/skills/jyotish-vedic-astrology`
- `/Users/wuyongnaren/Documents/星轨talk/engines-repo/jyotish`
- `/Users/wuyongnaren/Documents/Codex/2026-06-20`

The scan confirms the main issue is not absence of techniques. The issue is fragmented reuse, incomplete product exposure, incomplete external oracle calibration, and uneven frontend/API integration.
