# Birth Time Journey Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic first-use birth-time journey that separates reported and active times, routes uncertain data into free rectification, and connects the web UI to the existing candidate scanner.

**Architecture:** A pure TypeScript state machine owns route and application decisions. An authenticated Next.js route adapts Supabase persistence and the existing Python scan/score API to that state machine. A focused React component renders the input contract, while `page.tsx` only coordinates the established onboarding shell.

**Tech Stack:** Next.js 16 App Router, React 19, TypeScript, Zod, Supabase/PostgreSQL, Node test runner, Python Jyotish API.

## Global Constraints

- Agent copy may guide the user but may not determine route, confidence, or application eligibility.
- `reported_birth_time` is immutable historical input; `birth_time` mirrors only `active_birth_time` for compatibility.
- Rectification intake and questions never call the consultation billing endpoint.
- Questionnaire scoring cannot apply an exact minute because the current engine only ranks coarse clusters.
- Scanner failure must fail closed into rectification.
- Do not modify or import files from `.workbuddy` mirrors.

---

### Task 1: Deterministic Journey Domain

**Files:**
- Create: `frontend/src/lib/birth-time-journey.ts`
- Test: `frontend/tests/birth-time-journey.test.ts`

**Interfaces:**
- Produces: `assessBirthTime(input: BirthTimeAssessmentInput, scan?: CandidateScan): JourneySnapshot`
- Produces: `scoreJourneyAnswers(snapshot: JourneySnapshot, scoring: RectificationScoring): JourneySnapshot`
- Produces: source, period, status, route, input, snapshot, scan, and scoring types used by later tasks.

- [ ] Write table-driven failing tests for all five sources, invalid source-specific input, stable hospital scan, sensitive hospital scan, scanner failure, and `canApply=false` after questionnaire scoring.
- [ ] Run `npm test -- --test-name-pattern='birth time journey'` and confirm the module is missing.
- [ ] Implement exhaustive source routing and scan stability comparison without persistence or prose generation.
- [ ] Run the focused test and confirm every route and gate passes.

### Task 2: Birth-Time Persistence Contract

**Files:**
- Create: `frontend/supabase/migrations/20260717020000_birth_time_journey.sql`
- Create: `tests/test_birth_time_journey_contract.py`

**Interfaces:**
- Produces: profile columns and `public.birth_time_rectification_cases` expected by the route.

- [ ] Write a failing SQL contract test for columns, checks, backfill, foreign key, RLS policies, and column-level grants.
- [ ] Run `/Users/jesse/Downloads/Copse/astrology/yinduzhanxing/.venv/bin/python -m pytest -q tests/test_birth_time_journey_contract.py` and confirm the migration is missing.
- [ ] Add an idempotent migration that backfills old `birth_time` values, constrains enums and uncertainty ranges, creates the cases table, and grants only owner-scoped operations.
- [ ] Run the SQL contract test and the existing Supabase contract tests.

### Task 3: Authenticated Journey Service and Route

**Files:**
- Create: `frontend/src/lib/birth-time-journey-service.ts`
- Create: `frontend/src/app/api/birth-time-journey/route.ts`
- Test: `frontend/tests/birth-time-journey-service.test.ts`

**Interfaces:**
- Consumes: domain types and `assessBirthTime`/`scoreJourneyAnswers` from Task 1.
- Produces: `POST /api/birth-time-journey` events `assess` and `answer_question`.

- [ ] Write failing service tests with fake persistence and scanner ports for stable assessment, scanner failure, and answer accumulation.
- [ ] Implement a typed service port so tests never require live Supabase or Python.
- [ ] Implement the route's Zod boundary, authenticated profile read, free scanner calls, case persistence, and sanitized JSON response.
- [ ] Run focused service/domain tests and lint.

### Task 4: First-Use Birth Intake UI

**Files:**
- Create: `frontend/src/components/birth-time-intake.tsx`
- Create: `frontend/src/components/birth-time-rectification.tsx`
- Modify: `frontend/src/app/page.tsx`
- Modify: `frontend/src/app/globals.css`
- Test: `frontend/tests/birth-time-intake.test.ts`

**Interfaces:**
- Consumes: the journey source/status types and `JourneySnapshot`.
- Produces: source-specific profile draft updates, assessment requests after location, and answer events.

- [ ] Write failing tests for source-specific required fields, summary labels, and payload construction.
- [ ] Implement the source cards, conditional fields, accessible labels, and uncertainty/period copy.
- [ ] Implement the rectification status/question card with progress and explicit non-application language.
- [ ] Replace the old exact-time-only fields in `page.tsx`, extend profile parsing/persistence, add the `rectification` onboarding step, and block consultation until an active time exists.
- [ ] Add scoped responsive styles and run the focused UI helper tests plus lint.

### Task 5: Compatibility and End-to-End Verification

**Files:**
- Modify: `frontend/src/app/api/onboarding/route.ts`
- Modify: `frontend/src/mastra/index.ts`
- Modify: `tests/test_frontend_productization.py`

**Interfaces:**
- Consumes: active time and birth-time status persisted by earlier tasks.
- Produces: existing onboarding and consultation behavior with deterministic entry mode.

- [ ] Update onboarding completeness to require an active/confirmed time while accepting backfilled legacy profiles.
- [ ] Add `entryMode` to the consultation input and pass the deterministic value to the Python workflow instead of hard-coding `direct_chart`.
- [ ] Add regression assertions that the web path exposes five time-confidence choices, keeps rectification free, and contains no client-controlled application gate.
- [ ] Run frontend tests, relevant Python tests, lint, and `npm run build`.
- [ ] Start Next.js from the worktree and manually verify the first-use UI, source-dependent fields, rectification card, `/api/birth-time-journey` authentication behavior, and absence of consultation credit requests.

### Task 6: Review and Commit

**Files:**
- Review every path changed by Tasks 1-5.

**Interfaces:**
- Produces: a review-clean commit on `codex/birth-time-journey`.

- [ ] Run the TypeScript no-excuse checks and measure pure LOC for every changed source file.
- [ ] Review boundary parsing, exhaustive variants, RLS, billing isolation, and legacy compatibility.
- [ ] Re-run the full frontend test/lint/build gate and relevant Python contract tests on the final diff.
- [ ] Commit the implementation with a focused message and record the worktree path and commit SHA.
