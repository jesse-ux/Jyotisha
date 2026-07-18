import assert from "node:assert/strict";
import test from "node:test";
import {
  createInitialJourneyTurn,
  deriveNextAction,
  projectJourneyTurn,
} from "../src/lib/birth-time-journey-turn.ts";
import type { CandidateResult } from "../src/lib/birth-time-evidence.ts";
import type { QuestionSpec } from "../src/lib/birth-time-question-planner.ts";

function question(domain: QuestionSpec["domain"]): QuestionSpec {
  return {
    questionId: `baseline_${domain}_1`,
    phase: "baseline",
    domain,
    requestedPrecision: ["year", "month"],
    allowUnknown: true,
    purposeCode: `candidate_difference_${domain}`,
    plannerVersion: "candidate-difference-v1",
  };
}

const lowResult: CandidateResult = {
  resultId: "1d8ee348-61a3-433d-8907-ff6d281b9992",
  confidence: "low",
  canApply: false,
  winningSegment: null,
  eventCount: 3,
  domainCount: 3,
  topScore: 8,
  secondScore: 7,
  marginPercent: 12.5,
  reasons: ["Candidate scores remain close."],
  evidence: [],
  algorithmVersion: "birth-time-event-scoring-v1",
};

test("a fresh rectification turn asks exactly one baseline evidence question", () => {
  const turn = createInitialJourneyTurn(question("career"));

  assert.equal(turn.nextAction.kind, "ask_baseline_evidence");
  assert.equal(turn.progress.confirmedEvidenceCount, 0);
  assert.equal(turn.progress.maxAdaptiveRounds, 3);
  assert.equal(turn.permissions.canConfirmCandidate, false);
});

test("the third low adaptive result becomes terminal", () => {
  const next = deriveNextAction({
    progress: {
      phase: "adaptive",
      baselineDomainCount: 3,
      confirmedEvidenceCount: 6,
      adaptiveRound: 3,
      maxAdaptiveRounds: 3,
    },
    candidateResult: lowResult,
    nextQuestion: question("health_pressure"),
    confirmedTime: null,
  });

  assert.equal(next.kind, "present_low_result");
});

test("projection skips confirmed evidence domains when planning the next baseline question", () => {
  const careerEvents = [
    { id: "5cb071d6-6d99-46be-85dc-a9bf59ef6ac5", domain: "career", date: "2011", precision: "year" },
    { id: "0790866c-ad5e-4a45-b2b4-a5c73f6be6ea", domain: "career", date: "2019", precision: "year" },
    { id: "0ef52e51-ab5f-453b-81e5-adb44a929224", domain: "career", date: "2021", precision: "year" },
  ] as const;
  const turn = projectJourneyTurn({
    turnVersion: 0,
    snapshot: {
      state: "rectifying", assistantIntent: "continue_rectification_questions", input: "rectification_questions",
      route: "rectification", confidence: null, canApply: false, activeTime: null,
      reportedRange: { label: "14:00—15:00", startTime: "14:00", endTime: "15:00" },
    },
    questionnaire: { samples: [
      { d4Sign: "Aries", d9Sign: "Aries", d10Sign: "Aries", d24Sign: "Aries", d30Sign: "Aries" },
      { d4Sign: "Aries", d9Sign: "Aries", d10Sign: "Taurus", d24Sign: "Aries", d30Sign: "Aries" },
      { d4Sign: "Aries", d9Sign: "Aries", d10Sign: "Gemini", d24Sign: "Aries", d30Sign: "Aries" },
    ] },
    persistedProgress: { adaptiveRound: 0, askedDomains: [] },
    candidateResult: null,
    lifeEvents: careerEvents,
  });

  assert.equal(turn.nextAction.kind, "ask_baseline_evidence");
  assert.equal(turn.nextAction.question.domain, "education");
});

test("a low result becomes terminal when adaptive question planning is exhausted early", () => {
  const next = deriveNextAction({
    progress: {
      phase: "adaptive", baselineDomainCount: 3, confirmedEvidenceCount: 6, adaptiveRound: 1, maxAdaptiveRounds: 3,
    },
    candidateResult: lowResult,
    nextQuestion: null,
  });

  assert.deepEqual(next, { kind: "present_low_result", resultId: lowResult.resultId });
});

test("projection pauses completed legacy evidence without fabricating a draft", () => {
  const turn = projectJourneyTurn({
    turnVersion: 0,
    snapshot: {
      state: "rectifying", assistantIntent: "continue_rectification_questions", input: "rectification_questions",
      route: "rectification", confidence: null, canApply: false, activeTime: null,
      reportedRange: { label: "14:00—15:00", startTime: "14:00", endTime: "15:00" },
    },
    questionnaire: { samples: [] },
    candidateResult: null,
    lifeEvents: [
      { id: "5cb071d6-6d99-46be-85dc-a9bf59ef6ac5", domain: "education", date: "2011", precision: "year" },
      { id: "0790866c-ad5e-4a45-b2b4-a5c73f6be6ea", domain: "career", date: "2019", precision: "year" },
      { id: "0ef52e51-ab5f-453b-81e5-adb44a929224", domain: "relationship", date: "2021", precision: "year" },
    ],
  });

  assert.equal(turn.nextAction.kind, "paused");
  assert.equal(turn.evidenceDraft, null);
});
