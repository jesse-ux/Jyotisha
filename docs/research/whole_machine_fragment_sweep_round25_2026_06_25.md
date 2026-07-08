# Whole-Machine Jyotish Fragment Sweep Round 25 (2026-06-25)

## Scope

This sweep is a pre-work guardrail for the Jyotish web/app project. It checks whether useful Jyotish material is split across local folders, older Codex windows, WorkBuddy skill copies, downloads, Obsidian notes, benchmark outputs, and Git remotes.

Commands used:

```bash
find . -maxdepth 2 \( -name 'task_plan.md' -o -name 'findings.md' -o -name 'progress.md' -o -path './.planning/*' \) -print | sort
git remote -v && git branch -a --verbose --no-abbrev
git ls-remote https://github.com/732642856/yinduzhanxing.git 'refs/heads/*' 'refs/tags/*' | sort
find <home>/Documents <home>/Projects <home>/WorkBuddy <home>/.workbuddy <home>/Downloads <home>/.codex/attachments -type d -name .git 2>/dev/null | sed 's#/.git$##' | rg -i '印度|jyotish|vedic|astro|talk|yinduzhanxing|星轨|codex|workbuddy' | sort
find <home>/Documents <home>/Downloads <home>/.codex/attachments -type f \( -iname '*印度*' -o -iname '*jyotish*' -o -iname '*jhora*' -o -iname '*vedic*' -o -iname '*ashtakoot*' -o -iname '*shadbala*' -o -iname '*antigravity*' \) 2>/dev/null
```

## Planning Files

Root planning files exist and must be read before major work:

- `task_plan.md`
- `findings.md`
- `progress.md`

Current plan still contains the explicit pre-work rule: scan local fragments, `references/open_source_sources/*`, existing tests, and product gap matrices before implementation.

## Git Remote State

Remote:

- `origin`: `git@github.com:732642856/yinduzhanxing.git`

HTTPS remote refs were reachable:

- `refs/heads/main`: `4ff624812c7b9ec762a801f7219f9c2f5079e907`
- `refs/heads/codex/release-hygiene-ci`: `6338cf510aa00305bb15b833071ae236ea5da7ff`
- tags `v6.0.47` through `v6.0.52`

SSH push/fetch over port 22 timed out during this sweep. Local branch was ahead after `bac3748 docs(research): archive antigravity round 23 and 24 audits`; treat remote synchronization as unconfirmed until an HTTPS/SSH-443 push or later fetch confirms it.

## High-Value Local Jyotish Sources

### Current Main Workspace

- `<repo>`
- Contains current web/app, API, tests, oracle queues, benchmarks, Antigravity reports, local accuracy report, and planning files.
- This is the only write target for implementation.

### Older Skill Copy

- `<home>/.workbuddy/skills/jyotish-vedic-astrology`
- Previously identified as an older skill/benchmark copy on `main@4ff6248`.
- Use as read-only historical comparison only. Do not overwrite current project from this copy.

### Talk Engine Copies

- `<home>/Documents/星轨talk/engines-repo/jyotish`
- `<home>/Documents/Codex/2026-06-20/732642856-talk-https-github-com-732642856/work/talk-active/engines-repo/jyotish`

Potentially useful files:

- `jyotish-adapter.js`
- `vedic-calc-runner.py`
- `jyotishganit-adapter.js`
- `jyotishganit-runner.py`
- `local-jyotish-reference-audit.js`
- `reports/local-jyotish-reference-audit.md`

Action: read before changing engine adapter or external-reference audit paths.

### Obsidian Notes

- `<home>/Documents/ObsidianVault/03_研究_术数占星/印度占星 Jyotish.md`
- `<home>/Documents/ObsidianVault/03_研究_术数占星/印度占星研究结论 v3.md`
- `<home>/Documents/ObsidianVault/03_研究_术数占星/PRIVATE_REDACTED_CASE · 印度占星完整解盘报告 v2.md`

Boundary: these may contain private or interpretive material. Use for gap discovery only; do not quote or commit private birth data.

### Downloads / Private Artifacts

- `<home>/Downloads/印度占星.pdf`
- `<home>/Downloads/private_chart_reference.pdf`
- `<home>/Downloads/Kimi_Agent_高维印度占星师.zip`
- `<home>/Downloads/jyotish_training.agent.final.docx`

Boundary: treat as private/user-provided. Do not commit full contents or derived private reports. Extract only high-level requirements when needed.

### Open-Source Reference Mirrors In Current Repo

- `references/open_source_sources/jyotishganit`
- `references/open_source_sources/VedicAstro`
- `references/open_source_sources/dashaflow`
- `references/open_source_sources/vedic-astro-skills`
- `references/open_source_sources/rishi-ai-mcp`

Use license rules:

- MIT/Apache/BSD/ISC/CC0: possible copy/adapt candidates after checking exact file license.
- GPL/AGPL/LGPL/closed: behavior/reference only.

### Benchmark Assets

- `benchmarks/jyotish/scripts/run_shadbala_invariants.py`
- `benchmarks/jyotish/scripts/run_pyjhora_compare.py`
- `benchmarks/jyotish/scripts/run_shadbala_compare.py`
- `benchmarks/jyotish/reports/jyotish_benchmark_round*.md`
- `benchmarks/jyotish/outputs/shadbala_invariants_matrix.csv`

Action: include benchmark reports before changing Shadbala, PyJHora comparison, or benchmark accuracy claims.

### Oracle / Accuracy Assets

- `references/oracle/dasha_shadbala_oracle_cases.json`
- `references/oracle/ashtakoot_oracle_cases.json`
- `references/oracle/evidence_packet_templates/jhora_steve_jobs_lahiri_first_packet.json`
- `docs/user_jhora_capture_guide.md`
- `tests/test_shadbala_jhora_benchmark.py`
- `tests/vedicka_verification_report.md`

Current blocker remains: external oracle readiness is 0/5 for Dasha/Shadbala and 0/5 for Ashtakoot.

## Antigravity Sidecar State

Round 25 work order exists:

- `docs/research/antigravity_sidecar_work_order_round25_2026_06_25.md`

During this sweep, sidecar had already started generating Round 25 reports, including:

- `antigravity_round25_ashtakoot_round24_claim_correction_2026_06_25.md`
- `antigravity_round25_vedastro_mit_reuse_scope_2026_06_25.md`
- `antigravity_round25_accuracy_profile_blackbox_2026_06_25.md`
- `antigravity_round25_accuracy_profile_ci_plan_2026_06_25.md`

Do not treat Round 25 as complete until all 18+ requested files exist and are independently checked.

## Current Implementation Implications

1. Before changing Ashtakoot, read `scripts/ashtakoot.py`, `tests/test_ashtakoot.py`, `references/oracle/ashtakoot_oracle_cases.json`, and Round 25 Ashtakoot correction report.
2. Before changing Shadbala, read `benchmarks/jyotish/reports`, `references/shadbala-complete-methodology.md`, `tests/test_shadbala_jhora_benchmark.py`, and oracle evidence validator tests.
3. Before claiming all skills are complete, compare registry, API handlers, CLI commands, front-end exposure, and external oracle readiness.
4. Before implementing from external code, check exact license and prefer current repo mirrors over live copying.
5. Private PDFs, Obsidian reports, and Downloads are discovery sources only, not commit sources.

## Next Required Pre-Work Routine

Run this compact pre-work check before substantial changes:

```bash
git status --short --branch
python3 scripts/local_accuracy_report.py --format json
python3 scripts/audit_capabilities.py --mode validate
find docs/research -maxdepth 1 -name 'antigravity_round25_*_2026_06_25.md' -print | sort | wc -l
rg -n "Ashtakoot|Shadbala|Dasha|Panchang|Muhurta|JHora|PyJHora|VedAstro|AstroSage" task_plan.md findings.md progress.md docs/research references tests scripts jyotish-app
```

This is not a substitute for full machine search, but it prevents most multi-window drift.
