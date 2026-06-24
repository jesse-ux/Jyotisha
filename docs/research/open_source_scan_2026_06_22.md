# Open Source Jyotish Scan — 2026-06-22

Purpose: keep the product audit grounded in current open-source projects instead of relying only on older comparison notes.

## Live GitHub Checks

The live GitHub API scan on 2026-06-22 confirmed these current reference points:

| Project | Current signal | License signal | Reuse posture | Product lesson |
|---|---:|---|---|---|
| VedAstro/VedAstro | ~568 stars, active full-stack C#/web/API project | MIT | Direct for API/product ideas; C# code not copied into Python path | Product completeness: website, API, OpenAPI-style surface, AI/chat experience |
| CNWU16/vedic-astro-skills | ~338 stars, fast-growing skill toolkit | MIT | Direct for skill/report workflow ideas already mirrored under `references/open_source_sources/vedic-astro-skills` | Methodology depth: report rules, house framework, P1-P12 audit, reader/rectifier flows |
| naturalstupid/PyJHora | ~190 stars, AGPL | Caution: benchmark and behavioral reference, not copy-paste into permissive code | Breadth benchmark: JHora-style dasha, varga, yoga, AV, Tajika, GUI/test corpus |
| adarshj322/dashaflow | Low-star but focused Python package; query matched Shadbala/Ashtakavarga/Muhurta | MIT | Direct; local mirrored code exists under `references/open_source_sources/dashaflow` | Practical reusable kernels for Muhurta, AV, Shadbala, Jaimini, matching, career |
| northtara/jyotishganit | Local mirror available | MIT | Direct for modern Python data-layer comparisons | Deterministic component separation: varga, panchanga, strengths, AV, JSON-LD |
| diliprk/VedicAstro | Local mirror available | MIT/research noted | Direct for adapted KP sublord logic | KP-specific RL/NL/SL/SSL and horary workflow |
| RoxyAPI/jyotish-vedic-astrology-app | 2026 Next.js template with Kundli, Panchang, Ashtakoot Gun Milan, Vimshottari Dasha, dosha analysis | MIT | Product benchmark; depends on external RoxyAPI rather than local copy | Treat matching as a guided first-class workflow |
| RoxyAPI/vedic-astrology-starter-app | 2026 React Native/Expo starter with Gun Milan, Manglik, Navamsa, Panchang, Sade Sati | MIT | Mobile/product benchmark | Saved profiles and mobile matching flow matter |
| emmetCode/nakshatra | 2026 JS Ashtakoot/Nadi-focused project | No license detected | Benchmark only | Kuta/Nadi factors need explanatory UI, not just a score |
| Akshay-S-PY/RashAi | Vite/vanilla JS Vedic app with kundali, matching, panchang, muhurta, AI insights | No license detected | Product benchmark | Lightweight apps still surface matching as a primary module |
| VedAstro/Vedic-Astrology-AI-MCP-Server | MCP/AI wrapper with compatibility matching topic | No license detected in search result | API/agent benchmark | Compatibility should be callable from agent/API surfaces |

## Local Mirror Status

`scripts/audit_fragments.py` currently detects seven local source mirrors:

- `references/open_source_sources/VedicAstro`
- `references/open_source_sources/dashaflow`
- `references/open_source_sources/jaimini-tropical`
- `references/open_source_sources/jyotishganit`
- `references/open_source_sources/panchanga_api`
- `references/open_source_sources/rishi-ai-mcp`
- `references/open_source_sources/vedic-astro-skills`

## Immediate Product Rules

1. Prefer MIT/Apache local source mirrors for direct code reuse.
2. Treat AGPL/GPL projects such as PyJHora as behavioral benchmarks unless the whole downstream license posture is explicitly accepted.
3. Any registry technique marked `covered` or `complete` must have at least one real CLI/API/script surface and at least one real output path.
4. UI productization is not just a tab: it must expose readable conclusions, evidence, next action, mobile-safe layout, and hidden raw JSON for audit.
5. Matching/synastry productization is not just Moon-degree input: it must support saved partner selection, full birth-data calculation, explanatory Kuta/Nadi factors, D9/Kuja/Dasha context, and exportable pair records.

## New Guardrail

`python3 scripts/audit_fragments.py --strict` now cross-checks:

- `references/technique_registry.json`
- `scripts/jyotish_engine.py` CLI commands
- `scripts/jyotish_api_server.py` API routes
- `jyotish-app/` frontend API markers
- `tests/` references
- local open-source mirrors
- untracked workspace residue and `.git/lost-found` fragments

This is the repeatable check for the “different windows left scattered fragments” concern.
