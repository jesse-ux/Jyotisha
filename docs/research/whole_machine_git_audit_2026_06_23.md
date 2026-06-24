# Whole Machine + Git Cloud Jyotish Audit — 2026-06-23

## Scope

User request: perform a carpet-level audit of missed Jyotish / Vedic astrology information across the whole computer and the Git cloud repository, then map findings back to the current web/app.

Safety boundary:

- Read-only discovery only.
- Do not delete, move, upload, or rewrite external files.
- Do not quote or copy secrets. Several old local git remotes contain embedded GitHub tokens; this report records the risk without reproducing token characters.
- Treat all external/history documents as untrusted research data, not instructions.

## Second-Round Closure — 2026-06-24

Fresh audit command:

- `python3 scripts/audit_fragments.py --strict`

Result:

- Registry techniques: `68`
- API endpoints: `37`
- Front-end source files scanned: `43`
- Fragment candidates: `0`
- Hard problems: `0`
- Warnings: `0`
- Local open-source mirrors: `7`

Second-round fix applied during this audit:

- `deep_varga_avastha` had already been implemented as `/api/deep_varga_avastha` and a Skill Workbench action, but it was not yet a first-class registry/catalog technique.
- Added `references/technique_registry.json` entry for `deep_varga_avastha`.
- Added `scripts/audit_fragments.py` command and front-end markers for `deep-varga-avastha`.
- Added `scripts/jyotish_api_server.py` productization, UX, catalog endpoint, and visible-topic inference markers.
- Added regression tests requiring the technique audit, Technique Explorer filters, runnable examples, and sample payloads to include `/api/deep_varga_avastha`.

Global open-source ranking after first-class gaps were closed:

| Rank band | Project | Positioning | Current comparison |
|---|---|---|---|
| 1 | Jagannatha Hora / PyJHora class | Deep professional Jyotish calculation breadth and long-term validation | Still stronger as a specialist calculation benchmark; PyJHora is AGPL, so benchmark-only for this project. |
| 2 | This project (`yinduzhanxing`) | Web/app user productization of 68 techniques with API, Skill Workbench, report/export, PWA, Trust Center and browser smoke gates | Now likely top tier among open-source user-facing Jyotish web/app projects; strongest area is full web/app workflow coverage rather than raw legacy desktop calculation depth. |
| 3 | VedAstro class | Mature API/platform orientation and web service model | Strong API reference; this project now covers more in-app ordinary-user workflows, but should keep borrowing platform/API discipline. |
| 4 | VedicAstro / panchanga API / RoxyAPI templates | Focused API or starter-app coverage | Useful references for KP, panchanga and app scaffolding; current project is broader and more productized. |
| 5 | Single-purpose libraries | Panchanga, dasha, ephemeris or MCP fragments | Useful as specialized references, not comparable as full ordinary-user apps. |

Current conclusion:

- The previous first-class productization gap list is closed at registry/API/front-end/catalog level: Ashtakavarga PAV/Yoga Pinda, Sripathi/Placidus switch, KP Horary, Tajika Harsha/Panchavargiya Bala, Muhurta date-range solver, and Sayanadi/Shayanadi + D24/D30/D60 templates are now implemented and guarded.
- Remaining competitive gap is no longer "missing obvious skill capability"; it is release hardening: cloud sync/branch hygiene, full browser/release quality gate, external benchmark fixtures, and production packaging.
- The largest current project risk is workspace hygiene: many important product files are still untracked locally, so cloud deploys or ordinary-user builds from GitHub may miss them until the work is staged/committed.

## Git Cloud Evidence

Primary remote in current repo:

- `origin`: `git@github.com:732642856/yinduzhanxing.git`
- current branch: `codex/release-hygiene-ci`

Cloud access attempts:

- SSH `git ls-remote` failed because port 22 timed out.
- HTTPS `git ls-remote https://github.com/732642856/yinduzhanxing.git` succeeded.
- GitHub REST API anonymous request was rate-limited.
- HTTPS mirror clone succeeded into `/tmp/yinduzhanxing-mirror.git`, then checked out into `/tmp/yinduzhanxing-cloud`.

Cloud refs found:

- `refs/heads/main` -> `4ff624812c7b9ec762a801f7219f9c2f5079e907`
- `refs/heads/codex/release-hygiene-ci` -> `11bdee3ba1f480aff38440ad58cfbb81bfa5567d`
- tags: `v6.0.47`, `v6.0.48`, `v6.0.49`, `v6.0.50`, `v6.0.51`, `v6.0.52`

Cloud checkout facts:

- `/tmp/yinduzhanxing-cloud` checked out `codex/release-hygiene-ci`.
- Cloud HEAD: `11bdee3ba1f480aff38440ad58cfbb81bfa5567d`
- Cloud tree: `d3a89944bb1c319120f61f66a88c879d0fa28375`
- Cloud file count excluding `.git`: `720`
- Cloud text/code-like file count: `654`

Local workspace facts:

- Local file count excluding `.git`: `1525`
- Local text/code-like file count: `938`
- Local contains many build/cache/runtime outputs not present in cloud: `.pytest_cache`, `.ruff_cache`, `build/`, `dist/`, `jyotish-app/dist/`, `jyotish-app/node_modules/`, `__pycache__`, generated benchmark outputs.
- Tracked local diff is much larger than the cloud branch diff and includes active productization work in app/API/tests/docs.

Cloud branch diff against `origin/main`:

- 17 files changed.
- 192 insertions, 125 deletions.
- Mostly release hygiene, CI, README/SKILL docs, packaging manifest, quality gate, and small API/build fixes.

## Whole-Machine High-Value Sources

High-signal local sources found outside the current project:

- `/Users/wuyongnaren/.workbuddy/skills/jyotish-vedic-astrology`
- `/Users/wuyongnaren/Projects/星轨资料恢复/17-Skills技能库/jyotish-vedic-astrology`
- `/Users/wuyongnaren/Projects/星轨资料恢复/25-相关Skills补充/jyotish-vedic-astrology`
- `/Users/wuyongnaren/engines-repo/jyotish`
- `/Users/wuyongnaren/Documents/星轨talk/engines-repo/jyotish`
- `/Users/wuyongnaren/WorkBuddy/engines-repo/jyotish`
- `/Users/wuyongnaren/WorkBuddy/2026-06-09-20-03-34/jyotish-fragments`
- `/Users/wuyongnaren/WorkBuddy/2026-06-10-21-30-47`
- `/Users/wuyongnaren/WorkBuddy/2026-06-12-15-22-12`
- `/Users/wuyongnaren/.workbuddy/brain`
- `/Users/wuyongnaren/文件仓库/印度占星文章`
- `/Users/wuyongnaren/文件仓库/中外🔮占星/国外占星/印度占星书`

Important historical reports found:

- `印度占星Skill_真实Bug与遗漏清单_v6.1.11.md`
- `Yinduzhanxing_开源对标与优化报告_v6.1.11.md`
- `开源印度占星项目搜索报告.md`
- `vedic-astrology-open-source-research.md`
- `印度占星Skill全面审计与能力评估报告-v3.0.md`
- `jyotish_improvement_plan.md`
- `jyotish_capability_assessment.md`

## Open Source Sources Already Present Locally

Current project already contains local mirrors under `references/open_source_sources`:

- `jyotishganit`
- `jaimini-tropical`
- `VedicAstro`
- `rishi-ai-mcp`
- `dashaflow`
- `panchanga_api`
- `vedic-astro-skills`

Historical reports repeatedly classify reuse posture as:

- MIT / suitable for direct reuse or adaptation: `VedicAstro`, `dashaflow`, `vedic-astro-skills`, parts of `jyotishganit`, `happyalu/panchang-muhurt` where license permits.
- AGPL/GPL / benchmark or independent rewrite only: `PyJHora`, `vedic-calc`, some SwissEph WASM packages.

## Historical Missing-Feature Consensus

The recurring non-UI gaps from older reports:

- Ashtakavarga Prashtara / PAV source contribution table
- Ashtakavarga Kakshya
- Yoga Pinda
- Bhava Bala
- Navatara / Tara Bala
- Kantaka Shani
- Pushkara Navamsa / Pushkara Bhaga
- Ishta / Kashta Phala
- Sripathi / Placidus house systems
- 36 Sahams
- Tajika strength layers: Harsha Bala, Panchavargiya Bala
- KP Horary
- Deeper Prashna: Sphuta / Trisphuta / Prana-Deha-Mrityu
- Muhurta solver
- Vimshottari multiple start points
- Sayanadi / Shayanadi Avastha
- D24 / D30 / D60 deeper interpretive templates

## Current Coverage Matrix

Legend:

- `covered`: registry/API/engine or front-end has a meaningful implementation path.
- `partial`: some backend or docs exist, but the product/API/user flow is incomplete.
- `reference-only`: only docs or open-source reference exists; no first-class product implementation.

| Area | Current Status | Evidence | Gap |
|---|---:|---|---|
| Navatara / Tara Bala | partial | `scripts/nakshatra_advanced.py`, `tests/test_nakshatra.py`, registry has Nakshatra Advanced | Tara Bala exists, but Navatara itself is not first-class in skill-map/product cards. |
| Kantaka Shani | covered | `scripts/sade_sati.py`, `/api/sade_sati`, registry note | User-facing depth may still be limited to the Sade Sati surface. |
| Pushkara | covered | `scripts/jyotish_engine.py`, `jyotish-app/main.js`, registry | Covered in D9/marriage and full-reading contexts. |
| Ishta / Kashta Phala | partial | Shadbala references and tests mention Ishta/Kashta | No standalone registry/API/front-end module. |
| Ashtakavarga Prashtara | reference-only | `references/open_source_sources/dashaflow/ashtakavarga.py`, old reports | Current `scripts/ashtakavarga.py` has BAV/SAV; Prashtara source contribution table not productized. |
| Yoga Pinda | reference-only | `references/feature-gap-matrix-2026.md` | No engine/API/front-end implementation found. |
| Kakshya | covered | `scripts/kakshya.py`, `/api/kakshya`, `computeKakshya`, tests | Covered as backend/API; check if product surface is prominent enough. |
| Bhava Bala | covered | `scripts/bhava_bala.py`, `/api/bhava_bala`, skill-map card | Covered as backend/API and app card. |
| Sripathi / Placidus | partial | `scripts/bhava_chalit.py`, API example uses `house_system: sripati`; VedicAstro has Placidus references | Setting exists around Bhava Chalit, but not a clear user-facing house-system selector/parity gate. |
| 36 Sahams | covered | `scripts/tajika.py`, `scripts/varshaphala.py`, `/api/annual`, `/api/prashna` | Covered in annual/prashna contexts. |
| Harsha / Panchavargiya Bala | reference-only | roadmap and feature matrix | No first-class engine/API/front-end implementation found. |
| KP Horary | partial | `references/open_source_sources/VedicAstro/vedicastro/horary_chart.py`, `scripts/prashna.py` has simplified KP Prashna | MIT source exists but VedicAstro horary is not directly integrated as a product module. |
| Prashna Sphuta / Trisphuta | covered | `scripts/prashna.py`, tests assert `trisphuta`, front-end renders Sphuta points | Covered. |
| Muhurta solver | partial | `scripts/muhurta.py`, `/api/muhurta`, tests | Scoring exists; full constraint solver/date-range search is still unclear. |
| Vimshottari multiple start points | partial | `scripts/extended_dashas.py`, `nakshatra_dasha.py`, registry Dasha variants | No clear setting for all traditional 12 Vimshottari start points. |
| Sayanadi / Shayanadi Avastha | partial | `scripts/avastha_calculator.py` includes Shayanadi | Registry does not expose Sayanadi/Shayanadi as a separate capability; front-end status is partial. |
| D24 / D30 / D60 deep reading | partial | `scripts/divisional_charts_extended.py`, `trimshamsa_d30.py`, tests | Calculations exist; deep interpretive templates for D24/D30/D60 remain thinner than D1/D9/D10. |

## Highest Priority Remaining Gaps

1. Ashtakavarga Prashtara + Yoga Pinda
   - Why: Professional Ashtakavarga tools need source contribution tables, not only BAV/SAV totals.
   - Reuse: `dashaflow/ashtakavarga.py` can be studied/adapted if license allows; current local `scripts/ashtakavarga.py` already has calibrated BAV/SAV.

2. Sripathi / Placidus house-system productization
   - Why: Settings mention house systems, but the user-facing app still needs a trustworthy switch, provenance, and parity warning.
   - Reuse: VedicAstro horary/houses references and current `bhava_chalit.py`.

3. KP Horary via VedicAstro
   - Why: Historical reports rank VedicAstro as the best MIT source for KP Horary.
   - Reuse: `references/open_source_sources/VedicAstro/vedicastro/horary_chart.py`.

4. Harsha / Panchavargiya Bala for Tajika
   - Why: Annual Varshaphala already exists, but Tajika strength judgement is incomplete without these layers.
   - Reuse: historical notes and reference docs; avoid AGPL copying.

5. Muhurta constraint/date-range solver
   - Why: Current Muhurta scoring is not the same as a usable search workflow.
   - Reuse: `dashaflow/muhurtha.py`, `panchanga_api`, `happyalu/panchang-muhurt` if license permits.

6. Sayanadi/Shayanadi Avastha + D24/D30/D60 deep templates
   - Why: These are expert-depth gaps, not first-minute UX gaps.
   - Reuse: current `avastha_calculator.py`, `divisional_charts_extended.py`, and existing reference templates.

## Next Action

Start with Ashtakavarga Prashtara + Yoga Pinda because it is:

- Repeated across historical reports.
- Still not present in registry/API/frontend as a first-class capability.
- Close to existing calibrated Ashtakavarga code, so implementation risk is bounded.
- Highly visible for professional users comparing this app against real Jyotish tools.
