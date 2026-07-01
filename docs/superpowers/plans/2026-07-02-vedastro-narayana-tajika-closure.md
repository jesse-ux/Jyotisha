# VedAstro Narayana Tajika Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use systematic-debugging, test-driven-development, and verification-before-completion. Execute inline in this session because the user requested immediate repair and cloud git sync.

**Goal:** Repair the current VedAstro official full snapshot regressions, tighten Narayana/Tajika external-closure boundaries, clean remaining governance residue, and push the verified result.

**Architecture:** Keep local Jyotish calculation paths intact. Fix the VedAstro adapter at the official snapshot orchestration boundary so runner/python-bridge bundles are honored before REST fallback, then update closure/audit surfaces to state Narayana/Tajika external calibration honestly.

**Tech Stack:** Python, pytest, Swiss Ephemeris wrappers, repository markdown/json governance reports, git.

## Global Constraints

- Do not copy AGPL PyJHora code into permissive local code.
- Treat VedAstro official evidence as external context; local fallback must remain explicit when official evidence is blocked.
- Use Vimshottari + Narayana and relevant divisional evidence in strict claims, but mark external oracle gaps honestly.
- Stage and push only intentional changes.

---

### Task 1: Fix VedAstro official full snapshot bundle orchestration

**Files:**
- Modify: `scripts/vedastro_service_adapter.py`
- Test: `tests/test_vedastro_official_full_snapshot.py`

**Verification:**
- `python3 -m pytest tests/test_vedastro_official_full_snapshot.py -q`

**Expected behavior:**
- Official capability runner bundle can satisfy snapshot without REST endpoint.
- Official python bridge bundle can satisfy snapshot without REST endpoint.
- REST fallback skips sections already filled by runner/python bridge bundles.

### Task 2: Tighten Narayana/Tajika closure evidence

**Files:**
- Inspect/modify if needed: `scripts/narayana_dasha.py`
- Inspect/modify if needed: `scripts/tajika.py`
- Inspect/modify if needed: `README.md`, `docs/research/*.md`, `docs/benchmark/*.md`

**Verification:**
- Focused Narayana/Tajika tests if existing.
- `python3 scripts/preflight_fragment_scan.py`

**Expected behavior:**
- Project surfaces do not overstate Narayana subperiod or Tajika annual closure beyond external target-set evidence.

### Task 3: Resolve remaining governance residue and sync git

**Files:**
- Intentional docs/governance updates only.
- Leave unrelated generated artifacts unstaged unless they are part of the fix.

**Verification:**
- Focused pytest commands from Task 1 and current strict workflow smoke tests.
- `git status --short`
- Commit and push current branch.
