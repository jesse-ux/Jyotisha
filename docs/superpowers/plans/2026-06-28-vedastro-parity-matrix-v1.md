# VedAstro Parity Matrix v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a repeatable VedAstro parity matrix that maps public VedAstro capability areas to local assets, external adapter options, and implementation priorities.

**Architecture:** Add one focused generator script that consumes local capability audit output and a curated VedAstro seed list, then writes JSON and Markdown snapshots. Keep the matrix separate from strict adjudicator runtime so it cannot accidentally assert unverified production parity.

**Tech Stack:** Python 3 standard library, existing `scripts/audit_capabilities.py`, existing research markdown conventions.

## Global Constraints

- Do not copy VedAstro implementation code.
- Treat VedAstro results as external adapter evidence unless promoted by local tests or oracle artifacts.
- Do not modify strict workflow scoring in this task.
- Do not stage unrelated untracked workspace residue.

---

### Task 1: Generator And Tests

**Files:**
- Create: `scripts/vedastro_parity_matrix.py`
- Create: `tests/test_vedastro_parity_matrix.py`
- Modify: `docs/research/ACTIVE_FRONTS.md`

**Interfaces:**
- Produces: `build_matrix(audit: dict | None = None) -> dict`
- Produces: `render_markdown(matrix: dict) -> str`
- Produces CLI: `python3 scripts/vedastro_parity_matrix.py --format json|markdown --write`

- [ ] **Step 1: Write tests for P0 rows and contracts**

Run: `python3 -m pytest tests/test_vedastro_parity_matrix.py -q`

- [ ] **Step 2: Implement the generator**

Create the matrix with deterministic row ordering and explicit allowed values.

- [ ] **Step 3: Generate snapshots**

Run: `python3 scripts/vedastro_parity_matrix.py --write`

- [ ] **Step 4: Verify**

Run:

```bash
python3 -m pytest tests/test_vedastro_parity_matrix.py -q
python3 scripts/vedastro_parity_matrix.py --format json >/tmp/vedastro_parity_matrix.json
```

- [ ] **Step 5: Commit**

Stage only the parity matrix files, tests, and Active Fronts update.
