# Dynamic-Choice Birth-Time Rectification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the fixed five-domain, fixed-round, text-draft birth-time flow with a model-generated one-question-at-a-time choice flow whose candidate scoring, stopping decisions, persistence, and application permissions remain deterministic and server-owned.

**Architecture:** The Python Jyotish engine computes minute candidates, date-window opportunities, candidate partitions, information gain, and versioned scores. A constrained Mastra Agent may select one server-issued opportunity and write neutral Simplified Chinese question/option labels, while a TypeScript validator binds those labels to server-issued partition IDs. `BirthTimeJourney` persists the complete internal question, accepts only `questionId + optionId` from the client, drives scoring and stop policy, and makes terminal states irreversible within the same case.

**Tech Stack:** Python 3.11+, TypeScript 5, Zod 3, Next.js 16.2 Route Handlers, React 19, Mastra 1.50, Supabase/PostgreSQL, Node test runner, pytest, Playwright visual QA.

## Global Constraints

- Preserve the dirty worktree. Never reset, restore, overwrite, or stage unrelated user changes.
- New assessments use protocol `dynamic-choice-v2`; existing fixed-question fields remain read-only legacy audit data.
- The UI never displays a fixed total question count or an adaptive round number.
- The deterministic engine may use a finite registry of scoreable experience dimensions, but v2 has no “ask every domain” checklist: opportunity gain may skip a dimension, revisit a different partition in one dimension, or stop before any nominal coverage target.
- Each generated question has 2–4 primary choices plus server-added `不确定 / 不记得` and `都不符合` choices.
- A primary choice submits immediately; it never creates a date draft, precision selector, or second confirmation screen.
- `都不符合` may collect at most 240 characters of optional context. That text is never scored directly.
- The model cannot create candidate minutes, partitions, weights, scores, confidence, progress, permissions, or application commands.
- The browser submits only `caseId`, `actionId`, `turnVersion`, `questionId`, and `optionId`; it never receives or submits a `partitionId`.
- Stop on high confidence, no useful opportunity, two consecutive effective plateaus, repeated question/partition fingerprints, explicit user finish, unrecoverable generation fallback, or 10 effective answers.
- `present_low_result`, `present_medium_result`, and `ready` are terminal for their existing `caseId`; resume cannot generate another question.
- Low and medium confidence can save a candidate range only. Only an explicitly confirmed high-confidence candidate may update `active_birth_time`.
- `reported_birth_time` is immutable.
- Keep all scoring thresholds in a versioned deterministic module; prompts and client parameters cannot override them.
- Read `frontend/node_modules/next/dist/docs/01-app/01-getting-started/15-route-handlers.md` and `05-server-and-client-components.md` before changing Route Handlers or server/client component boundaries.
- Add no runtime dependency.
- Every task uses red → green TDD and ends with a focused commit containing only that task's files.

## File Responsibility Map

New focused files:

- `scripts/dynamic_rectification.py`: candidate-window opportunity generation and deterministic choice scoring.
- `frontend/src/lib/birth-time-dynamic-choice.ts`: browser-safe public question, option, and range schemas.
- `frontend/src/lib/birth-time-dynamic-choice-internal.ts`: server-only opportunities, private partition mappings, answers, evidence, and control state.
- `frontend/src/lib/birth-time-dynamic-stop-policy.ts`: pure stop/continue decision and plateau calculation.
- `frontend/src/lib/birth-time-dynamic-question-validator.ts`: bind model labels to server opportunities and add special options.
- `frontend/src/lib/birth-time-dynamic-transitions.ts`: pure v2 Journey transitions.
- `frontend/src/lib/birth-time-dynamic-actions.ts`: authenticated/idempotent v2 mutations.
- `frontend/src/lib/birth-time-dynamic-scoring-service.ts`: claim, execute, and complete v2 score jobs.
- `frontend/src/components/birth-time-choice-question.tsx`: click-first question and optional unmatched note UI.

Existing files retain these roles:

- `scripts/active_rectification_questions.py` and `active_rectification_scoring.py`: legacy fixed-question audit behavior only.
- `frontend/src/lib/birth-time-guide-agent.ts`: constrained question-generation request/output contract.
- `frontend/src/lib/birth-time-guide-service.ts`: generate and persist a v2 question; it does not score.
- `frontend/src/lib/birth-time-journey-service.ts`: protocol routing and public journey response orchestration.
- `frontend/src/lib/birth-time-journey-turn-protocol.ts`: public `NextAction` and progress protocol.
- `frontend/src/lib/birth-time-journey-turn-persistence.ts`: load public case state plus service-role-only v2 private state and save both atomically through RPCs.
- `frontend/src/hooks/use-birth-time-guided-journey.ts`: browser coordination only; no scoring or stop decisions.

---

### Task 1: Dynamic Choice Contracts and Stop Policy

**Files:**
- Create: `frontend/src/lib/birth-time-dynamic-choice.ts`
- Create: `frontend/src/lib/birth-time-dynamic-choice-internal.ts`
- Create: `frontend/src/lib/birth-time-dynamic-stop-policy.ts`
- Modify: `frontend/src/lib/birth-time-journey-turn-protocol.ts`
- Modify: `frontend/src/lib/birth-time-journey-turn.ts`
- Test: `frontend/tests/birth-time-dynamic-choice.test.ts`
- Test: `frontend/tests/birth-time-dynamic-stop-policy.test.ts`

**Interfaces:**
- Produces `CandidateDifferencePacket`, `QuestionOpportunity`, `PersistedDynamicChoiceQuestion`, `PublicDynamicChoiceQuestion`, `StoredChoiceAnswer`, and `DynamicControlState`.
- Produces `decideDynamicStop(input: DynamicStopInput): DynamicStopDecision`.
- Replaces fixed `ask_baseline_evidence` / `ask_adaptive_evidence` in v2 with `generate_dynamic_question`, `ask_dynamic_choice`, and `clarify_unmatched_answer`.

- [ ] **Step 1: Write failing schema tests**

```ts
test("public questions never expose partition ids", () => {
  const parsed = publicDynamicChoiceQuestionSchema.parse({
    questionId: "11111111-1111-4111-8111-111111111111",
    prompt: "哪一个时间段更接近这次工作变化？",
    options: [
      { optionId: "22222222-2222-4222-8222-222222222222", label: "2018—2020 年", kind: "primary" },
      { optionId: "33333333-3333-4333-8333-333333333333", label: "2021—2023 年", kind: "primary" },
      { optionId: "44444444-4444-4444-8444-444444444444", label: "不确定 / 不记得", kind: "unknown" },
      { optionId: "55555555-5555-4555-8555-555555555555", label: "都不符合", kind: "unmatched" },
    ],
  });
  assert.equal("partitionId" in parsed.options[0], false);
  assert.equal(publicDynamicChoiceQuestionSchema.safeParse({
    ...parsed,
    options: [{ ...parsed.options[0], partitionId: "private" }, ...parsed.options.slice(1)],
  }).success, false);
});

test("internal primary choices require a server partition", () => {
  assert.equal(persistedDynamicChoiceQuestionSchema.safeParse(internalQuestion).success, true);
  assert.equal(persistedDynamicChoiceQuestionSchema.safeParse({
    ...internalQuestion,
    options: internalQuestion.options.map((option) => option.kind === "primary"
      ? { optionId: option.optionId, label: option.label, kind: option.kind, partitionId: null }
      : option),
  }).success, false);
});
```

- [ ] **Step 2: Run the contracts test and verify RED**

Run: `cd frontend && node --test tests/birth-time-dynamic-choice.test.ts`

Expected: FAIL with `ERR_MODULE_NOT_FOUND` for `birth-time-dynamic-choice.ts`.

- [ ] **Step 3: Add strict public/internal schemas**

Add the browser-safe shapes to `birth-time-dynamic-choice.ts` and the partition-bearing shapes to `birth-time-dynamic-choice-internal.ts`. Do not add a `server-only` package dependency: this repository does not currently install that marker and the plan forbids new runtime dependencies. Enforce the boundary with strict public projection plus a source-contract test proving no component, hook, client transport, or public response schema imports `birth-time-dynamic-choice-internal.ts`.

```ts
export type PublicChoiceKind = "primary" | "unknown" | "unmatched";

export type TimeRange = { readonly startTime: string; readonly endTime: string };

export type PublicDynamicChoiceQuestion = {
  readonly questionId: string;
  readonly prompt: string;
  readonly options: readonly {
    readonly optionId: string;
    readonly label: string;
    readonly kind: PublicChoiceKind;
  }[];
};
```

Use these exact server-only shapes:

```ts
import type { CandidateResult } from "./birth-time-evidence.ts";
import type { PublicChoiceKind, PublicDynamicChoiceQuestion, TimeRange } from "./birth-time-dynamic-choice.ts";

export type EvidencePartition = {
  readonly partitionId: string;
  readonly descriptor: string;
  readonly fallbackLabel: string;
};

export type ScoredEvidencePartition = EvidencePartition & {
  readonly candidateScores: Readonly<Record<string, number>>;
};

export type QuestionOpportunity = {
  readonly opportunityId: string;
  readonly dimensionCode: string;
  readonly neutralContext: string;
  readonly estimatedInformationGain: number;
  readonly candidatePartitionFingerprint: string;
  readonly fallbackPrompt: string;
  readonly partitions: readonly EvidencePartition[];
};

export type CandidateDifferencePacket = {
  readonly caseId: string;
  readonly scoringVersion: "birth-time-choice-scoring-v2";
  readonly currentRange: TimeRange;
  readonly opportunities: readonly QuestionOpportunity[];
  readonly askedQuestionFingerprints: readonly string[];
  readonly candidatePartitionFingerprints: readonly string[];
  readonly recentRangeHistory: readonly TimeRange[];
};

export type CandidateDifferenceBuild = {
  readonly packet: CandidateDifferencePacket;
  readonly candidateModel: Readonly<Record<string, unknown>>;
  readonly scoringPartitions: Readonly<Record<string, readonly ScoredEvidencePartition[]>>;
};

export type PersistedDynamicChoiceQuestion = PublicDynamicChoiceQuestion & {
  readonly opportunityId: string;
  readonly dimensionCode: string;
  readonly estimatedInformationGain: number;
  readonly scoringVersion: string;
  readonly source: "agent" | "fallback";
  readonly questionFingerprint: string;
  readonly candidatePartitionFingerprint: string;
  readonly options: readonly {
    readonly optionId: string;
    readonly label: string;
    readonly kind: PublicChoiceKind;
    readonly partitionId: string | null;
    readonly candidateScores: Readonly<Record<string, number>> | null;
  }[];
};

export type StoredChoiceAnswer = {
  readonly questionId: string;
  readonly optionId: string;
  readonly kind: PublicChoiceKind;
  readonly opportunityId: string;
  readonly answeredAt: string;
};

export type ServerChoiceEvidence = {
  readonly questionId: string;
  readonly opportunityId: string;
  readonly partitionId: string;
  readonly dimensionCode: string;
  readonly candidateScores: Readonly<Record<string, number>>;
  readonly informationGain: number;
};

export type DynamicChoiceScoringResult = {
  readonly candidate: CandidateResult;
  readonly evidenceMode: "dynamic_choice";
  readonly effectiveAnswerCount: number;
  readonly dimensionCount: number;
};

export type PausedDynamicAction =
  | { readonly kind: "generate_dynamic_question" }
  | { readonly kind: "ask_dynamic_choice"; readonly questionId: string }
  | { readonly kind: "clarify_unmatched_answer"; readonly questionId: string }
  | { readonly kind: "retry_question_generation" }
  | { readonly kind: "score_pending"; readonly jobId: string }
  | { readonly kind: "retry_scoring"; readonly jobId: string };

export type DynamicControlState = {
  readonly asOfDate: string;
  readonly answeredCount: number;
  readonly effectiveAnswerCount: number;
  readonly plateauCount: number;
  readonly questionFingerprints: readonly string[];
  readonly partitionFingerprints: readonly string[];
  readonly dismissedOpportunityIds: readonly string[];
  readonly recentRanges: readonly TimeRange[];
  readonly pausedAction: PausedDynamicAction | null;
};
```

Use `.strict().readonly()` Zod objects. Enforce exactly 2–4 `primary`, exactly one `unknown`, exactly one `unmatched`, unique `optionId`, and nonempty labels up to 80 characters. Primary choices require a nonempty `partitionId` and finite `candidateScores`; both special choices require `partitionId === null` and `candidateScores === null`.

- [ ] **Step 4: Write failing stop-policy tests**

```ts
test("two effective unchanged scores stop without starting another question", () => {
  const decision = decideDynamicStop({
    result: mediumCandidate,
    effectiveAnswer: true,
    previousResult: mediumCandidate,
    priorPlateauCount: 1,
    usefulOpportunityCount: 3,
    repeatedOnly: false,
    effectiveAnswerCount: 6,
  });
  assert.deepEqual(decision, { kind: "finish", reason: "plateau", plateauCount: 2 });
});

test("unknown answers do not advance plateau or the effective safety count", () => {
  const decision = decideDynamicStop({
    result: lowCandidate,
    effectiveAnswer: false,
    previousResult: lowCandidate,
    priorPlateauCount: 1,
    usefulOpportunityCount: 2,
    repeatedOnly: false,
    effectiveAnswerCount: 4,
  });
  assert.deepEqual(decision, { kind: "continue", plateauCount: 1 });
});

test("terminal conditions are deterministic", () => {
  assert.equal(decisionFor({ result: null, forcedReason: "user_finished" }).reason, "user_finished");
  assert.equal(decisionFor({ result: null, forcedReason: "generation_unavailable" }).reason, "generation_unavailable");
  assert.equal(decisionFor({ confidence: "high" }).reason, "high_confidence");
  assert.equal(decisionFor({ usefulOpportunityCount: 0 }).reason, "no_information_gain");
  assert.equal(decisionFor({ repeatedOnly: true }).reason, "repeated_partition");
  assert.equal(decisionFor({ effectiveAnswerCount: 10 }).reason, "safety_cap");
});
```

- [ ] **Step 5: Run the stop-policy test and verify RED**

Run: `cd frontend && node --test tests/birth-time-dynamic-stop-policy.test.ts`

Expected: FAIL because `decideDynamicStop` does not exist.

- [ ] **Step 6: Implement deterministic stop ordering**

`DynamicStopInput.result` is nullable so generation can stop safely before a first score. Add `forcedReason: "user_finished" | "generation_unavailable" | null`; these explicit terminal events are checked before score-derived conditions. Use this decision order:

```ts
export function decideDynamicStop(input: DynamicStopInput): DynamicStopDecision {
  const plateauCount = input.effectiveAnswer && input.result
    ? materiallyChanged(input.previousResult, input.result) ? 0 : input.priorPlateauCount + 1
    : input.priorPlateauCount;
  if (input.forcedReason) return { kind: "finish", reason: input.forcedReason, plateauCount };
  if (input.result?.confidence === "high") return { kind: "finish", reason: "high_confidence", plateauCount };
  if (input.effectiveAnswerCount >= 10) return { kind: "finish", reason: "safety_cap", plateauCount };
  if (plateauCount >= 2) return { kind: "finish", reason: "plateau", plateauCount };
  if (input.usefulOpportunityCount === 0) return { kind: "finish", reason: "no_information_gain", plateauCount };
  if (input.repeatedOnly) return { kind: "finish", reason: "repeated_partition", plateauCount };
  return { kind: "continue", plateauCount };
}
```

`materiallyChanged()` returns true when the winning range start/end changes, the winning representative changes, or the margin changes by at least 2 percentage points.

- [ ] **Step 7: Replace the public v2 progress/action shapes**

Add these variants without deleting the legacy parser path yet:

```ts
type DynamicNextAction =
  | { readonly kind: "generate_dynamic_question" }
  | { readonly kind: "ask_dynamic_choice"; readonly question: PublicDynamicChoiceQuestion }
  | { readonly kind: "clarify_unmatched_answer"; readonly questionId: string }
  | { readonly kind: "retry_question_generation" }
  | { readonly kind: "score_pending"; readonly jobId: string }
  | { readonly kind: "retry_scoring"; readonly jobId: string }
  | { readonly kind: "present_low_result"; readonly resultId: string | null }
  | { readonly kind: "present_medium_result"; readonly resultId: string }
  | { readonly kind: "request_candidate_confirmation"; readonly resultId: string }
  | { readonly kind: "ready"; readonly activeTime: string }
  | { readonly kind: "paused" };

type DynamicJourneyProgress = {
  readonly phase: "question" | "clarification" | "scoring" | "result" | "ready" | "paused";
  readonly answeredCount: number;
  readonly effectiveAnswerCount: number;
  readonly currentRange: TimeRange;
  readonly previousRange: TimeRange | null;
  readonly plateauCount: number;
};
```

Do not expose the hidden safety count or a maximum question count in either schema.

Add `dynamicJourneyTurnStateSchema` with `journeyProtocol: z.literal("dynamic-choice-v2")`, nonnegative `turnVersion`, `dynamicNextActionSchema`, `dynamicJourneyProgressSchema`, and the existing derived permissions schema. Keep `journeyTurnStateSchema` unchanged as the legacy-guided-v1 compatibility contract. Terminal resume behavior is implemented by Task 6 transitions, but every v2 public response must parse through this explicit dynamic turn-state discriminator.

- [ ] **Step 8: Run focused tests and commit**

Run: `cd frontend && node --test tests/birth-time-dynamic-choice.test.ts tests/birth-time-dynamic-stop-policy.test.ts tests/birth-time-journey-turn.test.ts`

Expected: all selected tests pass.

```bash
git add frontend/src/lib/birth-time-dynamic-choice.ts frontend/src/lib/birth-time-dynamic-choice-internal.ts frontend/src/lib/birth-time-dynamic-stop-policy.ts frontend/src/lib/birth-time-journey-turn-protocol.ts frontend/src/lib/birth-time-journey-turn.ts frontend/tests/birth-time-dynamic-choice.test.ts frontend/tests/birth-time-dynamic-stop-policy.test.ts
git commit -m "feat: define dynamic birth time choice protocol"
```

---

### Task 2: Deterministic Candidate Opportunities and Choice Scoring

**Files:**
- Create: `scripts/dynamic_rectification.py`
- Create: `scripts/dynamic_rectification_opportunities.py`
- Modify: `scripts/jyotish_api_server.py:1280-1325,1735-1755,6766-6890,7645-7660,7770-7790`
- Test: `tests/test_dynamic_rectification.py`
- Test: `tests/test_dynamic_rectification_scoring.py`
- Modify: `tests/test_active_rectification_api.py`

**Interfaces:**
- Produces `build_difference_packet(request) -> dict` and `score_choice_evidence(request) -> dict`.
- Adds `POST /api/dynamic_rectification_opportunities` and `POST /api/dynamic_rectification_score`.
- Keeps `/api/active_rectification_questions`, `/api/active_rectification_score`, and `/api/active_rectification_events` unchanged for legacy cases.

- [ ] **Step 1: Write failing opportunity tests**

```python
def test_packet_contains_only_candidate_backed_high_gain_opportunities(monkeypatch):
    monkeypatch.setattr(dynamic_rectification, "_candidate_window_rows", fake_rows)
    packet = dynamic_rectification.build_difference_packet(base_request())
    assert packet["scoring_version"] == "birth-time-choice-scoring-v2"
    assert packet["current_range"] == {"start_time": "05:30", "end_time": "06:00"}
    assert len(packet["opportunities"]) >= 1
    for opportunity in packet["opportunities"]:
        assert opportunity["estimated_information_gain"] >= 0.15
        assert 2 <= len(opportunity["partitions"]) <= 4
        assert len({item["partition_id"] for item in opportunity["partitions"]}) == len(opportunity["partitions"])

def test_packet_excludes_used_opportunity_and_partition_fingerprints(monkeypatch):
    monkeypatch.setattr(dynamic_rectification, "_candidate_window_rows", fake_rows)
    first = dynamic_rectification.build_difference_packet(base_request())
    used = first["opportunities"][0]
    request = base_request()
    request["dismissed_opportunity_ids"] = [used["opportunity_id"]]
    request["partition_fingerprints"] = [used["candidate_partition_fingerprint"]]
    second = dynamic_rectification.build_difference_packet(request)
    assert all(item["opportunity_id"] != used["opportunity_id"] for item in second["opportunities"])
    assert all(item["candidate_partition_fingerprint"] != used["candidate_partition_fingerprint"] for item in second["opportunities"])

def test_packet_reuses_the_persisted_candidate_model(monkeypatch):
    calls = []
    monkeypatch.setattr(dynamic_rectification, "_compute_candidate_model", lambda request: calls.append(request) or fake_model())
    first = dynamic_rectification.build_difference_packet(base_request())
    second = dynamic_rectification.build_difference_packet({
        **base_request(), "candidate_model": first["candidate_model"],
    })
    assert len(calls) == 1
    assert second["candidate_model"] == first["candidate_model"]
```

- [ ] **Step 2: Run opportunity tests and verify RED**

Run: `.venv/bin/python -m pytest -q tests/test_dynamic_rectification.py -k packet`

Expected: FAIL with `ImportError: cannot import name 'dynamic_rectification'`.

- [ ] **Step 3: Generate candidate-backed date-window opportunities**

Use minute candidates from the submitted range, the existing local chart engine, D4/D9/D10/D24/D30, Vimshottari, and Narayana Dasha. For each supported experience dimension, evaluate bounded calendar windows from age 12 through the persisted `as_of_date`. Compute each candidate chart once, then reuse it across every dimension/window. Return a compact versioned `candidate_model` containing only candidate activation numbers needed for later opportunity ranking; a subsequent request must validate and reuse that model instead of recalculating charts. A candidate joins the partition for the window with its strongest domain activation; discard opportunities with fewer than two populated partitions or normalized entropy below `0.15`.

Treat an overnight range as one chronological sequence: `23:59` and `00:00` are adjacent candidates. Bind every reusable candidate model to the exact birth date, persisted `as_of_date`, start/end range, latitude, longitude, and timezone; location fields are required and never default to zero. Keep the public entrypoints/scoring in `dynamic_rectification.py` and extract candidate-model/opportunity helpers to `dynamic_rectification_opportunities.py` so production and test files stay within the repository's 250 pure-LOC limit.

The exact opportunity contract is:

```python
class EvidencePartition(TypedDict):
    partition_id: str
    descriptor: str
    fallback_label: str
    candidate_scores: dict[str, float]

class QuestionOpportunity(TypedDict):
    opportunity_id: str
    dimension_code: str
    neutral_context: str
    estimated_information_gain: float
    candidate_partition_fingerprint: str
    fallback_prompt: str
    partitions: list[EvidencePartition]
```

`candidate_scores` keys are `HH:MM` candidates inside the current range. IDs and fingerprints are SHA-256 hashes of canonical JSON containing scoring version, dimension, window boundaries, and sorted candidate memberships. Never use prose in a fingerprint.

- [ ] **Step 4: Write failing deterministic scoring tests**

```python
def test_primary_choice_changes_rankings_and_returns_a_real_range():
    result = dynamic_rectification.score_choice_evidence({
        **score_request(),
        "choice_evidence": [{
            "question_id": str(uuid4()),
            "opportunity_id": "career-window",
            "partition_id": "career-2020-2022",
            "dimension_code": "career",
            "candidate_scores": {"05:30": 0.0, "05:31": 1.0, "05:32": 1.0, "05:33": 0.0},
            "information_gain": 0.5,
        }],
    })
    assert result["effective_answer_count"] == 1
    assert result["winning_segment"] == {
        "start_time": "05:31", "end_time": "05:32", "representative_time": "05:31", "width_minutes": 2,
    }
    assert result["can_apply"] is False

def test_unknown_and_unmatched_are_never_choice_evidence():
    with pytest.raises(ValueError, match="partition evidence"):
        dynamic_rectification.score_choice_evidence({
            **score_request(),
            "choice_evidence": [{"kind": "unknown"}],
        })

def test_high_confidence_requires_versioned_hard_gates():
    result = dynamic_rectification.adjudicate_choice_rows(
        decisive_rows(), effective_answer_count=4, dimension_count=3, missing_layers=[]
    )
    assert result["confidence"] == "high"
    assert result["can_apply"] is True
    assert result["winning_segment"]["width_minutes"] <= 5
    assert result["margin_percent"] >= 20
```

- [ ] **Step 5: Run scoring tests and verify RED**

Run: `.venv/bin/python -m pytest -q tests/test_dynamic_rectification.py -k 'primary_choice or unknown or high_confidence'`

Expected: FAIL because choice scoring functions are absent.

- [ ] **Step 6: Add versioned scoring gates**

Set `ALGORITHM_VERSION = "birth-time-choice-scoring-v2"`. Sum only server-resolved primary evidence. Keep `answered_count` separate from `effective_answer_count`; the Python scorer receives only effective evidence. Return existing candidate-result compatibility fields, with `event_count = effective_answer_count`, `domain_count = dimension_count`, and an empty public `evidence` array because private choice evidence remains in the service-only table. Also return:

```python
{
    "evidence_mode": "dynamic_choice",
    "effective_answer_count": effective_answer_count,
    "dimension_count": dimension_count,
    "algorithm_version": ALGORITHM_VERSION,
}
```

High confidence requires one winning segment, at least 4 effective answers across 3 dimensions, width at most 5 minutes, margin at least 20%, and no missing mandatory layers. Medium requires one segment, at least 3 effective answers across 2 dimensions, width at most 15 minutes, and margin at least 10%. Every other result is low and `can_apply` is false.

- [ ] **Step 7: Add strict API validation and endpoints**

For opportunities accept only birth date, a persisted ISO `as_of_date`, start/end time, required location, an optional server-owned `candidate_model`, existing choice evidence summary, dismissed opportunity IDs, and fingerprint arrays. For scoring accept only birth/location/range and server-resolved `choice_evidence`. Reject candidate models whose version, bound location/range, candidate times, or numeric activation shape do not match the request; also reject candidate times outside the submitted range, duplicate question IDs, more than 10 evidence rows, non-finite scores, unsupported dimensions, and any client-style `option_id` field. Accept opaque trimmed nonempty server-issued question IDs rather than UUID-only IDs. Window generation uses `as_of_date`, never the Python process clock, so an existing case remains reproducible across days.

Both dynamic Python endpoints are server-to-server only. Require a constant-time checked bearer token from `JYOTISH_DYNAMIC_RECTIFICATION_TOKEN`, fail closed when it is absent, and remove the dynamic endpoints from any browser-runnable technique-example dispatch. The authenticated TypeScript adapter in Task 3 is the only application caller; a browser must not be able to submit `candidate_model`, `partition_id`, or `candidate_scores` directly.

- [ ] **Step 8: Run Python suites and commit**

Run: `.venv/bin/python -m pytest -q tests/test_dynamic_rectification.py tests/test_active_rectification_api.py tests/test_active_rectification_questions.py tests/test_active_rectification_events.py`

Expected: all selected tests pass.

```bash
git add scripts/dynamic_rectification.py scripts/jyotish_api_server.py tests/test_dynamic_rectification.py tests/test_active_rectification_api.py
git commit -m "feat: score dynamic birth time choices"
```

---

### Task 3: TypeScript Engine Adapter and Trust Boundary

**Files:**
- Modify: `frontend/src/lib/birth-time-journey-service.ts:1-120`
- Modify: `frontend/src/lib/birth-time-journey-engine.ts`
- Modify: `frontend/src/lib/birth-time-journey-adapters.ts`
- Create: `frontend/src/lib/birth-time-journey-dynamic-adapters.ts`
- Modify: `frontend/src/lib/birth-time-journey-engine-model.ts`
- Modify: `frontend/src/lib/birth-time-evidence.ts:86-150`
- Test: `frontend/tests/birth-time-journey-engine.test.ts`
- Test: `frontend/tests/birth-time-journey-adapters.test.ts`
- Test: `frontend/tests/birth-time-journey-dynamic-adapters.test.ts`
- Test support: `frontend/tests/birth-time-journey-memory-store.ts`

**Interfaces:**
- Adds `buildDifferencePacket(input: DifferencePacketInput): Promise<CandidateDifferenceBuild>`.
- Adds `scoreChoices(input: DynamicChoiceScoreInput): Promise<DynamicChoiceScoringResult>`.
- Preserves `scan`, `score`, and `scoreEvents` for legacy protocol cases.

- [ ] **Step 1: Write failing adapter tests**

```ts
test("difference packets keep candidate scores on the server-only internal shape", () => {
  const build = parseCandidateDifferenceBuild(apiPacket);
  assert.equal(build.scoringPartitions["career-window"][0].candidateScores["05:31"], 1);
  assert.equal(build.packet.opportunities[0].estimatedInformationGain, 0.5);
  assert.deepEqual(build.candidateModel, apiPacket.candidate_model);
});

test("choice score parser rejects model-controlled confidence fields", () => {
  assert.throws(() => parseDynamicChoiceScoring({
    ...apiScore,
    confidence: "high",
    effective_answer_count: 1,
    can_apply: true,
  }));
});

test("choice scores adapt into the existing guarded candidate shape", () => {
  const parsed = parseDynamicChoiceScoring(apiScore);
  assert.equal(parsed.candidate.eventCount, parsed.effectiveAnswerCount);
  assert.equal(parsed.candidate.domainCount, parsed.dimensionCount);
  assert.deepEqual(parsed.candidate.evidence, []);
  assert.equal(parsed.candidate.algorithmVersion, "birth-time-choice-scoring-v2");
});
```

- [ ] **Step 2: Run and verify RED**

Run: `cd frontend && node --test tests/birth-time-journey-engine.test.ts tests/birth-time-journey-adapters.test.ts`

Expected: FAIL because both parsers and engine methods are missing.

- [ ] **Step 3: Add exact engine inputs**

```ts
export type DifferencePacketInput = {
  readonly caseId: string;
  readonly asOfDate: string;
  readonly birthDate: string;
  readonly startTime: string;
  readonly endTime: string;
  readonly lat: number;
  readonly lon: number;
  readonly tz: number;
  readonly evidence: readonly ServerChoiceEvidence[];
  readonly dismissedOpportunityIds: readonly string[];
  readonly questionFingerprints: readonly string[];
  readonly partitionFingerprints: readonly string[];
  readonly recentRanges: readonly TimeRange[];
  readonly candidateModel: Readonly<Record<string, unknown>> | null;
};

export type DynamicChoiceScoreInput = Pick<DifferencePacketInput,
  "birthDate" | "startTime" | "endTime" | "lat" | "lon" | "tz" | "evidence"
>;
```

Extend `BirthTimeJourneyEngine` with the two methods. Do not add partition data to any client response schema.

Keep the primary `BirthTimeJourneyEngine` contract fully capable: both dynamic methods are required. Use an explicit legacy-only `Pick`/interface for old services and test doubles that intentionally need only `scan`, `score`, and `scoreEvents`; do not weaken the primary methods to optional.

Raise the compatibility `candidateResultSchema.eventCount` maximum from 6 to 10 and change its high-gate message from “events” to “effective evidence items.” The dated-event request schema remains capped at 6, so legacy API behavior does not broaden; the shared candidate result can now represent the v2 safety cap.

- [ ] **Step 4: Post to the new Python endpoints**

`buildDifferencePacket()` posts snake-case payloads to `/api/dynamic_rectification_opportunities` and separates the response into `{ packet, candidateModel, scoringPartitions }`. Only `packet` may enter the Agent prompt; `candidateModel` and `scoringPartitions` stay server-only. `bindDynamicQuestion()` copies the selected partition's score vector into the private persisted question, and the model cannot supply or alter that vector. `scoreChoices()` posts to `/api/dynamic_rectification_score`. Both use the existing 45-second abort timeout and strict adapter parsing.

For both dynamic calls, require `JYOTISH_DYNAMIC_RECTIFICATION_TOKEN` in the server environment and send it as a bearer token. Never expose that token through a client module or response. Legacy engine calls remain unchanged and unauthenticated.

`parseDynamicChoiceScoring()` must require `event_count === effective_answer_count`, `domain_count === dimension_count`, `evidence_mode === "dynamic_choice"`, an empty public evidence array, and the v2 algorithm version before constructing `DynamicChoiceScoringResult`. This prevents a malformed engine payload from satisfying the high-confidence gate with inconsistent counts.

Place all v2 response schemas and mappings in `birth-time-journey-dynamic-adapters.ts`; keep legacy parsing behavior byte-compatible in `birth-time-journey-adapters.ts`. Every nested dynamic object, including `winning_segment`, is strict. Keep each production and test module within 250 pure LOC, add duplicate opportunity/partition attack tests, and assert mapped fields against independent input fixtures rather than against each other.

Test authentication through an executable fake fetch/wire seam for both dynamic endpoints: exact URL, bearer header, request body, timeout signal, and missing-token fail-before-fetch. Also prove legacy calls omit the dynamic Authorization header. The HTTP helper accepts one typed request/options object rather than four primitive parameters.

Wire assertions use independent literal request expectations, not the production serializer as the expected value. Inject the timeout-signal factory in tests and assert it receives the literal `45_000`; do not infer the timeout from a sibling exported constant. If a pre-existing test-support module exceeds the limit, extract the memory journey store into `birth-time-journey-memory-store.ts` instead of compressing formatting to pass the LOC check.

- [ ] **Step 5: Verify endpoint payload ownership**

Add a source-level test asserting that `candidate_scores` appears only in server modules and never in `birth-time-journey-client.ts`, `birth-time-journey-request.ts`, or a component/hook.

- [ ] **Step 6: Run focused tests and commit**

Run: `cd frontend && node --test tests/birth-time-journey-engine.test.ts tests/birth-time-journey-adapters.test.ts`

Expected: all selected tests pass.

```bash
git add frontend/src/lib/birth-time-journey-service.ts frontend/src/lib/birth-time-journey-engine.ts frontend/src/lib/birth-time-journey-adapters.ts frontend/src/lib/birth-time-journey-engine-model.ts frontend/src/lib/birth-time-evidence.ts frontend/tests/birth-time-journey-engine.test.ts frontend/tests/birth-time-journey-adapters.test.ts
git commit -m "feat: connect dynamic rectification engine"
```

---

### Task 4: Constrained Agent Question Generation and Fallback

**Files:**
- Create: `frontend/src/lib/birth-time-dynamic-question-validator.ts`
- Modify: `frontend/src/lib/birth-time-guide-agent.ts`
- Modify: `frontend/src/lib/birth-time-guide-service.ts`
- Modify: `frontend/src/mastra/index.ts:179-220`
- Test: `frontend/tests/birth-time-guide-agent.test.ts`
- Test: `frontend/tests/birth-time-guide-route.test.ts`

**Interfaces:**
- Produces `generateDynamicQuestionPrompt(packet, note)` and `parseDynamicQuestionOutput(value, packet)`.
- Produces `bindDynamicQuestion(output, build, ids): PersistedDynamicChoiceQuestion`; `build.packet` supplies model-safe IDs/copy and `build.scoringPartitions` supplies the private score vector.
- Model output is either `{ kind: "question", opportunityId, prompt, options }` or `{ kind: "no_useful_question" }`.

- [ ] **Step 1: Replace variant tests with failing dynamic-output tests**

```ts
test("agent output may only reference one server opportunity and its partitions", () => {
  const parsed = parseDynamicQuestionOutput({
    kind: "question",
    opportunityId: "career-window",
    prompt: "哪一个时间段更接近一次明显的工作变化？",
    options: [
      { partitionId: "window-a", label: "2018—2020 年" },
      { partitionId: "window-b", label: "2021—2023 年" },
    ],
  }, packet);
  assert.equal(parsed.kind, "question");
  assert.throws(() => parseDynamicQuestionOutput({
    ...parsed,
    options: [{ partitionId: "invented", label: "某个时间" }],
  }, packet), BirthTimeGuideOutputError);
});

test("server adds special options and keeps partitions private", () => {
  const internal = bindDynamicQuestion(validOutput, differenceBuild, deterministicIds);
  const publicQuestion = toPublicDynamicChoiceQuestion(internal);
  assert.deepEqual(publicQuestion.options.slice(-2).map((item) => item.label), ["不确定 / 不记得", "都不符合"]);
  assert.equal(publicQuestion.options.some((item) => "partitionId" in item), false);
});
```

- [ ] **Step 2: Run and verify RED**

Run: `cd frontend && node --test tests/birth-time-guide-agent.test.ts`

Expected: FAIL because dynamic generation functions do not exist.

- [ ] **Step 3: Define the model prompt boundary**

Send only opportunity ID, dimension code, neutral context, partition ID, descriptor, fallback label, prior public question summaries, and the optional unmatched note. Do not send candidate times, candidate scores, partition memberships, confidence thresholds, or support directions.

The Mastra instruction must require valid JSON only, one question, 2–4 options, neutral Simplified Chinese, no birth-minute claim, no methodology exposure, and exact server IDs. It must state that `no_useful_question` is advisory and the server makes the stop decision.

- [ ] **Step 4: Bind, fingerprint, and validate server-side**

`bindDynamicQuestion()` must:

1. verify the opportunity exists;
2. verify each partition belongs to it and appears once;
3. require 2–4 primary labels;
4. reject prompts over 120 characters and labels over 80;
5. reject time-of-birth strings matching `HH:MM`, confidence language, candidate-support language, and control claims;
6. create UUIDs server-side for question/options;
7. add the two special options with null partitions;
8. hash normalized public semantics for `questionFingerprint`;
9. reject existing question or partition fingerprints.

- [ ] **Step 5: Add one retry and deterministic fallback tests**

```ts
test("invalid model output retries once then persists the top opportunity fallback", async () => {
  const calls: string[] = [];
  const result = await serviceWithGenerator(async () => {
    calls.push("generate");
    return { text: "{}" };
  }).generateQuestion("owner-1", generationCommand);
  assert.equal(calls.length, 2);
  assert.equal(result.nextAction.kind, "ask_dynamic_choice");
  assert.equal(result.nextAction.question.prompt, packet.opportunities[0].fallbackPrompt);
  assert.equal(result.nextAction.question.options.length, packet.opportunities[0].partitions.length + 2);
});

test("no opportunity ends safely instead of regenerating the first question", async () => {
  const result = await serviceWithPacket({ ...packet, opportunities: [] })
    .generateQuestion("owner-1", generationCommand);
  assert.equal(result.nextAction.kind, "present_low_result");
});

test("model no_useful_question cannot stop while the engine has an opportunity", async () => {
  const result = await serviceWithGenerator(async () => ({
    text: JSON.stringify({ kind: "no_useful_question" }),
  })).generateQuestion("owner-1", generationCommand);
  assert.equal(result.nextAction.kind, "ask_dynamic_choice");
  assert.equal(result.nextAction.question.prompt, packet.opportunities[0].fallbackPrompt);
});
```

- [ ] **Step 6: Run focused tests and commit**

Run: `cd frontend && node --test tests/birth-time-guide-agent.test.ts tests/birth-time-guide-route.test.ts`

Expected: all selected tests pass.

```bash
git add frontend/src/lib/birth-time-dynamic-question-validator.ts frontend/src/lib/birth-time-guide-agent.ts frontend/src/lib/birth-time-guide-service.ts frontend/src/mastra/index.ts frontend/tests/birth-time-guide-agent.test.ts frontend/tests/birth-time-guide-route.test.ts
git commit -m "feat: generate constrained dynamic choice questions"
```

#### Task 4 review amendment (mandatory before Task 5)

Independent review of `437d50f..1ffc09e` blocked Task 4. Complete and independently re-review
these corrections before persistence work begins:

- Localize engine-owned `neutral_context`, `fallback_prompt`, and fallback labels with a
  deterministic Simplified-Chinese dimension map. Add a real Task 2 Python-shaped
  adapter-to-service regression proving two invalid Agent responses still persist the
  highest-gain fallback.
- Treat `unmatchedNote` as untrusted evidence: discard or redact birth-time, scoring,
  confidence, support, control, and instruction-like content before the model boundary; label
  the remaining text as untrusted quoted data. Require generated public copy to be grounded in
  the selected opportunity's localized context so valid IDs cannot authorize unrelated copy.
- Separate recoverable Agent-output/repetition failures from server binding, private scoring,
  UUID, and persisted-schema failures. Validate bindings before allocating IDs, catch only
  recoverable variants, and never translate a server fault into `present_low_result`.
- Enforce byte-exact model IDs and close the reviewed confidence/support/control wording gaps.
  Keep `bindDynamicQuestion(output, build, ids)` as the agent-facing API and use a separate
  fallback binder for server-owned source selection.
- Split the dynamic tests and shared fixtures so every changed TypeScript test module is at or
  below 250 pure lines. Add distinct-input semantic-normalization coverage and replace
  sanitized-only integration fixtures with the real engine shape.
- Correct `.superpowers/sdd/task-4-report.md` and reference durable RED/GREEN/gate artifacts.

This amendment expands Task 4 ownership to
`scripts/dynamic_rectification_opportunities.py`, its focused Python test, and focused
dynamic-question test/fixture modules. Prior public-question summaries are deferred to Task 6,
where persisted question history becomes available; Task 4 continues to enforce exact server
fingerprints without fabricating summaries from hashes.

#### Task 4 second review amendment (finite rendering contract)

The corrected range `437d50f..797cb65` is still blocked because free-form notes and model-authored
labels remain bypassable. The final Task 4 boundary is therefore:

- Raw `unmatchedNote` never crosses the Agent boundary. Task 4 omits it rather than attempting
  semantic instruction detection with keyword filters.
- Agent output is selection-only: `{ kind: "question", opportunityId }` or
  `{ kind: "no_useful_question" }`. The server renders the selected engine opportunity's
  prompt and primary labels; model-authored prompt/label copy is not accepted.
- The model dynamically chooses the next information opportunity, while the deterministic
  engine owns partitions/answer semantics and the server owns a finite public rendering
  grammar. This is the approved hybrid design, not a fixed-round questionnaire.
- `bindDynamicQuestion(selection, build, ids)` validates unique normalized server labels and
  binds them to private partitions. Duplicate/malformed server copy is a binding fault that
  propagates; it cannot be retried as model output or converted to low confidence.
- Python range labels select year/month/day precision as needed so distinct same-year windows
  remain visibly distinct. Fallback explicitly chooses maximum information gain with stable ID
  tie-breaking rather than trusting packet order.
- Required regressions cover the tea/water note bypass, inability for the model to author or
  duplicate labels, unsorted multi-opportunity fallback, valid Agent selection with correct
  private bindings, same-year unique labels, and the real Python public-copy seam. Superseded
  `CLEAR` evidence and the Task 4 report must be corrected with fresh artifact paths.

---

### Task 5: Durable v2 Persistence and Legacy Isolation

**Files:**
- Create: `frontend/supabase/migrations/20260718090000_dynamic_choice_birth_time_rectification.sql`
- Modify: `frontend/src/lib/birth-time-journey-turn-persistence.ts`
- Modify: `frontend/src/lib/birth-time-journey-store.ts`
- Modify: `frontend/src/lib/birth-time-journey-service.ts`
- Modify: `tests/test_birth_time_journey_contract.py`
- Test: `frontend/tests/birth-time-dynamic-persistence.test.ts`

**Interfaces:**
- Persists `journey_protocol` on the existing public case row.
- Persists the candidate model, internal current question, choice answers, server choice evidence, dynamic control state, and optional Agent context in `birth_time_rectification_dynamic_state`, which authenticated clients cannot select.
- Adds `saveDynamicTurn(value, expectedVersion, actionId)` and `upgradeLegacyActiveCase(value)`.
- Existing terminal cases remain terminal and are never upgraded into a question state.

- [ ] **Step 1: Write failing migration contract tests**

```python
def test_dynamic_choice_migration_keeps_private_mapping_and_agent_context_server_side():
    sql = DYNAMIC_CHOICE_MIGRATION.read_text()
    assert "journey_protocol text not null default 'legacy-guided-v1'" in sql
    assert "create table if not exists public.birth_time_rectification_dynamic_state" in sql
    assert "candidate_model jsonb" in sql
    assert "current_choice_question jsonb" in sql
    assert "choice_answers jsonb not null default '[]'::jsonb" in sql
    assert "choice_evidence jsonb not null default '[]'::jsonb" in sql
    assert "dynamic_control jsonb" in sql
    assert "agent_context jsonb not null default '[]'::jsonb" in sql
    assert "revoke all on table public.birth_time_rectification_dynamic_state from anon, authenticated" in sql
    assert "grant all on table public.birth_time_rectification_dynamic_state to service_role" in sql
    assert "save_birth_time_dynamic_turn" in sql
    assert "complete_birth_time_dynamic_scoring_job" in sql
    assert "fail_birth_time_dynamic_scoring_job" in sql
```

- [ ] **Step 2: Run and verify RED**

Run: `.venv/bin/python -m pytest -q tests/test_birth_time_journey_contract.py -k dynamic_choice`

Expected: FAIL because the migration is absent.

- [ ] **Step 3: Add a private dynamic-state table and transactional RPC**

Add only `journey_protocol` to `birth_time_rectification_cases`, allowing `legacy-guided-v1` or `dynamic-choice-v2`. Create `birth_time_rectification_dynamic_state` with `case_id` primary/foreign key, `user_id`, `candidate_model`, the other five private JSON fields, and timestamps. Add JSON type checks, cap the audit-only `choice_answers` array at 50 rows, cap effective `choice_evidence` at 10 rows, and cap Agent context at 10 notes of at most 240 characters. Enable RLS, revoke every privilege from `anon` and `authenticated`, and grant all only to `service_role`.

Create `save_birth_time_dynamic_turn(p_user_id, p_case_id, p_expected_version, p_action_id, p_public_turn_state, p_snapshot, p_candidate_result, p_private_state)`. The function must be `security definer`, set `search_path = ''`, require the matching owner and `dynamic-choice-v2`, perform the optimistic version/action-receipt update, and upsert the private row in the same database transaction. Return the new version; return the existing version for a replayed action; raise `stale_birth_time_dynamic_turn` otherwise. Revoke function execution from `public`, `anon`, and `authenticated`; grant it only to `service_role`.

Create matching service-role-only `complete_birth_time_dynamic_scoring_job(...)` and `fail_birth_time_dynamic_scoring_job(...)` RPCs. Each verifies the owner, case, job ID, expected turn version, evidence fingerprint, algorithm version, and current job state before atomically updating the job, public turn/result, and private dynamic state. A replay returns the already completed/failed turn; a mismatch raises a stale-job exception.

- [ ] **Step 4: Write failing store tests**

```ts
test("v2 load restores the exact internal question after refresh", async () => {
  const loaded = await loadStoredRectificationCase(fakeSupabase(v2CaseRow, v2PrivateRow), "owner", caseId);
  assert.deepEqual(loaded?.currentChoiceQuestion, persistedQuestion);
  assert.deepEqual(loaded?.candidateModel, persistedCandidateModel);
  assert.deepEqual(loaded?.dynamicControl.questionFingerprints, [persistedQuestion.questionFingerprint]);
});

test("save uses optimistic version and action receipt once", async () => {
  const first = await store.saveDynamicTurn(updated, 7, actionId);
  const replay = await store.saveDynamicTurn(updated, 7, actionId);
  assert.equal(first.turnVersion, 8);
  assert.equal(replay.turnVersion, 8);
  assert.equal(replay.processedActionIds.filter((value) => value === actionId).length, 1);
});
```

- [ ] **Step 5: Extend stored case parsing and persistence**

Discriminate by `journey_protocol`. `saveAssessment()` explicitly creates a `dynamic-choice-v2` case, initializes `asOfDate`, and inserts its empty private state before returning the case ID. For v2 resume, load the owner-scoped public case row and the service-role-only private row, then parse private JSON with Task 1 schemas; a missing private row is a store error, not an excuse to regenerate from scratch. `saveDynamicTurn()` calls the transactional RPC and never writes `active_birth_time`. Only `toPublicDynamicChoiceQuestion(currentChoiceQuestion)` is stored in public `turn_state` and projected into `nextAction`; candidate scores, partition IDs, and Agent notes never enter the case row.

- [ ] **Step 6: Define legacy upgrade rules**

`upgradeLegacyActiveCase()` is allowed only when the old case is nonterminal. It preserves `answers`, `life_events`, questionnaire, candidate result, reported range, and audit timestamps; sets protocol v2; initializes dynamic counters from confirmed legacy evidence; excludes legacy question fingerprints; and sets `generate_dynamic_question`. Old `present_low_result`, `present_medium_result`, confirmation, and ready states return unchanged.

- [ ] **Step 7: Run persistence tests and commit**

Run: `.venv/bin/python -m pytest -q tests/test_birth_time_journey_contract.py && cd frontend && node --test tests/birth-time-dynamic-persistence.test.ts tests/birth-time-journey-turn-persistence.test.mjs`

Expected: all selected tests pass.

```bash
git add frontend/supabase/migrations/20260718090000_dynamic_choice_birth_time_rectification.sql frontend/src/lib/birth-time-journey-turn-persistence.ts frontend/src/lib/birth-time-journey-store.ts frontend/src/lib/birth-time-journey-service.ts tests/test_birth_time_journey_contract.py frontend/tests/birth-time-dynamic-persistence.test.ts
git commit -m "feat: persist dynamic rectification turns"
```

#### Task 5 review amendment

Review expands Task 5 ownership to the following correctness and maintainability fixes before
Task 6:

- Split the migration into ordered schema/turn and scoring-job RPC migrations, each at or below
  250 pure lines. Deduplicate private-state persistence through one service-role-only SQL helper.
- Create public v2 case, required private state, and exact profile link atomically through a
  service-role `create_birth_time_dynamic_case` RPC; never use separate inserts.
- Apply protocol isolation to every legacy guided mutation and scoring-poll path, not only
  question/evidence actions.
- Add ordered protocol-guard migrations for existing legacy scoring/candidate RPCs: public
  signatures stay stable, internal bodies are not executable by API roles, and service-role
  wrappers owner-lock and verify `legacy-guided-v1` atomically. Direct legacy PostgREST writes
  include the same protocol predicate.
- Parse external rows into a strict `journeyProtocol`-discriminated stored-case union; normalize
  absent old protocol values to legacy at the loader boundary.
- Make memory replay return the stored advanced state. Map supported unknown time ranges to the
  full day while continuing to reject malformed mixed-null ranges.
- Split contract tests below 250 lines and replace deletion-only/source-mirroring claims with
  executable store behavior. If local Postgres execution is unavailable, preserve evidence of
  the environment limitation and make no live-database claim.
- Expose typed persistence wrappers for dynamic scoring completion/failure RPCs and cover exact
  payloads, replay/version results, and stale/error propagation with executable fakes. Task 6
  continues to own stop-policy and scoring orchestration.

---

### Task 6: Journey Actions, Scoring Jobs, and Anti-Loop Transitions

#### Task 6 persistence amendment

Task 5 intentionally exposed only typed dynamic scoring completion/failure wrappers. Its
legacy scoring protocol guards make the existing public create/claim RPCs unavailable to
`dynamic-choice-v2`, so Task 6 must also close the v2 job lifecycle rather than bypassing the
private-state boundary or leaving browser polling unable to complete.

- Add one ordered migration at or below 250 pure lines for
  `create_birth_time_dynamic_scoring_job(...)` and
  `claim_birth_time_dynamic_scoring_job(...)`.
- Creation owner-locks a v2 case, validates expected version/action/question/job/fingerprint/
  algorithm, atomically persists the advanced public turn, private dynamic state, canonical
  action receipt, and one pending job, and replays only the identical completed action.
- Claim owner-locks the v2 case, validates job identity, fingerprint, algorithm, current
  `score_pending`/`retry_scoring` action, and the processing lease. Completed replay is allowed
  only when the stored candidate result and dynamic terminal/continuation action agree.
- Add typed production store methods and executable fake/store tests. Do not call the
  legacy-guarded public wrappers or write the service-only private table from orchestration.
- If live PostgreSQL is unavailable, record that limitation explicitly and retain executable
  TypeScript RPC-fake evidence plus static SQL contract/syntax checks without claiming a live
  database pass.

**Files:**
- Create: `frontend/supabase/migrations/20260718094000_dynamic_choice_scoring_job_lifecycle.sql`
- Create: `frontend/src/lib/birth-time-dynamic-transitions.ts`
- Create: `frontend/src/lib/birth-time-dynamic-actions.ts`
- Create: `frontend/src/lib/birth-time-dynamic-scoring-service.ts`
- Modify: `frontend/src/lib/birth-time-journey-service.ts`
- Modify: `frontend/src/lib/birth-time-scoring-job.ts`
- Modify: `frontend/src/lib/birth-time-scoring-job-store.ts`
- Test: `frontend/tests/birth-time-dynamic-actions.test.ts`
- Test: `frontend/tests/birth-time-dynamic-scoring.test.ts`
- Test: `frontend/tests/birth-time-dynamic-terminal.test.ts`
- Test: `tests/test_birth_time_dynamic_scoring_job_contract.py`

**Interfaces:**
- Produces `answerDynamicChoice`, `submitUnmatchedContext`, `generateDynamicQuestion`, `pauseDynamic`, `resumeDynamic`, and `finishDynamic` service actions.
- Primary choices resolve a stored partition and create one idempotent `birth-time-choice-scoring-v2` job.
- Unknown and unmatched answers never create `ServerChoiceEvidence`.

- [ ] **Step 1: Write failing primary-answer tests**

```ts
test("a primary click resolves its private partition and enters score_pending", async () => {
  const result = await flow.answerDynamicChoice("owner", {
    caseId, actionId, turnVersion: 4, questionId, optionId: primaryOptionId,
  });
  assert.equal(result.nextAction.kind, "score_pending");
  assert.equal(flow.saved.choiceAnswers.length, 1);
  assert.equal(flow.saved.choiceEvidence[0].partitionId, "window-a");
  assert.equal(flow.saved.dynamicControl.effectiveAnswerCount, 1);
});

test("a forged or stale option cannot affect evidence", async () => {
  await assert.rejects(() => flow.answerDynamicChoice("owner", {
    caseId, actionId, turnVersion: 3, questionId, optionId: forgedOptionId,
  }), StaleJourneyTurnError);
  assert.deepEqual(flow.saved.choiceEvidence, []);
});
```

- [ ] **Step 2: Run action tests and verify RED**

Run: `cd frontend && node --test tests/birth-time-dynamic-actions.test.ts`

Expected: FAIL because dynamic actions do not exist.

- [ ] **Step 3: Implement special-choice transitions**

- Primary: persist answer and private evidence, increment both counts, clear current question, create score job.
- Unknown: persist a non-effective answer, increment only `answeredCount`, dismiss the opportunity/fingerprints, clear current question, enter `generate_dynamic_question`.
- Unmatched: persist a non-effective answer, increment only `answeredCount`, retain the question, enter `clarify_unmatched_answer`.
- Unmatched context: validate at most 240 characters, persist separate Agent context, dismiss the old opportunity/fingerprints, clear the question, enter `generate_dynamic_question` without scoring.
- Finish: preserve current result/range and enter a terminal low or medium result.

- [ ] **Step 4: Write failing score-completion tests**

```ts
test("score completion continues only when the stop policy allows it", async () => {
  const result = await scoring.complete(lowChangedScore, packetWithUsefulOpportunity);
  assert.equal(result.nextAction.kind, "generate_dynamic_question");
});

test("the second plateau is terminal and resume stays terminal", async () => {
  const terminal = await scoring.complete(mediumUnchangedScore, packetWithUsefulOpportunity);
  assert.equal(terminal.nextAction.kind, "present_medium_result");
  const resumed = await flow.resumeDynamic("owner", caseId);
  assert.deepEqual(resumed.nextAction, terminal.nextAction);
});

test("high confidence still requires explicit confirmation", async () => {
  const result = await scoring.complete(highScore, packetWithUsefulOpportunity);
  assert.equal(result.nextAction.kind, "request_candidate_confirmation");
  assert.equal(result.snapshot.activeTime, null);
  assert.equal(result.permissions.canConfirmCandidate, true);
});
```

- [ ] **Step 5: Run scoring tests and verify RED**

Run: `cd frontend && node --test tests/birth-time-dynamic-scoring.test.ts tests/birth-time-dynamic-terminal.test.ts`

Expected: FAIL because v2 completion and terminal guards are absent.

- [ ] **Step 6: Add scoring claim/completion flow**

Fingerprint canonical server choice evidence, not public labels or Agent notes. Claim jobs by case, evidence fingerprint, and algorithm version. Validate returned effective count, dimension count, algorithm version, candidate range, and confidence gates before persisting. Apply `decideDynamicStop()` in the same saved turn as the candidate result; never expose an intermediate low result that `resume()` could reinterpret as a new cycle.

- [ ] **Step 7: Make terminal transitions one-way**

Every answer, generation, reframe, retry, and scoring action must reject a terminal `nextAction`. `resumeDynamic()` returns the stored terminal state byte-for-byte. `pauseDynamic()` stores the exact non-paused action in `dynamicControl.pausedAction`; resume restores only that action and clears the saved pause action.

- [ ] **Step 8: Run focused tests and commit**

Run: `cd frontend && node --test tests/birth-time-dynamic-actions.test.ts tests/birth-time-dynamic-scoring.test.ts tests/birth-time-dynamic-terminal.test.ts tests/birth-time-scoring-job.test.ts`

Expected: all selected tests pass.

```bash
git add frontend/src/lib/birth-time-dynamic-transitions.ts frontend/src/lib/birth-time-dynamic-actions.ts frontend/src/lib/birth-time-dynamic-scoring-service.ts frontend/src/lib/birth-time-journey-service.ts frontend/src/lib/birth-time-scoring-job.ts frontend/src/lib/birth-time-scoring-job-store.ts frontend/tests/birth-time-dynamic-actions.test.ts frontend/tests/birth-time-dynamic-scoring.test.ts frontend/tests/birth-time-dynamic-terminal.test.ts
git commit -m "feat: orchestrate dynamic rectification turns"
```

---

### Task 7: Authenticated API, Client Commands, and Automatic Browser Coordination

**Files:**
- Modify: `frontend/src/lib/birth-time-journey-request.ts`
- Modify: `frontend/src/lib/birth-time-journey-response-schema.ts`
- Modify: `frontend/src/lib/birth-time-journey-client.ts`
- Modify: `frontend/src/app/api/birth-time-journey/route.ts`
- Modify: `frontend/src/app/api/birth-time-guide/route.ts`
- Modify: `frontend/src/hooks/use-birth-time-guided-journey.ts`
- Test: `frontend/tests/birth-time-dynamic-api.test.ts`
- Modify: `frontend/tests/birth-time-guide-client.test.ts`
- Modify: `frontend/tests/birth-time-guided-polling.test.ts`

**Interfaces:**
- Journey command: `{ type: "answer_dynamic_choice", caseId, actionId, turnVersion, questionId, optionId }`.
- Guide commands: `generate_dynamic_question` and `reframe_unmatched`.
- Controller exposes `selectOption(optionId)`, `submitUnmatchedContext(note)`, `finish()`, `pause()`, and existing candidate actions.

- [ ] **Step 1: Write failing request-boundary tests**

```ts
test("choice commands accept only public ids", () => {
  const valid = { type: "answer_dynamic_choice", caseId, actionId, turnVersion: 4, questionId, optionId };
  assert.equal(birthTimeJourneyRequestSchema.safeParse(valid).success, true);
  for (const field of ["partitionId", "candidateScores", "confidence", "time"] as const) {
    assert.equal(birthTimeJourneyRequestSchema.safeParse({ ...valid, [field]: "forged" }).success, false);
  }
});

test("unmatched context is optional, trimmed, and bounded", () => {
  assert.equal(birthTimeGuideRequestSchema.safeParse({
    type: "reframe_unmatched", caseId, actionId, turnVersion: 5, questionId, note: "  更像是 2017 年  ",
  }).success, true);
  assert.equal(birthTimeGuideRequestSchema.safeParse({
    type: "reframe_unmatched", caseId, actionId, turnVersion: 5, questionId, note: "字".repeat(241),
  }).success, false);
});
```

- [ ] **Step 2: Run API tests and verify RED**

Run: `cd frontend && node --test tests/birth-time-dynamic-api.test.ts tests/birth-time-guide-client.test.ts`

Expected: FAIL because v2 commands are absent.

- [ ] **Step 3: Add strict route dispatch**

Authenticate before body parsing. Route each v2 command to only its scoped service method. Map stale/terminal/forged actions to 409, missing cases to 404, invalid model output to the deterministic fallback path, and engine/store outages to 503 while preserving the current question. Record metrics after persisted transitions only.

- [ ] **Step 4: Add automatic generation and scoring coordination**

In the hook:

- on `generate_dynamic_question`, call the guide route once per `caseId:turnVersion` identity;
- on `score_pending`, poll the existing idempotent job identity;
- on network failure, keep the same action and show retry; do not optimistically create another question;
- on `ask_dynamic_choice`, render the persisted public question directly, without a second render-question request;
- on primary click, disable all options until the mutation resolves;
- on terminal result, stop all generation and polling effects.

- [ ] **Step 5: Add race/replay tests**

```ts
test("duplicate option clicks publish one advanced turn", async () => {
  const requests = coordinateDuplicateClicks();
  await Promise.all([requests.select(primaryOptionId), requests.select(primaryOptionId)]);
  assert.equal(requests.sent.length, 1);
  assert.equal(requests.published.at(-1)?.nextAction.kind, "score_pending");
});

test("a stale generated question cannot replace a newer turn", async () => {
  const result = await resolveGenerationAfterTurnAdvanced();
  assert.equal(result.current.turnVersion, 8);
  assert.notEqual(result.current.nextAction.kind, "ask_dynamic_choice");
});
```

- [ ] **Step 6: Run focused tests and commit**

Run: `cd frontend && node --test tests/birth-time-dynamic-api.test.ts tests/birth-time-guide-client.test.ts tests/birth-time-guided-polling.test.ts tests/birth-time-guided-review-fixes.test.ts`

Expected: all selected tests pass.

```bash
git add frontend/src/lib/birth-time-journey-request.ts frontend/src/lib/birth-time-journey-response-schema.ts frontend/src/lib/birth-time-journey-client.ts frontend/src/app/api/birth-time-journey/route.ts frontend/src/app/api/birth-time-guide/route.ts frontend/src/hooks/use-birth-time-guided-journey.ts frontend/tests/birth-time-dynamic-api.test.ts frontend/tests/birth-time-guide-client.test.ts frontend/tests/birth-time-guided-polling.test.ts
git commit -m "feat: expose dynamic rectification actions"
```

---

### Task 8: Click-First Question UI and Simplified Progress

**Files:**
- Create: `frontend/src/components/birth-time-choice-question.tsx`
- Modify: `frontend/src/components/birth-time-rectification.tsx`
- Modify: `frontend/src/components/birth-time-candidate-result.tsx`
- Modify: `frontend/src/app/globals.css:360-415,650-670`
- Modify: `frontend/src/hooks/use-birth-time-guided-journey.ts`
- Test: `frontend/tests/birth-time-choice-question.test.ts`
- Modify: `frontend/tests/birth-time-guide-flow.test.ts`
- Modify: `frontend/tests/birth-time-rectification-contract.test.ts`

**Interfaces:**
- Consumes only `PublicDynamicChoiceQuestion`, `DynamicJourneyProgress`, and controller callbacks.
- Removes v2 imports/usages of `BirthTimeGuideTurn` and `BirthTimeEvidenceDraftCard` from the active rectification path.

- [ ] **Step 1: Write failing UI contract tests**

```ts
test("the v2 question surface is click-first", () => {
  assert.match(choiceSource, /question\.options\.map/);
  assert.match(choiceSource, /onSelect\(option\.optionId\)/);
  assert.doesNotMatch(choiceSource, /整理为经历草稿|记得的精度|发生时间|第.*\/.*轮/);
  assert.doesNotMatch(choiceSource, /<textarea/);
});

test("only unmatched expands an optional note", () => {
  assert.match(choiceSource, /option\.kind === "unmatched"/);
  assert.match(choiceSource, /maxLength=\{240\}/);
  assert.match(choiceSource, /补充一句（可选）/);
  assert.doesNotMatch(choiceSource, /required/);
});
```

- [ ] **Step 2: Run UI tests and verify RED**

Run: `cd frontend && node --test tests/birth-time-choice-question.test.ts tests/birth-time-guide-flow.test.ts`

Expected: FAIL because `birth-time-choice-question.tsx` does not exist and the old textarea flow remains active.

- [ ] **Step 3: Build the accessible question card**

Render a `<fieldset>` with the question in `<legend>`. Render each primary option as a full-width button with at least 44px height. Render unknown and unmatched as secondary actions. While pending, disable every option, set `aria-busy="true"`, and show `正在缩小候选范围…`. Preserve keyboard focus and announce errors with `role="alert"`.

When unmatched is selected, render one optional textarea and two actions: `换一道题` and `提交补充并换题`. Both call the reframe action; the former sends an empty note. The text is not called evidence and the UI makes no scoring claim.

- [ ] **Step 4: Replace round progress with facts**

Show exactly:

```tsx
<div className="birth-time-question-progress">
  <b>已完成 {progress.effectiveAnswerCount} 个有效判断</b>
  <span>当前候选范围：{rangeLabel(progress.currentRange)}</span>
</div>
```

Do not show answered total, hidden safety cap, baseline domains, adaptive rounds, or a progress denominator.

- [ ] **Step 5: Make terminal copy explicit and non-looping**

Low copy: `目前没有足够的新信息继续稳定缩小范围，本次评估已结束并保存当前候选范围。`

Medium copy: `已形成较窄的候选范围，本次评估已结束；它不会自动改动当前排盘时间。`

If a new assessment entry remains available, label it `开始新的评估` and explain `会建立新的记录，当前结果仍会保留`. Do not label a terminal action `继续校正` or silently reuse the same `caseId`.

- [ ] **Step 6: Add responsive styles**

Use existing spacing, color, border, radius, and type tokens. Primary option buttons are full width at every viewport; special actions may share a row above 720px and stack below it. Add visible `:focus-visible`, selected/pending feedback, and `prefers-reduced-motion` protection. Do not hardcode a new palette.

- [ ] **Step 7: Run focused tests and commit**

Run: `cd frontend && node --test tests/birth-time-choice-question.test.ts tests/birth-time-guide-flow.test.ts tests/birth-time-rectification-contract.test.ts`

Expected: all selected tests pass.

```bash
git add frontend/src/components/birth-time-choice-question.tsx frontend/src/components/birth-time-rectification.tsx frontend/src/components/birth-time-candidate-result.tsx frontend/src/app/globals.css frontend/src/hooks/use-birth-time-guided-journey.ts frontend/tests/birth-time-choice-question.test.ts frontend/tests/birth-time-guide-flow.test.ts frontend/tests/birth-time-rectification-contract.test.ts
git commit -m "feat: add click-first birth time questions"
```

---

### Task 9: Migration Compatibility, Telemetry, and Product Documentation

**Files:**
- Modify: `frontend/src/lib/birth-time-journey-response.ts`
- Modify: `frontend/src/lib/birth-time-journey-response-schema.ts`
- Modify: `frontend/src/lib/birth-time-journey-telemetry.ts`
- Modify: `frontend/src/lib/birth-time-guided-preview.ts`
- Modify: `frontend/tests/birth-time-journey-resume.test.ts`
- Modify: `frontend/tests/birth-time-journey-legacy-isolation.test.ts`
- Modify: `frontend/tests/birth-time-journey-telemetry.test.ts`
- Modify: `frontend/tests/birth-time-rectification-contract.test.ts`
- Modify: `frontend/DESIGN.md`
- Modify: `docs/superpowers/specs/2026-07-18-agent-guided-birth-time-rectification-design.md`

**Interfaces:**
- Legacy response parser remains compatible, but active v2 responses must satisfy strict dynamic invariants.
- Telemetry records counts/reasons only and never records free text, partition membership, candidate scores, or birth data.

- [ ] **Step 1: Write failing migration/resume tests**

```ts
test("an active legacy case upgrades once and keeps confirmed evidence", async () => {
  const upgraded = await service.resume(owner, activeLegacyCase.id);
  assert.equal(upgraded.nextAction.kind, "generate_dynamic_question");
  assert.deepEqual(upgraded.lifeEvents, activeLegacyCase.lifeEvents);
  assert.deepEqual(upgraded.answers, activeLegacyCase.answers);
});

test("legacy terminal cases do not restart", async () => {
  for (const stored of [legacyLow, legacyMedium, legacyReady]) {
    const resumed = await service.resume(owner, stored.id);
    assert.notEqual(resumed.nextAction.kind, "generate_dynamic_question");
    assert.notEqual(resumed.nextAction.kind, "ask_dynamic_choice");
  }
});
```

- [ ] **Step 2: Run migration tests and verify RED**

Run: `cd frontend && node --test tests/birth-time-journey-resume.test.ts tests/birth-time-journey-legacy-isolation.test.ts`

Expected: FAIL because resume still projects fixed baseline/adaptive turns.

- [ ] **Step 3: Add protocol-aware projection and invariants**

Only `legacy-guided-v1` uses fixed `QuestionSpec`, `adaptiveRound`, and evidence drafts. Only `dynamic-choice-v2` accepts dynamic actions/progress. Strict response parsing rejects:

- a public option containing `partitionId`;
- a terminal case with a question action;
- a question state without the persisted public question;
- a high confirmation whose result/time does not match;
- low/medium `canConfirmCandidate` permission;
- fixed round fields in a v2 progress object.

- [ ] **Step 4: Add privacy-safe telemetry**

Record event names `dynamic_question_presented`, `dynamic_choice_answered`, `dynamic_question_unmatched`, `dynamic_score_completed`, and `dynamic_journey_stopped`. Allowed properties are protocol version, source (`agent` or `fallback`), answered/effective counts, confidence, stop reason, range width, and latency bucket. Tests must reject/narrow objects containing note, prompt, label, partition ID, candidate scores, birth date/time, or user ID.

- [ ] **Step 5: Update preview fixtures and documentation**

Add preview fixtures for question, unmatched clarification, scoring, low terminal, medium terminal, and high confirmation. Update `frontend/DESIGN.md` with the public command/response contract, the private partition boundary, and the one-way terminal invariant. Mark legacy fixed-question and date-draft components as compatibility-only, not the active product flow.

- [ ] **Step 6: Run focused tests and commit**

Run: `cd frontend && node --test tests/birth-time-journey-resume.test.ts tests/birth-time-journey-legacy-isolation.test.ts tests/birth-time-journey-telemetry.test.ts tests/birth-time-rectification-contract.test.ts`

Expected: all selected tests pass.

```bash
git add frontend/src/lib/birth-time-journey-response.ts frontend/src/lib/birth-time-journey-response-schema.ts frontend/src/lib/birth-time-journey-telemetry.ts frontend/src/lib/birth-time-guided-preview.ts frontend/tests/birth-time-journey-resume.test.ts frontend/tests/birth-time-journey-legacy-isolation.test.ts frontend/tests/birth-time-journey-telemetry.test.ts frontend/tests/birth-time-rectification-contract.test.ts frontend/DESIGN.md docs/superpowers/specs/2026-07-18-agent-guided-birth-time-rectification-design.md
git commit -m "docs: define dynamic rectification lifecycle"
```

---

### Task 10: End-to-End, Regression, and Visual QA

**Files:**
- Create: `frontend/tests/birth-time-dynamic-flow-e2e.test.ts`
- Modify: `frontend/tests/birth-time-agent-flow-e2e.test.ts`
- Modify: `tests/test_frontend_productization.py`
- Test only: all files changed in Tasks 1–9

**Interfaces:**
- Verifies the complete authenticated v2 journey and the unchanged guarded candidate-confirmation transaction.
- Produces visual evidence for desktop, narrow mobile, keyboard focus, unmatched expansion, loading, and terminal result states.

- [ ] **Step 1: Add the complete v2 flow test**

```ts
test("dynamic choices narrow, stop, and never loop", async () => {
  let turn = await flow.assess();
  assert.equal(turn.nextAction.kind, "generate_dynamic_question");
  turn = await flow.generate(turn);
  assert.equal(turn.nextAction.kind, "ask_dynamic_choice");
  turn = await flow.choose(turn, primaryOption(turn));
  assert.equal(turn.nextAction.kind, "score_pending");
  turn = await flow.completeScore(turn, lowChangedScore);
  assert.equal(turn.nextAction.kind, "generate_dynamic_question");
  turn = await flow.generate(turn);
  turn = await flow.choose(turn, primaryOption(turn));
  turn = await flow.completeScore(turn, secondPlateauScore);
  assert.equal(turn.nextAction.kind, "present_low_result");
  const resumed = await flow.resume(turn.caseId);
  assert.deepEqual(resumed.nextAction, turn.nextAction);
});
```

- [ ] **Step 2: Add the unmatched and failure flows**

Cover unknown → different fingerprint, unmatched → optional note → new clickable question, invalid model output → one retry → fallback, model unavailable with no fallback → terminal, duplicate click replay, stale click rejection, score failure/retry with no duplicate evidence, pause/resume exact action restoration, explicit finish, and terminal resume.

- [ ] **Step 3: Run all focused birth-time tests**

Run: `.venv/bin/python -m pytest -q tests/test_dynamic_rectification.py tests/test_active_rectification_api.py tests/test_active_rectification_questions.py tests/test_active_rectification_events.py tests/test_birth_time_journey_contract.py tests/test_frontend_productization.py`

Expected: all selected Python tests pass.

Run: `cd frontend && node --test tests/birth-time-*.test.ts`

Expected: all birth-time TypeScript tests pass.

- [ ] **Step 4: Run static verification**

Run: `cd frontend && npm run lint`

Expected: exit 0 with no new warnings in changed files.

Run: `cd frontend && npm run build`

Expected: production build completes successfully.

Run: `git diff --check`

Expected: no whitespace errors.

- [ ] **Step 5: Run manual visual QA**

Start the app with `cd frontend && npm run dev`. Use Playwright against the local authenticated/preview path and capture:

1. desktop dynamic question at 1440×1000;
2. mobile dynamic question at 390×844;
3. unmatched note expanded on mobile;
4. pending/scoring state with disabled buttons;
5. low terminal result after resume;
6. high candidate confirmation showing that the active time is still unchanged.

Verify no horizontal scroll, every target is at least 44px, keyboard Tab/Enter completes the choice, visible focus is present, screen-reader labels are meaningful, no fixed-round copy appears, and no date form/draft confirmation appears.

- [ ] **Step 6: Final diff audit**

Run: `git status --short && git diff --stat && git diff --check`

Expected: only intended implementation/documentation files are staged for the final task; unrelated dirty files remain untouched and unstaged.

- [ ] **Step 7: Commit final verification artifacts**

```bash
git add frontend/tests/birth-time-dynamic-flow-e2e.test.ts frontend/tests/birth-time-agent-flow-e2e.test.ts tests/test_frontend_productization.py
git commit -m "test: verify dynamic birth time rectification"
```

## Final Acceptance Checklist

- [ ] A normal user can complete each question by clicking once.
- [ ] No normal path asks for prose, a date precision, a date, or a second confirmation of the same answer.
- [ ] Agent-generated labels cannot alter private partitions or deterministic scoring.
- [ ] Unknown/unmatched answers do not become scoring evidence.
- [ ] Every next question reflects the latest stored candidate score and excludes used fingerprints.
- [ ] No fixed five-question or three-round exit rule remains in v2.
- [ ] Plateau, no-gain, repetition, safety cap, explicit finish, and high confidence all stop deterministically.
- [ ] Terminal cases remain terminal after refresh, resume, retries, and duplicate requests.
- [ ] Low/medium results cannot update the active chart time.
- [ ] High results update the active chart time only after explicit matching confirmation.
- [ ] Existing terminal cases and confirmed legacy evidence are preserved.
- [ ] Free text, candidate memberships, partition IDs, and candidate scores are absent from browser payloads and telemetry.
