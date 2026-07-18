# Birth-Time Evidence Rectification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Continue the completed birth-time questionnaire into structured life-event scoring, candidate review, and guarded user confirmation.

**Architecture:** Extend the pure TypeScript journey state machine first, then add one isolated Python event adjudicator behind the existing Jyotish API. The authenticated Next.js service owns persistence and confirmation; React renders only the server-returned input state.

**Tech Stack:** Python 3.12, pytest, Next.js 16 App Router, React 19, TypeScript 5, Zod 3, Supabase/PostgreSQL, Node test runner.

## Global Constraints

- Agent prose never determines state, candidate score, confidence, route, or application permission.
- `reported_birth_time` is immutable; only a confirmed server-side result may update `active_birth_time` and legacy `birth_time`.
- Rectification events use the free journey route and never call `/api/consult`.
- Life-event dates and domains are structured; free-form text never affects scoring.
- Low and medium results cannot apply a time. High results require an explicit confirmation event.
- The UI must say “候选时间” or “当前排盘使用时间”, never “真实出生时间”.
- Preserve unrelated dirty-worktree changes and do not reset the repository.

---

### Task 1: Deterministic Journey State and Event Contracts

**Files:**
- Modify: `frontend/src/lib/birth-time-journey.ts`
- Test: `frontend/tests/birth-time-journey.test.ts`

**Interfaces:**
- Produces: `lifeEventSchema`, `candidateResultSchema`, extended `JourneySnapshot`, `withCompletedQuestionnaire()`, `withCandidateResult()`, and `withConfirmedCandidate()`.
- Consumes: existing `JourneySnapshot` and `RectificationScoring`.

- [ ] **Step 1: Write failing state-transition tests**

```ts
test("the final questionnaire answer requests dated life events", () => {
  const next = withRectificationScoring(initial, {
    answeredCount: 8,
    candidateClusterRankings: [{ cluster: "middle_candidate_cluster", score: 5 }],
    nextRoundQuestions: [],
  });
  assert.equal(next.input, "life_events");
  assert.equal(next.assistantIntent, "collect_dated_life_events");
  assert.equal(next.canApply, false);
});

test("only a high candidate enters confirmation", () => {
  assert.equal(withCandidateResult(eventSnapshot, mediumResult).input, "candidate_actions");
  assert.equal(withCandidateResult(eventSnapshot, highResult).input, "candidate_confirmation");
});
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `cd frontend && node --test tests/birth-time-journey.test.ts`

Expected: FAIL because the new input, intent, schemas, and transition functions do not exist.

- [ ] **Step 3: Implement the minimal typed state model**

```ts
export const lifeEventSchema = z.object({
  id: z.string().uuid(),
  domain: z.enum(["education", "relocation", "relationship", "career", "health_pressure"]),
  date: z.string(),
  precision: z.enum(["year", "month", "day"]),
}).strict().readonly();

export function withCandidateResult(snapshot: JourneySnapshot, result: CandidateResult): JourneySnapshot {
  switch (result.confidence) {
    case "low": return { ...snapshot, state: "rectifying", input: "life_events", canApply: false };
    case "medium": return { ...snapshot, state: "candidate", input: "candidate_actions", canApply: false };
    case "high": return { ...snapshot, state: "confirming", input: "candidate_confirmation", canApply: true };
    default: return assertNever(result.confidence);
  }
}
```

- [ ] **Step 4: Run the focused test and verify GREEN**

Run: `cd frontend && node --test tests/birth-time-journey.test.ts`

Expected: all birth-time journey domain tests pass.

---

### Task 2: Local Candidate Event Adjudicator

**Files:**
- Create: `scripts/active_rectification_events.py`
- Test: `tests/test_active_rectification_events.py`

**Interfaces:**
- Produces: `score_life_events(request: RectificationEventRequest) -> CandidateResult`.
- Consumes: stored birth date/range/location, structured events, `domain_calculation_service`, `varga`, `jaimini`, Vimshottari timeline, and Narayana Dasha.

- [ ] **Step 1: Write failing Python tests for segments, thresholds, and abstention**

```python
def test_high_confidence_requires_four_events_three_domains_and_narrow_leader() -> None:
    result = score_life_events(high_fixture())
    assert result["confidence"] == "high"
    assert result["winning_segment"]["start_time"] <= result["winning_segment"]["end_time"]
    assert result["can_apply"] is True

def test_tied_candidates_abstain() -> None:
    result = score_life_events(tied_fixture())
    assert result["confidence"] == "low"
    assert "tied_leader" in result["reasons"]
    assert result["can_apply"] is False
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `.venv/bin/python -m pytest -q tests/test_active_rectification_events.py`

Expected: collection fails because `active_rectification_events` does not exist.

- [ ] **Step 3: Implement frozen request models and fixed rule tables**

```python
class LifeEvent(TypedDict):
    id: str
    domain: EventDomain
    date: str
    precision: EventPrecision

PRECISION_WEIGHTS: Final = {"day": 1.0, "month": 0.8, "year": 0.5}
DOMAIN_LAYERS: Final = {
    "education": ("D24", (4, 5, 9)),
    "relocation": ("D4", (4, 12)),
    "relationship": ("D9", (7,)),
    "career": ("D10", (10,)),
    "health_pressure": ("D30", (6, 8, 12)),
}
```

- [ ] **Step 4: Implement minute scanning, contiguous signature segments, dual-Dasha rule IDs, and confidence thresholds**

Every candidate row records actual D1/D4/D9/D10/D24/D30 data. Adjacent equal signatures collapse into segments. Each event score emits rule IDs for Vimshottari lord/domain-house, Narayana sign/domain-house, and domain-Varga support; unavailable mandatory layers produce a low-confidence abstention.

- [ ] **Step 5: Run the focused test and verify GREEN**

Run: `.venv/bin/python -m pytest -q tests/test_active_rectification_events.py`

Expected: all event adjudicator tests pass without network access.

---

### Task 3: Python API Boundary

**Files:**
- Modify: `scripts/jyotish_api_server.py`
- Modify: `tests/test_active_rectification_api.py`

**Interfaces:**
- Produces: `POST /api/active_rectification_events`.
- Consumes: `score_life_events()` from Task 2.

- [ ] **Step 1: Add a failing API contract test**

```python
def test_active_rectification_events_api_scores_structured_events() -> None:
    result = _handler()._compute_active_rectification_events(valid_payload())
    assert result["success"] is True
    assert result["endpoint"] == "active_rectification_events"
    assert result["candidate_result_id"]
```

- [ ] **Step 2: Run and verify RED**

Run: `.venv/bin/python -m pytest -q tests/test_active_rectification_api.py -k events`

Expected: FAIL because the handler and route are missing.

- [ ] **Step 3: Add strict payload parsing and the new handler route**

The HTTP method validates date/range/location and three-to-six events before calling `score_life_events`; invalid variants raise `BadRequest`. Register the path in POST dispatch, endpoint catalog, and capability metadata.

- [ ] **Step 4: Run and verify GREEN**

Run: `.venv/bin/python -m pytest -q tests/test_active_rectification_api.py`

Expected: all active rectification API tests pass.

---

### Task 4: Journey Service, Engine, Store, and SQL

**Files:**
- Modify: `frontend/src/lib/birth-time-journey-service.ts`
- Modify: `frontend/src/lib/birth-time-journey-engine.ts`
- Modify: `frontend/src/lib/birth-time-journey-adapters.ts`
- Modify: `frontend/src/lib/birth-time-journey-store.ts`
- Create: `frontend/supabase/migrations/20260718010000_birth_time_evidence_rectification.sql`
- Modify: `frontend/tests/birth-time-journey-service.test.ts`
- Modify: `frontend/tests/birth-time-journey-adapters.test.ts`
- Modify: `tests/test_birth_time_journey_contract.py`

**Interfaces:**
- Produces: engine `scoreEvents`, store `saveCandidateResult`/`confirmCandidate`, service `submitLifeEvents`/`saveCandidate`/`confirmCandidate`.
- Consumes: Task 1 schemas and Task 3 API.

- [ ] **Step 1: Write failing service tests**

```ts
test("submitting life events persists the server result", async () => {
  const result = await service.submitLifeEvents("user-1", "case-1", events);
  assert.equal(result.candidateResult?.confidence, "medium");
  assert.equal(result.snapshot.input, "candidate_actions");
});

test("confirmation rejects a stale result id", async () => {
  await assert.rejects(
    service.confirmCandidate("user-1", "case-1", "stale", "14:24"),
    StaleCandidateConfirmationError,
  );
});
```

- [ ] **Step 2: Run focused frontend tests and verify RED**

Run: `cd frontend && node --test tests/birth-time-journey-service.test.ts tests/birth-time-journey-adapters.test.ts`

Expected: FAIL because the new ports and methods are missing.

- [ ] **Step 3: Implement engine adapter and service transitions**

`scoreEvents` posts only stored assessment/range/location plus parsed events. `submitLifeEvents` reloads the owner-scoped case, computes the result, transitions through `withCandidateResult`, and persists atomically. `confirmCandidate` rechecks state, result ID, confidence, time, and ownership before store confirmation.

- [ ] **Step 4: Write the failing SQL contract assertions and verify RED**

Run: `.venv/bin/python -m pytest -q tests/test_birth_time_journey_contract.py`

Expected: FAIL because event/result columns and grants are absent.

- [ ] **Step 5: Add the migration and store persistence**

The migration adds `life_events`, `candidate_result`, `event_scoring_version`, `candidate_result_id`, `candidate_saved_at`, and `confirming` status. Browser grants exclude score/result/confirmation writes. The admin store updates profile active time only inside `confirmCandidate`.

- [ ] **Step 6: Run service, adapter, and SQL tests and verify GREEN**

Run: `cd frontend && node --test tests/birth-time-journey-service.test.ts tests/birth-time-journey-adapters.test.ts && cd .. && .venv/bin/python -m pytest -q tests/test_birth_time_journey_contract.py`

Expected: all selected tests pass.

---

### Task 5: Route and Client Boundary

**Files:**
- Modify: `frontend/src/app/api/birth-time-journey/route.ts`
- Modify: `frontend/src/lib/birth-time-journey-client.ts`
- Modify: `frontend/tests/birth-time-journey-client.test.ts`

**Interfaces:**
- Produces: client calls `submitBirthTimeLifeEvents`, `saveBirthTimeCandidate`, `confirmBirthTimeCandidate`.
- Consumes: Task 4 service methods.

- [ ] **Step 1: Write failing parser and request tests**

```ts
test("client accepts only a guarded high-confirmation response", () => {
  const parsed = parseJourneyResponse(highConfirmationResponse);
  assert.equal(parsed.snapshot.input, "candidate_confirmation");
});

test("client rejects a rectification response that applies without confirmation state", () => {
  assert.throws(() => parseJourneyResponse(unsafeResponse));
});
```

- [ ] **Step 2: Run and verify RED**

Run: `cd frontend && node --test tests/birth-time-journey-client.test.ts`

Expected: FAIL on missing response fields and client functions.

- [ ] **Step 3: Extend strict event schemas and exhaustive route dispatch**

The route accepts only `submit_life_events`, `save_candidate`, and `confirm_candidate` shapes defined by Zod `.strict()`. It maps stale confirmation and insufficient evidence to 409 and keeps all server failures fail-closed.

- [ ] **Step 4: Run and verify GREEN**

Run: `cd frontend && node --test tests/birth-time-journey-client.test.ts`

Expected: all client boundary tests pass.

---

### Task 6: Life-Event and Candidate UI

**Files:**
- Create: `frontend/src/components/birth-time-life-events.tsx`
- Create: `frontend/src/components/birth-time-candidate-result.tsx`
- Modify: `frontend/src/components/birth-time-rectification.tsx`
- Modify: `frontend/src/app/page.tsx`
- Modify: `frontend/src/app/globals.css`
- Modify: `frontend/DESIGN.md`
- Modify: `frontend/tests/birth-time-rectification-contract.test.ts`

**Interfaces:**
- Produces: accessible event form and low/medium/high result actions.
- Consumes: Task 5 client calls and parsed `JourneyClientResponse`.

- [ ] **Step 1: Add failing UI contract assertions**

```ts
test("rectification renders the life-event step from the server input", () => {
  assert.match(component, /snapshot\.input === "life_events"/);
  assert.match(component, /BirthTimeLifeEvents/);
  assert.match(component, /BirthTimeCandidateResult/);
});
```

- [ ] **Step 2: Run and verify RED**

Run: `cd frontend && node --test tests/birth-time-rectification-contract.test.ts`

Expected: FAIL because the new components and input branches are missing.

- [ ] **Step 3: Document and implement the component states**

Extend the existing Birth time intake component in `DESIGN.md` with life-event rows, candidate action states, and confirmation copy. Implement three initial event rows, a six-row maximum, persistent labels, precision-dependent native inputs, live errors, and existing design tokens only.

- [ ] **Step 4: Wire page handlers and ready transition**

`page.tsx` submits events, saves candidates, and confirms only through Task 5 client functions. A ready response updates profile state and proceeds to existing onboarding; no client code sets `activeTime` or `canApply`.

- [ ] **Step 5: Run and verify GREEN**

Run: `cd frontend && node --test tests/birth-time-rectification-contract.test.ts`

Expected: the full UI contract passes.

---

### Task 7: Final Verification and Browser QA

**Files:**
- Review all files changed in Tasks 1–6.

**Interfaces:**
- Produces: fresh automated and browser evidence for the approved design.

- [ ] **Step 1: Run focused Python and frontend tests**

Run: `.venv/bin/python -m pytest -q tests/test_active_rectification_events.py tests/test_active_rectification_api.py tests/test_birth_time_journey_contract.py`

Run: `cd frontend && npm test`

Expected: zero failures.

- [ ] **Step 2: Run lint, TypeScript, and production build**

Run: `cd frontend && npm run lint && npx tsc --noEmit && npm run build`

Expected: exit code 0 for every command.

- [ ] **Step 3: Run no-excuse checks on changed Python and TypeScript sources**

Run the programming skill checkers against the changed source files and repair every new violation without refactoring unrelated legacy code.

- [ ] **Step 4: Run real-browser visual QA**

Start the verified application, drive the final questionnaire answer, event validation, low/medium/high candidate cards, and confirmation fixture at 375px, 768px, and 1280px. Verify keyboard labels, live regions, overflow, motion, and that no consultation request is issued before ready.

- [ ] **Step 5: Review the final diff**

Confirm every spec section has implementation evidence, `reported_birth_time` remains immutable, client payloads cannot inject score/confidence/application fields, and unrelated dirty files were not overwritten.
