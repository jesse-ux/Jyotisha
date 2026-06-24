# Jyotish Product Gap Matrix — 2026-06-22

Purpose: keep the web/app roadmap tied to same-category product expectations, live open-source scans, and local fragment audits. The registry audit can be 65/65 while product parity is still incomplete.

## Evidence Baseline

| Source | Signal | Product lesson | Reuse posture |
|---|---|---|---|
| `scripts/audit_fragments.py --strict` | 65 registry techniques, 37 CLI commands, 35 API endpoints, 42 frontend files, 0 hard gaps | Capability registry is covered; product gaps must be tracked separately | Local guardrail |
| `references/open_source_sources/vedic-astro-skills` | MIT skill/report/rectifier toolkit mirrored locally | Report workflow, P1-P12 audit, rectifier flow, validation rules | Direct for workflow and report packaging |
| `references/open_source_sources/dashaflow` | MIT Python kernels mirrored locally | Panchanga, Muhurta, Shadbala, Ashtakavarga, matching, career kernels | Direct where architecture fits |
| `references/open_source_sources/jyotishganit` | MIT Python component model mirrored locally | Separate deterministic components, JSON-LD style output, Panchanga objects | Direct for data-contract ideas |
| `references/open_source_sources/jaimini-tropical` | Local web app with Panchanga cards and export | Product UX pattern for Panchanga and plain-text export | Direct after license review |
| `VedAstro/VedAstro` GitHub scan | 568 stars, MIT, API/web/OpenAPI/chat/Panchanga topics | Full-stack product surface matters as much as calculation breadth | Direct for product/API ideas, not direct C# copy |
| `vedika-io/xalen-ephemeris` GitHub scan | 879 stars, Apache-2.0, Rust ephemeris, active in 2026 | Ephemeris abstraction and settings provenance should be a first-class long-term track | Candidate benchmark/integration spike |
| `naturalstupid/PyJHora` GitHub scan | Broad JHora-style feature reference, AGPL | Breadth benchmark and validation fixture source | Benchmark only unless license posture changes |
| `dineshpaudel/acharavidya` GitHub scan | MIT, Python/PyPI Panchanga calculations including Muhurta and Rahu Kala | Panchanga product parity includes inauspicious day parts, not just Tithi/Nakshatra | Candidate direct reference after source review |
| `jayeshmepani/panchang-core` GitHub scan | MIT, Panchang/Muhurta/raw JSON export product surface | Calendar APIs need exportable structured rows and event windows | Product/API benchmark; PHP code not copied |
| `RoxyAPI/jyotish-vedic-astrology-app` GitHub scan | MIT Next.js app with Panchang, Ashtakoot Gun Milan, Vimshottari Dasha, dosha analysis | Same-category apps expose Gun Milan as a guided product flow | Product/API benchmark; external API dependency not copied |
| `emmetCode/nakshatra` GitHub scan | JS Ashtakoot/Nadi-focused app, no license detected | Matching UX should explain Kuta/Nadi factors, not only return a total score | Benchmark only unless license becomes clear |
| `Akshay-S-PY/RashAi` GitHub scan | Vite/vanilla JS Vedic app with kundali, matching, panchang, muhurta, AI insights | Lightweight web apps still make matching a first-class module | Product benchmark |
| `VedAstro/Vedic-Astrology-AI-MCP-Server` GitHub scan | AI/MCP wrapper with compatibility matching topic | Agent/API surfaces should expose compatibility as callable workflow | Product/API benchmark |

## P0 Product Parity Gaps

| Gap | Current state | Same-category expectation | Next implementation task | Done when |
|---|---|---|---|---|
| Calculation settings and provenance center | 参数/日历面板 now shows engine, ayanamsa, ephemeris, house/node strategy, chart style, saved-chart status, and export provenance | User can inspect and later change calculation settings; exports preserve assumptions | Add setting selectors for ayanamsa/node/house/sunrise/geocoder policies | User can see the calculation basis before trusting a reading |
| Panchanga calendar product | Birth-time Panchanga + Tithi Lord are visible; `/api/panchanga_range` returns date ranges, month grid, activity filtering, Rahu Kala/Yamaganda/Gulika, day/night Choghadiya, planetary Hora windows, SwissEph `rise_trans` sunrise/sunset, SwissEph Tithi/Nakshatra/Yoga end times, richer tithi/nakshatra/vara vrata tags, masa-dependent festival candidates, condition tags, all/any combined condition search, `search_summary`, `festival_details`, location-aware summary, CSV and ICS export | Daily/weekly/monthly Panchanga cards, Rahu Kala/Yamaganda/Gulika, calendar export, end times, vrata/festival rules, day/night sub-windows | Add masa-aware festival naming and dedicated festival drill-down pages | User can use the app as an almanac, not only a natal chart |
| Saved chart workspace | Main UI now reuses `jyotish_chart_library`: save current chart, open selected chart, delete with confirmation, export selected chart, show local library status, use time-aware chart IDs with legacy ID compatibility, export case libraries, unified chart/pair/prashna case list, group/relation/tag metadata, and group/relation filters | Chart library, case workspace, profile compare, share/export workflow | Add editable metadata and profile compare shortcuts | User can return to charts without opening chat |
| Professional report pipeline | Export JSON/SVG/PNG exists; HTML report export produces a standalone printable artifact; `/api/report_artifact` generates backend HTML/PDF artifacts through `report_builder.py`; `/api/thematic_report` now derives real chart/dasha/yoga/shadbala/AV/relationship/career/Jaimini evidence when birth/chart payload is present | Printable HTML/PDF report with evidence, settings, boundaries, and narrative | Add method docs/cURL/OpenAPI snippets and fold thematic sections into final report artifact UX | One-click HTML/PDF and thematic reports work with evidence provenance and safe fallbacks |
| Product-grade chart workspace | South/North Indian charts exist | North/South/East styles, varga grid, print layout, comparison chart | Stabilize chart style controls and add varga grid/report print states | Professional user recognizes the app as chart software |

## P1 Deep Parity Gaps

| Gap | Current state | Same-category expectation | Next implementation task |
|---|---|---|---|
| Calculation catalog/API explorer | `/api/technique_catalog` now exposes searchable registry/productization/UX/API metadata, `api_docs`, row-level `method_docs`, cURL snippets, and minimal OpenAPI operations; `/api/technique_example` runs whitelisted sample payloads; Skill workbench directory cards can run examples with current chart payloads and displays thematic evidence source | Searchable calculation catalog, method docs, API examples | Continue polishing method explanations and expose copy affordances in UI |
| Rectification scanner UX | Rectification panel exists | Event list, time scan candidates, heatmap, reasoned winner | Reuse `vedic-astro-skills/.../time_scan.py` concepts and local rectifier |
| Rule explorer and variant toggles | Settings/export chain records rule variants; `/api/yogas`, `/api/ashtakavarga`, `/api/shadbala` now return result-level `rule_variants`; Skill workbench renders Yoga/Shadbala rule evidence | Yoga/KP/Jaimini/AV variants visible and switchable | Extend realtime variant metadata to KP/Jaimini result cards and add copyable method docs |
| Benchmark dashboard | Tests and benchmark reports exist | Per-module precision table against JHora/PyJHora/VedAstro-style references | Build static benchmark summary from `benchmarks/jyotish/reports` |
| Relationship/family workspace | Synastry has manual birth-data flow, quick Moon longitude flow, deep D9/Kuja/Dasha context, relationship report templates, bi-wheel/composite-style comparison view, spouse-status yoga evidence, UL/DK relationship timing evidence, print-polished relationship HTML/PDF report export, saved partner selection, saved pair records, pair reopen/delete controls, editable chart/pair/prashna case metadata, current-pair JSON/HTML/PDF export, and pair records now carry partner/group metadata in the unified case workspace | Saved partners, bi-wheel/composite-like comparison, dasha sync, relationship case records | Continue with Panchanga search/details and calculation-settings selectors |

## P2 Platform Gaps

| Gap | Current state | Same-category expectation | Next implementation task |
|---|---|---|---|
| Offline/PWA/desktop packaging | Vite app now has manifest, SVG icon, service worker shell cache, install prompt handling, PWA status, desktop packaging spike, and `scripts/desktop_packaging_preflight.py` | Installable PWA or Pake/Tauri-style desktop shell | Run Pake smoke only when CLI is available; defer Tauri until Python sidecar/signing strategy |
| Privacy and trust center | Trust Center now explains local-first storage, local API boundary, AI/remote boundary, local record counts, export local data, terminology preference, and confirm-clear local data | Clear data location, API-key handling, deletion/export controls | Add deeper account/API-key documentation after desktop path |
| First-use onboarding and empty-state path | First screen now offers API health check, demo birth fill, import focus, and actionable saved-library empty copy | New users can create or inspect a chart without reading docs first | Browser smoke the first-run path on mobile and desktop after the next full build |
| Localization modes | Chinese/English labels plus入门/专业/梵文优先 terminology mode | Beginner/pro terminology switch, glossary depth, Sanskrit spellings | Continue copy QA as features expand |
| Ephemeris abstraction | SwissEph/WASM + Python API, calculation provenance records `ephemerisBackend`; backend probe, adapter contract, and candidate spike now report readiness, `package_license`, runtime exposure gates, `PARITY_CASES`, `sun_moon_asc_nodes`, and `longitude_delta_arcsec` thresholds | Replaceable ephemeris backend and explicit accuracy notes | Add a real executable candidate adapter only after local assets/license review are complete |

## Fragment Triage Queue

These files are not hard failures, but they must be classified before the product can be called fully audited:

| Fragment | Likely value | Triage decision needed |
|---|---|---|
| `reading_orchestrator.py` | Full-reading workflow | Referenced by `/api/thematic_report.workflow_orchestration`; keep as workflow vocabulary and future registry execution layer |
| `report_orchestrator.py` | Report packaging | Reused by `/api/thematic_report`; now supports sample, custom, and derived real-evidence modes |
| `report_builder.py` | Report generation | Reused by `/api/report_artifact` for backend HTML/PDF artifact generation; keep for future thematic report assembly |
| `tithi_analyzer.py` | Panchanga depth | Merged into `/api/chart` as `tithi_lord_analysis`; surfaced in 参数/日历 and HTML report |
| `shadbala_advanced.py` | Strength calibration | Integrated into `/api/shadbala.advanced_layer`; keep as evidence layer, not total-score override |
| `dasha_analyzer.py` | Dasha narrative | Integrated into `/api/dasha.vimshottari_analysis` and Dasha UI cards |
| `spouse_status_yoga.py` | Relationship depth | Fold into relationship workspace |
| `curse_yoga_detector.py` | Yoga special cases | Integrated into `/api/yogas.curse_yogas` and Skill workbench boundary cards |
| `hermes_bridge.py` | Agent bridge | External personal WorkBuddy/Hermes automation; archived outside product surface because it writes `~/.workbuddy` |
| `orchestrator_bridge.py` | Agent bridge | Referenced by `/api/thematic_report.workflow_orchestration` as report pipeline bridge |
| `mevg_automation.py` | Validation automation | Integrated as read-only `/api/case_validation.mevg_gate` protocol/status source |

## Immediate Execution Order

1. Completed: visible provenance/Panchanga/workspace panel in the main web app.
2. Completed: static tests guard the panel, Tithi Lord, HTML report export, and Panchanga starter entry.
3. Completed: JSON export metadata carries provenance; HTML report exports a readable artifact.
4. Completed MVP: `tithi_analyzer.py` and `/api/muhurta` are wired into product flow; `report_builder.py` is triaged as PDF backend pattern.
5. Completed MVP: Panchanga starter upgraded to `/api/panchanga_range`, Rahu Kala/Yamaganda/Gulika rows, and CSV export.
6. Completed MVP: Panchanga range now uses chart location for sunrise/sunset when available and supports ICS export.
7. Completed MVP: Panchanga month grid, activity filters, and SwissEph `rise_trans` sunrise/sunset precision are wired into API and web panel.
8. Completed MVP: Tithi/Nakshatra/Yoga end times and Ekadashi/Pradosham/Purnima/Amavasya tags are wired into API, month grid, table, CSV, and ICS export.
9. Completed MVP: Choghadiya and planetary Hora sub-day windows are wired into API, month grid, table, CSV, and ICS export.
10. Completed MVP: dedicated saved chart workspace reuses `jyotish_chart_library` with save/open/delete/export in the main UI.
11. Completed MVP: Synastry can select a saved partner chart from the local library and reuse the full Ashtakoot + D9 + Kuja + Dasha comparison path.
12. Completed MVP: Synastry pair records now save to `jyotish_synastry_pair_library`, show recent saved pairs, and export the current comparison JSON.
13. Completed data fix: saved chart IDs now include birth time and still recognize legacy IDs, preventing same-day/same-place charts from overwriting each other.
14. Completed MVP: pair reopen/delete controls and current synastry HTML report export are wired into the saved case workflow.
15. Completed MVP: richer Panchanga vrata/festival-candidate rules and search-by-condition are wired into API, month grid, table, CSV, ICS and tests.
16. Completed MVP: unified chart/pair/prashna case workspace now has group/relation/tag metadata, group/relation filters, chart rows in case search, selected chart export/delete, and open-chart actions.
17. Completed MVP: relationship report templates now summarize Ashtakoot/D9/Kuja/Dasha evidence, persist with saved pair records, replay from old/new case data, and export into HTML reports.
18. Completed MVP: bi-wheel/composite-style comparison view now shows relationship axes, planet overlay houses, sign relationship tone, and Sun/Moon/Venus/Mars midpoints in the full synastry flow.
19. Completed MVP: `spouse_status_yoga.py` is folded into `/api/relationship`, full synastry deep context, relationship report evidence, saved pair replay/export, and HTML report output.
20. Completed MVP: relationship HTML report export now has a print-polished deliverable section with conclusion hero, evidence cards, bi-wheel axes, overlay table, midpoint cards, spouse-status cards, action lists, and boundaries.
21. Completed MVP: unified case workspace now edits chart/pair/prashna label, group, relation, and tags in place, preserving existing JSON import/export shape.
22. Completed MVP: backend report artifact/PDF pipeline now exposes `/api/report_artifact`, reuses `report_builder.py`, blocks active HTML, returns `pdf_base64` or HTML fallback, and is wired to the web export menu.
23. Completed MVP: richer relationship timing/UL-DK fold-in now returns `/api/relationship.relationship_timing`, reuses `darakaraka_reader.py` and `jaimini.py`, renders UL/DK+Dasha trigger cards in full synastry, and exports `uldk-print-grid` in HTML/PDF reports.
24. Completed MVP: Panchanga search enhancement now supports all/any condition combinations, festival explanation cards, backend `search_summary`/`festival_details`, and location-aware calendar summaries.
25. Completed MVP: calculation settings selectors now persist ayanamsa/node/house/sunrise/geocoder policy, attach settings to chart payload/provenance, and preserve assumptions in JSON/HTML/PDF export paths.
26. Completed MVP: calculation catalog/API Explorer now exposes `/api/technique_catalog`, whitelisted `/api/technique_example`, endpoint/action mapping, current-chart sample payloads, and searchable/runnable Skill workbench cards.
27. Completed MVP: Yoga/Shadbala rule fragments now run through product APIs: `/api/yogas` reuses `curse_yoga_detector.py` and `/api/shadbala` reuses `shadbala_advanced.py`; Skill workbench renders both with rule boundaries.
28. Completed MVP: `dasha_analyzer.py` now powers Vimshottari analysis inside `/api/dasha`, while `dasha_calculator_enhanced.py` supplies five-level Dasha context for UI cards.
29. Completed MVP: remaining workflow/bridge fragments are classified: thematic report exposes reading/report/orchestrator bridge metadata, case validation exposes MEVG gate status, Hermes bridge is archived as external personal automation rather than product UI.
30. Completed MVP: `/api/thematic_report` now upgrades from sample evidence to `derived_chart_evidence` when birth/chart payload is provided, and the UI exposes evidence source/module status.
31. Completed MVP: Technique Directory/API Explorer now exposes method docs, cURL snippets, minimal OpenAPI operations, endpoint notes, and row-level API doc keys.
32. Completed MVP: PWA manifest/service worker/installability status and local-first Trust Center are visible in the app.
33. Completed MVP: terminology mode now affects glossary display and provenance/JSON/HTML export.
34. Completed spike: desktop packaging path is documented, README links it, and `scripts/desktop_packaging_preflight.py` checks PWA/Pake/Tauri readiness.
35. Completed MVP: First-use onboarding and empty-state path now gives new users API health check, demo chart fill, import focus, and clearer local-library empty copy.
36. Completed MVP: browser smoke covered the first-run desktop/mobile path, example chart generation, runtime health entry, and Banner missing-field guard.
37. Completed feasibility guard: ephemeris abstraction now has a read-only backend probe plus research note documenting SwissEph Python/WASM, xalen, VedAstro, PyJHora readiness and license posture.
38. Completed contract guard: `scripts/ephemeris_adapter_contract.py` now emits SwissEph Python baseline parity rows for Sun/Moon/Asc/Rahu/Ketu with `longitude_delta_arcsec` acceptance thresholds.
39. Completed candidate spike guard: `scripts/ephemeris_candidate_adapter_spike.py` keeps SwissEph WASM and xalen as blocked candidates until license and parity gates pass.
40. Completed candidate license gate: `scripts/ephemeris_candidate_adapter_spike.py` detects local WASM assets, records `@swisseph/browser` as `AGPL-3.0`, `swisseph-wasm` as `GPL-3.0-or-later`, and keeps xalen marked as no local executable.
41. Next: add a real executable candidate adapter only after local xalen assets or a reviewed WASM execution harness is available.
