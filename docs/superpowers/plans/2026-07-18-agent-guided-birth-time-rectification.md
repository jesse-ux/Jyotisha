# Agent-Guided Birth-Time Rectification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the fixed questionnaire/manual comparison path with a deterministic, versioned JourneyTurn that asks one high-information question at a time, lets an Agent create review-only evidence drafts, and automatically advances to the next question or guarded result.

**Architecture:** Extend the existing `BirthTimeJourney` as the only state authority. A pure planner ranks canonical evidence domains from actual candidate Varga differences; a constrained Mastra Agent may phrase a server-selected question and extract a draft, but only authenticated structured UI actions can confirm evidence, run scoring, save a candidate, or confirm an active time. Persist `nextAction`, progress, optimistic version, idempotency receipts, drafts, and scoring jobs so refresh/resume cannot produce a dead end.

**Tech Stack:** TypeScript 5, Zod 3, Next.js 16.2 Route Handlers, React 19 Client Components, Mastra 1.50, Supabase/PostgreSQL, Python 3.11+, Node test runner, pytest.

## Global Constraints

- Preserve all existing dirty work; inspect the diff before every edit and never reset, restore, or overwrite unrelated changes.
- Agent prose never determines candidate ranking, confidence, route, progress, or permission.
- Every scored event is structured and explicitly confirmed by the user.
- Baseline scoring requires at least three confirmed events across two domains.
- Low-confidence adaptive questioning is capped at three displayed questions; skip consumes the displayed round.
- Medium confidence saves only; high confidence still requires explicit confirmation of the matching result ID and representative time.
- `reported_birth_time` remains immutable; only guarded confirmation may update `active_birth_time`.
- Keep the legacy response `canApply` compatibility parser, but new UI and Agent permissions use `canConfirmCandidate`.
- Use “候选时间” and “当前排盘使用时间”; never claim a proven true birth minute.
- Read `frontend/node_modules/next/dist/docs/01-app/01-getting-started/15-route-handlers.md` and `05-server-and-client-components.md` before editing Next.js code.
- No new runtime dependency is permitted.
- Each implementation task follows red → green TDD and stages only files owned by that task.

---

### Task 1: Deterministic Candidate-Difference Question Planner

**Files:**
- Modify: `scripts/active_rectification_questions.py`
- Modify: `frontend/src/lib/birth-time-journey-adapters.ts`
- Create: `frontend/src/lib/birth-time-question-planner.ts`
- Modify: `tests/test_active_rectification_questions.py`
- Create: `frontend/tests/birth-time-question-planner.test.ts`

**Interfaces:**
- Consumes: candidate scan samples with D4/D9/D10/D24/D30 Ascendant signs.
- Produces: `planEvidenceQuestion(input: QuestionPlannerInput): QuestionSpec | null` and `QuestionSpec` for Tasks 2, 4, and 6.

- [ ] **Step 1: Add failing Python coverage for all canonical domain Vargas**

```python
def test_candidate_recast_contains_all_evidence_domain_vargas(monkeypatch):
    report = build_questionnaire(
        "1993-04-17 14:30", 30, 30,
        lat=31.2304, lon=121.4737, tz=8,
    )
    sample = report["candidate_scan"]["samples"][0]
    assert {"D4", "D9", "D10", "D24", "D30"}.issubset(sample["varga_lagna"])
```

- [ ] **Step 2: Run the Python test and verify RED**

Run: `.venv/bin/python -m pytest -q tests/test_active_rectification_questions.py -k evidence_domain_vargas`

Expected: FAIL because `_candidate_recast()` currently omits division 4.

- [ ] **Step 3: Add D4 to the recast and expose five parsed signs**

Change `varga.calc_all_vargas(... divisions=[4, 9, 10, 24, 30, 60])`. Extend `RectificationQuestionnaire.samples` and the adapter with `d4Sign`, `d9Sign`, `d10Sign`, `d24Sign`, and `d30Sign`.

- [ ] **Step 4: Add failing planner tests**

```ts
test("planner chooses the unasked domain with the largest candidate split", () => {
  const question = planEvidenceQuestion({
    phase: "baseline",
    samples: [
      { d4Sign: "Aries", d9Sign: "Cancer", d10Sign: "Leo", d24Sign: "Gemini", d30Sign: "Virgo" },
      { d4Sign: "Taurus", d9Sign: "Cancer", d10Sign: "Leo", d24Sign: "Gemini", d30Sign: "Virgo" },
      { d4Sign: "Gemini", d9Sign: "Cancer", d10Sign: "Leo", d24Sign: "Gemini", d30Sign: "Virgo" },
    ],
    askedDomains: [],
    coveredDomains: [],
    adaptiveRound: 0,
  });
  assert.equal(question?.domain, "relocation");
  assert.equal(question?.phase, "baseline");
});

test("planner never repeats a domain and returns null after canonical domains are exhausted", () => {
  assert.equal(planEvidenceQuestion({
    phase: "baseline",
    samples: [],
    askedDomains: ["education", "relocation", "relationship", "career", "health_pressure"],
    coveredDomains: [],
    adaptiveRound: 0,
  }), null);
});
```

- [ ] **Step 5: Run the planner test and verify RED**

Run: `cd frontend && node --test tests/birth-time-question-planner.test.ts`

Expected: FAIL because the planner module does not exist.

- [ ] **Step 6: Implement the pure planner**

```ts
export const evidenceDomains = [
  "education", "relocation", "relationship", "career", "health_pressure",
] as const;

const layerByDomain = {
  education: "d24Sign",
  relocation: "d4Sign",
  relationship: "d9Sign",
  career: "d10Sign",
  health_pressure: "d30Sign",
} as const;

export function planEvidenceQuestion(input: QuestionPlannerInput): QuestionSpec | null {
  const available = evidenceDomains.filter((domain) => !input.askedDomains.includes(domain));
  const ranked = available.map((domain) => ({
    domain,
    split: new Set(input.samples.map((sample) => sample[layerByDomain[domain]]).filter(Boolean)).size,
    coverageBonus: input.coveredDomains.includes(domain) ? 0 : 1,
  })).sort((left, right) => right.split - left.split
    || right.coverageBonus - left.coverageBonus
    || evidenceDomains.indexOf(left.domain) - evidenceDomains.indexOf(right.domain));
  const winner = ranked[0];
  return winner ? questionSpecFor(winner.domain, input.phase, input.adaptiveRound) : null;
}
```

- [ ] **Step 7: Run focused tests and verify GREEN**

Run: `.venv/bin/python -m pytest -q tests/test_active_rectification_questions.py && cd frontend && node --test tests/birth-time-question-planner.test.ts tests/birth-time-journey-adapters.test.ts`

Expected: all selected tests pass.

- [ ] **Step 8: Commit the isolated planner change**

```bash
git add scripts/active_rectification_questions.py tests/test_active_rectification_questions.py frontend/src/lib/birth-time-question-planner.ts frontend/src/lib/birth-time-journey-adapters.ts frontend/tests/birth-time-question-planner.test.ts frontend/tests/birth-time-journey-adapters.test.ts
git commit -m "feat: plan adaptive birth time evidence questions"
```

---

### Task 2: JourneyTurn, NextAction, Progress, and Permission Protocol

**Files:**
- Create: `frontend/src/lib/birth-time-journey-turn.ts`
- Modify: `frontend/src/lib/birth-time-journey-service.ts`
- Modify: `frontend/src/lib/birth-time-journey-client.ts`
- Create: `frontend/tests/birth-time-journey-turn.test.ts`
- Modify: `frontend/tests/birth-time-journey-client.test.ts`

**Interfaces:**
- Consumes: `QuestionSpec`, `CandidateResult`, and confirmed `LifeEvent[]`.
- Produces: `NextAction`, `JourneyProgress`, `JourneyPermissions`, `JourneyTurnState`, `deriveNextAction()`, and parsed response fields for later tasks.

- [ ] **Step 1: Write failing invariants tests**

```ts
test("a fresh rectification turn asks exactly one baseline evidence question", () => {
  const turn = createInitialJourneyTurn(question("career"));
  assert.equal(turn.nextAction.kind, "ask_baseline_evidence");
  assert.equal(turn.progress.confirmedEvidenceCount, 0);
  assert.equal(turn.progress.maxAdaptiveRounds, 3);
  assert.equal(turn.permissions.canConfirmCandidate, false);
});

test("the third low adaptive result becomes terminal", () => {
  const next = deriveNextAction({
    progress: { phase: "adaptive", baselineDomainCount: 3, confirmedEvidenceCount: 6, adaptiveRound: 3, maxAdaptiveRounds: 3 },
    candidateResult: lowResult,
    nextQuestion: question("health_pressure"),
  });
  assert.equal(next.kind, "present_low_result");
});
```

- [ ] **Step 2: Run and verify RED**

Run: `cd frontend && node --test tests/birth-time-journey-turn.test.ts`

Expected: FAIL because the protocol module does not exist.

- [ ] **Step 3: Implement strict Zod schemas and pure transitions**

```ts
export const nextActionSchema = z.discriminatedUnion("kind", [
  z.object({ kind: z.literal("ask_baseline_evidence"), question: questionSpecSchema }),
  z.object({ kind: z.literal("ask_adaptive_evidence"), question: questionSpecSchema }),
  z.object({ kind: z.literal("review_evidence_draft"), draftId: z.string().uuid() }),
  z.object({ kind: z.literal("score_pending"), jobId: z.string().uuid() }),
  z.object({ kind: z.literal("retry_scoring"), jobId: z.string().uuid() }),
  z.object({ kind: z.literal("present_low_result"), resultId: z.string().uuid().nullable() }),
  z.object({ kind: z.literal("present_medium_result"), resultId: z.string().uuid() }),
  z.object({ kind: z.literal("request_candidate_confirmation"), resultId: z.string().uuid() }),
  z.object({ kind: z.literal("ready"), activeTime: z.string() }),
  z.object({ kind: z.literal("paused") }),
]);
```

`deriveNextAction()` must exhaustively map: baseline incomplete → one baseline question; low and adaptive round < 3 → one adaptive question; low at round 3 → terminal low; medium → terminal medium; high → confirmation; confirmed → ready.

- [ ] **Step 4: Extend service and client response types**

Add `nextAction`, `progress`, `permissions`, `turnVersion`, and nullable `evidenceDraft` to `JourneyResponse` and its client Zod schema. Keep defaults only in the legacy-normalization path; new responses must provide all fields.

- [ ] **Step 5: Add parser rejection coverage**

```ts
test("client rejects a nonterminal turn without nextAction", () => {
  assert.throws(() => parseJourneyResponse({ ...validTurn, nextAction: undefined }));
});

test("client does not expose legacy canApply as Agent permission", () => {
  const parsed = parseJourneyResponse(highConfirmationTurn);
  assert.equal(parsed.permissions.canConfirmCandidate, true);
  assert.equal("canApply" in parsed.permissions, false);
});
```

- [ ] **Step 6: Run focused tests and verify GREEN**

Run: `cd frontend && node --test tests/birth-time-journey-turn.test.ts tests/birth-time-journey-client.test.ts`

Expected: all selected tests pass.

- [ ] **Step 7: Commit the protocol**

```bash
git add frontend/src/lib/birth-time-journey-turn.ts frontend/src/lib/birth-time-journey-service.ts frontend/src/lib/birth-time-journey-client.ts frontend/tests/birth-time-journey-turn.test.ts frontend/tests/birth-time-journey-client.test.ts
git commit -m "feat: define versioned birth time journey turns"
```

---

### Task 3: Persisted Turn Version, Drafts, and Idempotency Receipts

**Files:**
- Create: `frontend/supabase/migrations/20260718020000_agent_guided_birth_time_rectification.sql`
- Modify: `frontend/src/lib/birth-time-journey-store.ts`
- Modify: `frontend/src/lib/birth-time-journey-service.ts`
- Modify: `tests/test_birth_time_journey_contract.py`
- Modify: `frontend/tests/birth-time-journey-service.test.ts`

**Interfaces:**
- Produces: `saveTurn(value, expectedVersion, actionId)`, `StaleJourneyTurnError`, stored `turnVersion`, `turnState`, `evidenceDraft`, `processedActionIds`.
- Consumed by Tasks 4 and 5.

- [ ] **Step 1: Add failing migration contract assertions**

```python
def test_agent_guided_rectification_migration_versions_turns_and_jobs():
    sql = MIGRATION.read_text()
    assert "turn_version bigint not null default 0" in sql
    assert "turn_state jsonb not null default" in sql
    assert "evidence_draft jsonb" in sql
    assert "processed_action_ids uuid[]" in sql
    assert "birth_time_rectification_scoring_jobs" in sql
```

- [ ] **Step 2: Run and verify RED**

Run: `.venv/bin/python -m pytest -q tests/test_birth_time_journey_contract.py -k agent_guided`

Expected: FAIL because the migration does not exist.

- [ ] **Step 3: Create the additive migration**

The migration must add typed JSON checks, a bounded `processed_action_ids` array, a service-role-only scoring job table with random UUID primary key, ownership, status, expiry, and unique `(case_id, evidence_fingerprint, algorithm_version)`. Do not grant job-table access to `authenticated` or `anon`.

- [ ] **Step 4: Add a failing optimistic-concurrency service test**

```ts
test("stale turn versions cannot overwrite the current action", async () => {
  await assert.rejects(
    service.skipEvidenceQuestion("user-1", "case-1", actionId, 4),
    StaleJourneyTurnError,
  );
  assert.equal(memory.savedCase()?.turnVersion, 5);
});
```

- [ ] **Step 5: Implement atomic store writes**

Use one Supabase update constrained by `.eq("turn_version", expectedVersion)` and owner ID. Append the action ID and increment the version in the same statement. If no row is returned, reload: return the current case when `processedActionIds` already includes the action ID; otherwise throw `StaleJourneyTurnError`.

- [ ] **Step 6: Run focused tests and verify GREEN**

Run: `.venv/bin/python -m pytest -q tests/test_birth_time_journey_contract.py && cd frontend && node --test tests/birth-time-journey-service.test.ts`

Expected: migration and concurrency tests pass.

- [ ] **Step 7: Commit persistence**

```bash
git add frontend/supabase/migrations/20260718020000_agent_guided_birth_time_rectification.sql frontend/src/lib/birth-time-journey-store.ts frontend/src/lib/birth-time-journey-service.ts tests/test_birth_time_journey_contract.py frontend/tests/birth-time-journey-service.test.ts
git commit -m "feat: persist versioned rectification turns"
```

---

### Task 4: Draft Confirmation, Skip, Pause, Resume, and Automatic Service Progression

**Files:**
- Modify: `frontend/src/lib/birth-time-evidence.ts`
- Modify: `frontend/src/lib/birth-time-evidence-service.ts`
- Modify: `frontend/src/lib/birth-time-journey-service.ts`
- Modify: `frontend/src/app/api/birth-time-journey/route.ts`
- Modify: `frontend/src/lib/birth-time-journey-client.ts`
- Modify: `frontend/tests/birth-time-evidence.test.ts`
- Modify: `frontend/tests/birth-time-journey-service.test.ts`
- Modify: `frontend/tests/birth-time-journey-client.test.ts`

**Interfaces:**
- Produces: `proposeEvidenceDraft`, `confirmEvidenceDraft`, `skipEvidenceQuestion`, `pause`, `finishWithCurrentRange`, and legacy `resume` normalization.
- Calls `planEvidenceQuestion()` and Task 3 store writes.

- [ ] **Step 1: Add failing end-to-end service tests with a memory store**

```ts
test("confirmed drafts automatically advance from baseline to scoring", async () => {
  const first = await service.proposeEvidenceDraft(userId, caseId, actionId1, 0, careerDraft);
  assert.equal(first.nextAction.kind, "review_evidence_draft");
  const confirmed = await service.confirmEvidenceDraft(userId, caseId, actionId2, first.turnVersion, first.evidenceDraft!.id);
  assert.equal(confirmed.progress.confirmedEvidenceCount, 1);
  assert.equal(confirmed.nextAction.kind, "ask_baseline_evidence");
});

test("a third confirmed baseline event starts scoring without a compare action", async () => {
  const result = await confirmThirdDraft();
  assert.equal(result.nextAction.kind, "score_pending");
  assert.equal(engine.scoreEventsCalls, 0);
});

test("resume reconstructs one deterministic action for a legacy dead-end snapshot", async () => {
  const result = await service.resume(userId, legacyCaseId);
  assert.equal(result.nextAction.kind, "ask_baseline_evidence");
});
```

- [ ] **Step 2: Run and verify RED**

Run: `cd frontend && node --test --test-name-pattern="draft|third confirmed|legacy dead-end" tests/birth-time-journey-service.test.ts`

Expected: FAIL because these actions do not exist.

- [ ] **Step 3: Add a strict evidence draft schema**

Drafts carry `id`, server-selected `questionId`/`domain`, nullable precision/date, `status: "draft"`, and `needsReview`. `confirmEvidenceDraft` must parse the final draft through `lifeEventSchema`; incomplete or domain-mismatched drafts fail closed.

- [ ] **Step 4: Implement automatic transition rules**

On confirmation: append the event; if baseline minimum is not met, persist the next baseline question; if met, create `score_pending`; after a low completed score, persist the next adaptive question and increment the displayed round exactly once; at round 3 persist terminal low. Skip marks the domain/question asked, consumes adaptive round only in the adaptive phase, and plans the next question. Pause persists `paused` without changing evidence.

- [ ] **Step 5: Normalize legacy cases on resume**

Legacy questionnaire and `life_events` snapshots without turn state must derive one current `nextAction` from stored evidence/result. Resume may repair derived turn state but must not call the external scoring engine.

- [ ] **Step 6: Add authenticated structured API actions**

Add strict `confirm_evidence_draft`, `skip_evidence_question`, `pause_rectification`, and `finish_rectification` request variants. Every mutation includes `caseId`, UUID `actionId`, and non-negative `turnVersion`; confirmation additionally includes only `draftId`. The client exposes `confirmBirthTimeEvidenceDraft()`, `skipBirthTimeEvidenceQuestion()`, `pauseBirthTimeRectification()`, and `finishBirthTimeRectification()` and never submits candidate score, confidence, or permissions.

- [ ] **Step 7: Run focused tests and verify GREEN**

Run: `cd frontend && node --test tests/birth-time-evidence.test.ts tests/birth-time-question-planner.test.ts tests/birth-time-journey-turn.test.ts tests/birth-time-journey-service.test.ts tests/birth-time-journey-client.test.ts`

Expected: all focused service-flow tests pass.

- [ ] **Step 8: Commit the orchestration**

```bash
git add frontend/src/lib/birth-time-evidence.ts frontend/src/lib/birth-time-evidence-service.ts frontend/src/lib/birth-time-journey-service.ts frontend/src/app/api/birth-time-journey/route.ts frontend/src/lib/birth-time-journey-client.ts frontend/tests/birth-time-evidence.test.ts frontend/tests/birth-time-journey-service.test.ts frontend/tests/birth-time-journey-client.test.ts
git commit -m "feat: advance rectification from confirmed evidence"
```

---

### Task 5: Idempotent Score-Pending Jobs and Polling

**Files:**
- Modify: `frontend/src/lib/birth-time-journey-store.ts`
- Modify: `frontend/src/lib/birth-time-evidence-service.ts`
- Modify: `frontend/src/app/api/birth-time-journey/route.ts`
- Modify: `frontend/src/lib/birth-time-journey-client.ts`
- Modify: `frontend/tests/birth-time-journey-service.test.ts`
- Modify: `frontend/tests/birth-time-journey-client.test.ts`
- Modify: `tests/test_birth_time_journey_contract.py`

**Interfaces:**
- Produces: `createScoringJob`, `pollScoringJob`, `completeScoringJob`, `failScoringJob`, API action `poll_scoring`, and client `pollBirthTimeScoring()`.

- [ ] **Step 1: Add failing job lifecycle tests**

```ts
test("polling a pending job scores exactly once and atomically stores the next action", async () => {
  const first = await service.pollScoringJob(userId, caseId, jobId);
  const second = await service.pollScoringJob(userId, caseId, jobId);
  assert.equal(engine.scoreEventsCalls, 1);
  assert.deepEqual(second.nextAction, first.nextAction);
});

test("a failed job preserves evidence and exposes retry_scoring", async () => {
  engine.scoreEventsError = new Error("offline");
  const result = await service.pollScoringJob(userId, caseId, jobId);
  assert.equal(result.nextAction.kind, "retry_scoring");
  assert.equal(result.lifeEvents.length, 3);
});
```

- [ ] **Step 2: Run and verify RED**

Run: `cd frontend && node --test --test-name-pattern="pending job|failed job" tests/birth-time-journey-service.test.ts`

Expected: FAIL because job APIs do not exist.

- [ ] **Step 3: Implement owner-scoped job claim and completion**

Only one poll may change `pending` → `processing`. A completed job returns the stored result. A failed job may be retried with the same evidence fingerprint without duplicating evidence or consuming an adaptive round. Job expiry and ownership are checked before engine invocation.

- [ ] **Step 4: Add strict API and client contracts**

```ts
z.object({
  type: z.literal("poll_scoring"),
  caseId: z.string().uuid(),
  jobId: z.string().uuid(),
}).strict()
```

The route authenticates first and never accepts candidate score, confidence, result, or active time from this action.

- [ ] **Step 5: Run focused tests and verify GREEN**

Run: `cd frontend && node --test tests/birth-time-journey-service.test.ts tests/birth-time-journey-client.test.ts && cd .. && .venv/bin/python -m pytest -q tests/test_birth_time_journey_contract.py`

Expected: all job and API contracts pass.

- [ ] **Step 6: Commit the scoring job path**

```bash
git add frontend/src/lib/birth-time-journey-store.ts frontend/src/lib/birth-time-evidence-service.ts frontend/src/app/api/birth-time-journey/route.ts frontend/src/lib/birth-time-journey-client.ts frontend/tests/birth-time-journey-service.test.ts frontend/tests/birth-time-journey-client.test.ts tests/test_birth_time_journey_contract.py
git commit -m "feat: resume idempotent birth time scoring jobs"
```

---

### Task 6: Constrained BirthTimeGuideAgent and Unbilled Guide API

**Files:**
- Create: `frontend/src/lib/birth-time-guide-agent.ts`
- Modify: `frontend/src/mastra/index.ts`
- Create: `frontend/src/app/api/birth-time-guide/route.ts`
- Modify: `frontend/src/lib/birth-time-journey-client.ts`
- Create: `frontend/tests/birth-time-guide-agent.test.ts`
- Create: `frontend/tests/birth-time-guide-route.test.ts`

**Interfaces:**
- Produces: `getBirthTimeGuideAgent(model)`, `parseEvidenceDraftOutput()`, deterministic `fallbackQuestionCopy()`, `requestBirthTimeGuidePrompt()`, and `draftBirthTimeEvidence()`.
- Consumes only server-loaded `QuestionSpec` and current case identifiers; does not expose score/save/confirm/apply tools.

- [ ] **Step 1: Add failing pure safety tests**

```ts
test("draft parser cannot change the server-selected domain", () => {
  assert.throws(() => parseEvidenceDraftOutput(
    { domain: "relationship", precision: "month", date: "2023-04" },
    { requiredDomain: "career" },
  ));
});

test("ambiguous dates stay incomplete instead of being invented", () => {
  const draft = parseEvidenceDraftOutput(
    { domain: "career", precision: null, date: null },
    { requiredDomain: "career" },
  );
  assert.equal(draft.needsReview, true);
  assert.equal(draft.date, null);
});
```

- [ ] **Step 2: Run and verify RED**

Run: `cd frontend && node --test tests/birth-time-guide-agent.test.ts tests/birth-time-guide-route.test.ts`

Expected: FAIL because guide modules do not exist.

- [ ] **Step 3: Implement the constrained guide agent**

Agent instructions must require concise Simplified Chinese, one neutral question, no candidate-support disclosure, JSON-only drafts, no missing-date invention, and no astrology result. Register only a draft-structure tool; do not register consultation, scoring, candidate, profile, or confirmation tools.

- [ ] **Step 4: Implement the authenticated no-credit route**

Supported actions:

```ts
type GuideRequest =
  | { type: "render_question"; caseId: string }
  | { type: "draft_evidence"; caseId: string; actionId: string; turnVersion: number; message: string };
```

The route loads the owner-scoped current turn itself. `render_question` returns Agent copy or deterministic fallback. `draft_evidence` constrains extraction to the current question domain, then calls `proposeEvidenceDraft`; it never calls score/save/confirm/apply and never touches consultation credits.

- [ ] **Step 5: Add source/contract assertions for the tool boundary**

Assert that the guide route does not import `begin_consultation_credit`, `confirmBirthTimeCandidate`, `saveBirthTimeCandidate`, or the consultation Agent, and that fallback output is returned when no model is configured.

- [ ] **Step 6: Run focused tests and verify GREEN**

Run: `cd frontend && node --test tests/birth-time-guide-agent.test.ts tests/birth-time-guide-route.test.ts tests/birth-time-journey-client.test.ts`

Expected: all guide safety tests pass.

- [ ] **Step 7: Commit the Agent boundary**

```bash
git add frontend/src/lib/birth-time-guide-agent.ts frontend/src/mastra/index.ts frontend/src/app/api/birth-time-guide/route.ts frontend/src/lib/birth-time-journey-client.ts frontend/tests/birth-time-guide-agent.test.ts frontend/tests/birth-time-guide-route.test.ts
git commit -m "feat: add constrained birth time guide agent"
```

---

### Task 7: One-Question Chat UI, Draft Confirmation, and Automatic Polling

**Files:**
- Create: `frontend/src/components/birth-time-guide-turn.tsx`
- Create: `frontend/src/components/birth-time-evidence-draft-card.tsx`
- Modify: `frontend/src/components/birth-time-rectification.tsx`
- Modify: `frontend/src/components/birth-time-candidate-result.tsx`
- Modify: `frontend/src/app/page.tsx`
- Modify: `frontend/src/app/globals.css`
- Modify: `frontend/tests/birth-time-rectification-contract.test.ts`
- Create: `frontend/tests/birth-time-guide-flow.test.ts`

**Interfaces:**
- Consumes: parsed `JourneyClientResponse.nextAction`, guide prompt/draft APIs, `confirmBirthTimeEvidenceDraft`, `skipBirthTimeEvidenceQuestion`, and `pollBirthTimeScoring`.
- Produces: one-question composer, review card, progress display, score-pending state, terminal low/medium/high result actions.

- [ ] **Step 1: Add failing UI-flow contract tests**

```ts
test("guided rectification renders one question and a natural-language composer", () => {
  assert.match(turnSource, /journey\.nextAction\.kind === "ask_baseline_evidence"/);
  assert.match(turnSource, /说出大概年份也可以/);
  assert.doesNotMatch(rectificationSource, /questions\.slice\(0, 3\)/);
});

test("draft review is explicit and scoring starts from confirmation", () => {
  assert.match(draftSource, /确认并用于校正/);
  assert.match(pageSource, /confirmBirthTimeEvidenceDraft/);
  assert.doesNotMatch(turnSource, /比较候选时间/);
});

test("score_pending polls automatically and resume renders the persisted action", () => {
  assert.match(pageSource, /pollBirthTimeScoring/);
  assert.match(pageSource, /nextAction\.kind === "score_pending"/);
  assert.match(pageSource, /resumeBirthTimeJourney/);
});
```

- [ ] **Step 2: Run and verify RED**

Run: `cd frontend && node --test tests/birth-time-rectification-contract.test.ts tests/birth-time-guide-flow.test.ts`

Expected: FAIL because guided components and handlers do not exist.

- [ ] **Step 3: Implement focused Client Components**

`BirthTimeGuideTurn` owns the one-question message input and skip action. `BirthTimeEvidenceDraftCard` owns editable domain-locked date/precision fields and the explicit confirm action. Keep candidate rendering in `BirthTimeCandidateResult`; do not put server transitions back into `page.tsx`.

- [ ] **Step 4: Wire page state and automatic polling**

When `nextAction` changes to an ask action, request Agent copy with a deterministic fallback already visible. When it changes to `score_pending`, start one bounded poll loop, cancel it on unmount/case/version change, and replace the whole Journey response on completion. Network failure leaves the persisted retry action visible.

- [ ] **Step 5: Preserve legacy rendering only behind normalized responses**

Remove the fixed three-question presentation from the active path. Existing legacy questionnaire fields may remain parsed for audit/migration, but `BirthTimeRectification` renders from `nextAction` only.

- [ ] **Step 6: Add responsive styles using existing tokens**

Use the existing card, type, color, spacing, focus, and 44px target tokens. Keep Chinese phrases such as “候选时间”, “当前排盘使用时间”, “关键经历”, and “确认并用于校正” phrase-safe at 390px.

- [ ] **Step 7: Run focused tests, typecheck, and lint**

Run: `cd frontend && node --test tests/birth-time-rectification-contract.test.ts tests/birth-time-guide-flow.test.ts && npx tsc --noEmit && npm run lint -- src/components/birth-time-guide-turn.tsx src/components/birth-time-evidence-draft-card.tsx src/components/birth-time-rectification.tsx src/app/page.tsx`

Expected: tests, typecheck, and targeted lint pass.

- [ ] **Step 8: Commit the UI**

```bash
git add frontend/src/components/birth-time-guide-turn.tsx frontend/src/components/birth-time-evidence-draft-card.tsx frontend/src/components/birth-time-rectification.tsx frontend/src/components/birth-time-candidate-result.tsx frontend/src/app/page.tsx frontend/src/app/globals.css frontend/tests/birth-time-rectification-contract.test.ts frontend/tests/birth-time-guide-flow.test.ts
git commit -m "feat: guide birth time evidence one question at a time"
```

---

### Task 8: Complete Verification Suite, Real Flow QA, and Accuracy Boundary

**Files:**
- Create: `frontend/tests/birth-time-agent-flow-e2e.test.ts`
- Create: `frontend/src/lib/birth-time-journey-telemetry.ts`
- Create: `frontend/tests/birth-time-journey-telemetry.test.ts`
- Modify: `frontend/src/app/api/birth-time-journey/route.ts`
- Modify: `frontend/src/app/api/birth-time-guide/route.ts`
- Modify: `frontend/DESIGN.md`
- Modify: `docs/superpowers/specs/2026-07-18-agent-guided-birth-time-rectification-design.md` only if implementation reveals a corrected contract; otherwise leave the committed spec unchanged.

**Interfaces:**
- Consumes the complete feature.
- Produces a reusable regression test set and manual QA evidence for baseline, adaptive, low, medium, high, failure, and resume branches.

- [ ] **Step 1: Add a fake-Agent/fake-engine full-flow test**

```ts
test("agent-guided journey cannot dead-end or apply without high confirmation", async () => {
  let turn = await harness.assess(approximateAssessment);
  for (const event of baselineEvents) {
    turn = await harness.draftAndConfirm(turn, event);
    assert.ok(turn.nextAction);
  }
  turn = await harness.pollUntilSettled(turn);
  while (turn.nextAction.kind === "ask_adaptive_evidence") {
    turn = await harness.skip(turn);
    assert.ok(turn.nextAction);
  }
  assert.ok(["present_low_result", "present_medium_result", "request_candidate_confirmation"].includes(turn.nextAction.kind));
  assert.equal(harness.profile.activeBirthTime, null);
});
```

- [ ] **Step 2: Run all frontend journey tests**

Run: `cd frontend && node --test tests/birth-time-*.test.ts`

Expected: all birth-time tests pass with no skipped tests.

- [ ] **Step 3: Run Python scoring and API tests**

Run: `.venv/bin/python -m pytest -q tests/test_active_rectification_questions.py tests/test_active_rectification_events.py tests/test_active_rectification_api.py tests/test_birth_time_journey_contract.py`

Expected: all selected Python tests pass.

- [ ] **Step 4: Run full frontend verification**

Run: `cd frontend && npm test && npx tsc --noEmit && npm run lint && npm run build`

Expected: full tests, typecheck, lint, and production build pass.

- [ ] **Step 5: Run manual browser scenarios**

Verify at desktop and 390px mobile:

1. baseline question → natural-language draft → edit → confirm → next question;
2. third baseline evidence → automatic calculation → adaptive question;
3. three low adaptive rounds → terminal saved range;
4. medium result → save only, no minute application;
5. high result → explicit representative-time confirmation → active profile time;
6. refresh on ask, draft, score-pending, retry, and confirmation states;
7. Agent unavailable fallback and scoring failure retry;
8. duplicate confirm does not duplicate evidence.

- [ ] **Step 6: Run security and code review**

Confirm the guide route has no billing/candidate/apply tool, job handles are owner-scoped and unguessable, raw event prose is not sent to the scorer or analytics, and low/medium confirmation attempts return conflict responses.

- [ ] **Step 7: Add privacy-safe structured journey metrics**

```ts
export type JourneyMetric =
  | "turn_advanced"
  | "draft_corrected"
  | "journey_paused"
  | "scoring_failed"
  | "scoring_recovered"
  | "illegal_snapshot";

export function journeyMetric(name: JourneyMetric, labels: {
  phase: "baseline" | "adaptive" | "result";
  confidence?: "low" | "medium" | "high";
}) {
  console.info("[birth-time-journey]", JSON.stringify({ name, ...labels }));
}
```

Tests must prove the metric API has no field for raw message, event date, birth date, coordinates, case ID, or user ID. Route calls record state transitions and failures only.

- [ ] **Step 8: Record the accuracy boundary in `frontend/DESIGN.md`**

Document that the Agent controls wording only; confidence is a versioned internal deterministic gate and remains below external-oracle/real-case proof.

- [ ] **Step 9: Commit the verification set**

```bash
git add frontend/tests/birth-time-agent-flow-e2e.test.ts frontend/src/lib/birth-time-journey-telemetry.ts frontend/tests/birth-time-journey-telemetry.test.ts frontend/src/app/api/birth-time-journey/route.ts frontend/src/app/api/birth-time-guide/route.ts frontend/DESIGN.md
git commit -m "test: verify agent guided birth time journey"
```

## Execution Order and Subagent Ownership

1. Tasks 1 and 2 may run in parallel because they own separate new modules; coordinate the shared adapter/service type before merging.
2. Task 3 follows Task 2.
3. Task 4 follows Tasks 1–3.
4. Task 5 follows Task 4.
5. Task 6 may start after Task 2 but must integrate only after Task 4.
6. Task 7 follows Tasks 4–6.
7. Task 8 runs only after all implementation tasks pass their focused tests.

Each executor must state owned files, preserve other agents’ edits, capture RED and GREEN output, and hand back changed-file and test evidence. A separate reviewer checks spec compliance and code quality before the next dependent task begins.
