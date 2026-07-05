# B.V. Raman Long Report Book Structure Implementation Plan
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
**Goal:** Convert the existing single-file comprehensive chart study into a reusable long-report book structure that can serve Markdown-first authoring and later PDF export.
**Architecture:** Keep the existing [`/Users/wuyongnaren/Documents/印度占星/docs/reports/bv_raman_style_comprehensive_chart_research_REDACTED_DATE_REDACTED_TIME_v1.md`](/Users/wuyongnaren/Documents/印度占星/docs/reports/bv_raman_style_comprehensive_chart_research_REDACTED_DATE_REDACTED_TIME_v1.md) as the source draft, then add a new `chart_research_REDACTED_DATE_REDACTED_TIME/` directory with `book.md` as the main concatenation entry, chapter files for thematic expansion, appendix files for raw evidence, and a small metadata file for later export tooling. No new PDF pipeline is added now because none is already wired in this repo.
**Tech Stack:** Markdown, YAML metadata, existing repo docs conventions, local JSON artifacts under `.tmp/chart_study`.
## Global Constraints
- Reuse existing report content; do not rewrite the full report from scratch.
- Keep Markdown as the source of truth; PDF remains an export artifact, not a second authoring format.
- Do not add new dependencies or a speculative PDF toolchain.
- Preserve honesty boundaries about VedAstro/PyJHora/jyotishganit closure.
- Prefer links to existing JSON artifacts over copying large raw blobs into prose chapters.
- Before editing chapters, read `docs/reports/chart_research_REDACTED_DATE_REDACTED_TIME/README.md` and `docs/reports/chart_research_REDACTED_DATE_REDACTED_TIME/appendices/H_error_ledger_and_preflight.md`.

### Task 1: Add the long-report container
**Files:**
- Create: `/Users/wuyongnaren/Documents/印度占星/docs/reports/chart_research_REDACTED_DATE_REDACTED_TIME/README.md`
- Create: `/Users/wuyongnaren/Documents/印度占星/docs/reports/chart_research_REDACTED_DATE_REDACTED_TIME/book.md`
- Create: `/Users/wuyongnaren/Documents/印度占星/docs/reports/chart_research_REDACTED_DATE_REDACTED_TIME/metadata.yaml`
**Interfaces:**
- Consumes: existing v1 report and `.tmp/chart_study/*.json`
- Produces: one stable report root that later tools or humans can extend
- [ ] **Step 1: Create report root directory structure**
- [ ] **Step 2: Add `README.md` explaining source-of-truth and export intent**
- [ ] **Step 3: Add `metadata.yaml` for title/author/date/export hints**
- [ ] **Step 4: Add `book.md` listing chapters and appendices in final reading order**

### Task 2: Add chapter skeletons mapped to the requested methodology
**Files:**
- Create: `/Users/wuyongnaren/Documents/印度占星/docs/reports/chart_research_REDACTED_DATE_REDACTED_TIME/chapters/*.md`
**Interfaces:**
- Consumes: user-requested B.V. Raman / Parāśara / Jaimini scope
- Produces: one file per chapter so later expansion stays bounded
- [ ] **Step 1: Create 00–21 chapter files**
- [ ] **Step 2: Put a short contract at top of each chapter saying what belongs there**
- [ ] **Step 3: Pre-fill only the first few chapters with live links to existing content/data**
- [ ] **Step 4: Leave later chapters as clean skeletons instead of fake filled content**

### Task 3: Add appendix and data references
**Files:**
- Create: `/Users/wuyongnaren/Documents/印度占星/docs/reports/chart_research_REDACTED_DATE_REDACTED_TIME/appendices/*.md`
- Populate/Reference: `/Users/wuyongnaren/Documents/印度占星/docs/reports/chart_research_REDACTED_DATE_REDACTED_TIME/data/`
**Interfaces:**
- Consumes: `.tmp/chart_study/*.json`
- Produces: report appendix map and raw evidence pointers
- [ ] **Step 1: Create appendix stubs for raw tables, dasha boundaries, varga positions, parity, audit, glossary**
- [ ] **Step 2: Reference current `.tmp/chart_study` artifacts instead of duplicating them**
- [ ] **Step 3: Explain which appendices are ready vs blocked**

### Task 4: Connect old draft into new main chain
**Files:**
- Modify/Create: `/Users/wuyongnaren/Documents/印度占星/docs/reports/chart_research_REDACTED_DATE_REDACTED_TIME/README.md`
- Keep: `/Users/wuyongnaren/Documents/印度占星/docs/reports/bv_raman_style_comprehensive_chart_research_REDACTED_DATE_REDACTED_TIME_v1.md`
**Interfaces:**
- Consumes: existing v1 draft headings and current chapter structure
- Produces: migration notes from monolith draft to book structure
- [ ] **Step 1: Mark the old v1 report as the seed draft**
- [ ] **Step 2: Map v1 sections to new chapter files**
- [ ] **Step 3: Keep migration incremental instead of copying all prose immediately**

### Task 5: Verify structure only
**Files:**
- Verify: report directory tree and links
**Interfaces:**
- Consumes: created Markdown files
- Produces: a structure that humans can open immediately
- [ ] **Step 1: List created files**
- [ ] **Step 2: Open `book.md` and `README.md` to confirm links**
- [ ] **Step 3: Avoid claiming PDF export exists until an actual exporter is wired and tested**
