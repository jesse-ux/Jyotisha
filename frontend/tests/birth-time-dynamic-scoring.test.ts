import assert from "node:assert/strict";
import test from "node:test";
import {
  completeDynamicScoreTransition,
} from "../src/lib/birth-time-dynamic-transitions.ts";
import type { CandidateResult } from "../src/lib/birth-time-evidence.ts";
import type { ServerChoiceEvidence } from "../src/lib/birth-time-dynamic-choice-internal.ts";
import { createBirthTimeJourneyService } from "../src/lib/birth-time-journey-service.ts";
import {
  dynamicCase,
  ownerId,
  persistedQuestion,
} from "./birth-time-dynamic-persistence-fixture.ts";
import { memoryStore } from "./birth-time-journey-memory-store.ts";
import { dynamicJobStore } from "./birth-time-dynamic-job-memory-store.ts";

const lowCandidate: CandidateResult = {
  resultId: "11111111-1111-4111-8111-111111111111",
  confidence: "low",
  canApply: false,
  winningSegment: null,
  eventCount: 1,
  domainCount: 1,
  topScore: 10,
  secondScore: 9,
  marginPercent: 10,
  reasons: ["close"],
  evidence: [],
  algorithmVersion: "birth-time-choice-scoring-v2",
};

const actionId = "ab2d936b-5ce7-45d8-a0fb-33f48f960f36";

function freshDynamicCase(
  candidateResult: CandidateResult | null = null,
  priorEvidence: readonly ServerChoiceEvidence[] = [],
) {
  const stored = dynamicCase();
  const effectiveAnswerCount = priorEvidence.length;
  return {
    ...stored,
    eventContext: {
      birthDate: "1993-04-17",
      lat: 31.23,
      lon: 121.47,
      tz: 8,
    },
    candidateResult,
    choiceEvidence: priorEvidence,
    dynamicControl: {
      ...stored.dynamicControl,
      answeredCount: effectiveAnswerCount,
      effectiveAnswerCount,
      plateauCount: candidateResult === null ? 0 : 1,
    },
    dynamicTurnState: {
      ...stored.dynamicTurnState,
      progress: {
        ...stored.dynamicTurnState.progress,
        answeredCount: effectiveAnswerCount,
        effectiveAnswerCount,
        plateauCount: candidateResult === null ? 0 : 1,
      },
    },
  };
}

function scoringFlow(input: {
  readonly candidate?: CandidateResult;
  readonly initialCandidate?: CandidateResult | null;
  readonly priorEvidence?: readonly ServerChoiceEvidence[];
  readonly failOnce?: boolean;
} = {}) {
  const initial = freshDynamicCase(input.initialCandidate ?? null, input.priorEvidence);
  const memory = memoryStore(initial);
  const jobs = dynamicJobStore(memory.store, () => {
    const value = memory.savedCase();
    return value?.journeyProtocol === "dynamic-choice-v2" ? value : null;
  });
  let scoreCalls = 0;
  let shouldFail = input.failOnce ?? false;
  const candidate = input.candidate ?? lowCandidate;
  const service = createBirthTimeJourneyService({
    store: jobs.store,
    engine: {
      async scan() { throw new Error("unexpected scan"); },
      async score() { throw new Error("unexpected score"); },
      async scoreEvents() { throw new Error("unexpected event score"); },
      async scoreChoices() {
        scoreCalls += 1;
        if (shouldFail) {
          shouldFail = false;
          throw new TypeError("offline");
        }
        return {
          candidate,
          evidenceMode: "dynamic_choice" as const,
          effectiveAnswerCount: candidate.eventCount,
          dimensionCount: candidate.domainCount,
        };
      },
      async buildDifferencePacket(value) {
        return {
          packet: {
            caseId: value.caseId,
            scoringVersion: "birth-time-choice-scoring-v2" as const,
            currentRange: { startTime: value.startTime, endTime: value.endTime },
            opportunities: [{
              opportunityId: "next-opportunity",
              dimensionCode: "relocation_change",
              neutralContext: "一次居住变化",
              estimatedInformationGain: 0.5,
              candidatePartitionFingerprint: "next-partition",
              fallbackPrompt: "哪一段更接近一次居住变化？",
              partitions: [
                { partitionId: "early", descriptor: "early", fallbackLabel: "较早" },
                { partitionId: "late", descriptor: "late", fallbackLabel: "较晚" },
              ],
            }],
            askedQuestionFingerprints: value.questionFingerprints,
            candidatePartitionFingerprints: value.partitionFingerprints,
            recentRangeHistory: value.recentRanges,
          },
          candidateModel: { version: "after-score" },
          scoringPartitions: {},
        };
      },
    },
  });
  return { memory, jobs, service, scoreCalls: () => scoreCalls };
}

test("score completion continues only when stop policy allows it", () => {
  const stored = dynamicCase();
  const result = completeDynamicScoreTransition({
    stored: { ...stored, currentChoiceQuestion: null },
    candidate: lowCandidate,
    usefulOpportunityCount: 1,
    repeatedOnly: false,
    nextVersion: 8,
  });

  assert.equal(result.dynamicTurnState.nextAction.kind, "generate_dynamic_question");
  assert.equal(result.dynamicControl.plateauCount, 0);
});

test("high confidence requires explicit confirmation without applying a time", () => {
  const stored = dynamicCase();
  const candidate = {
    ...lowCandidate,
    resultId: "097b7b4c-60f3-4ed8-b290-64b2084182e7",
    confidence: "high" as const,
    canApply: true,
    winningSegment: {
      startTime: "05:10",
      endTime: "05:12",
      representativeTime: "05:11",
      widthMinutes: 2,
    },
    eventCount: 4,
    domainCount: 3,
    marginPercent: 20,
  };
  const result = completeDynamicScoreTransition({
    stored: { ...stored, currentChoiceQuestion: null },
    candidate,
    usefulOpportunityCount: 1,
    repeatedOnly: false,
    nextVersion: 8,
  });

  assert.deepEqual(result.dynamicTurnState.nextAction, {
    kind: "request_candidate_confirmation",
    resultId: candidate.resultId,
  });
  assert.equal(result.snapshot.activeTime, null);
  assert.equal(result.dynamicTurnState.permissions.canConfirmCandidate, true);
});

test("dynamic scoring claims once, completes atomically, and replays", async () => {
  const flow = scoringFlow();
  const pending = await flow.service.answerDynamicChoice(ownerId, {
    caseId: dynamicCase().id,
    actionId,
    turnVersion: 7,
    questionId: persistedQuestion.questionId,
    optionId: persistedQuestion.options[0].optionId,
  });
  if (pending.nextAction.kind !== "score_pending") throw new Error("expected pending score");

  const first = await flow.service.pollDynamicScoringJob(ownerId, dynamicCase().id, pending.nextAction.jobId);
  const replay = await flow.service.pollDynamicScoringJob(ownerId, dynamicCase().id, pending.nextAction.jobId);

  assert.equal(first.nextAction.kind, "generate_dynamic_question");
  assert.deepEqual(replay.nextAction, first.nextAction);
  assert.equal(flow.scoreCalls(), 1);
  assert.deepEqual(flow.memory.savedCase()?.candidateModel, { version: "after-score" });
});

test("dynamic scoring failure retries the same job without duplicating evidence", async () => {
  const flow = scoringFlow({ failOnce: true });
  const pending = await flow.service.answerDynamicChoice(ownerId, {
    caseId: dynamicCase().id,
    actionId,
    turnVersion: 7,
    questionId: persistedQuestion.questionId,
    optionId: persistedQuestion.options[0].optionId,
  });
  if (pending.nextAction.kind !== "score_pending") throw new Error("expected pending score");
  const jobId = pending.nextAction.jobId;

  const failed = await flow.service.pollDynamicScoringJob(ownerId, dynamicCase().id, jobId);
  const completed = await flow.service.pollDynamicScoringJob(ownerId, dynamicCase().id, jobId);

  assert.deepEqual(failed.nextAction, { kind: "retry_scoring", jobId });
  assert.equal(completed.nextAction.kind, "generate_dynamic_question");
  assert.equal(flow.memory.savedCase()?.choiceEvidence?.length, 1);
  assert.equal(flow.memory.savedCase()?.dynamicControl?.effectiveAnswerCount, 1);
  assert.equal(flow.scoreCalls(), 2);
});

test("the second plateau is terminal and resume stays terminal", async () => {
  const medium = {
    ...lowCandidate,
    confidence: "medium" as const,
    winningSegment: {
      startTime: "05:10", endTime: "05:12", representativeTime: "05:11", widthMinutes: 3,
    },
    eventCount: 3,
    domainCount: 3,
    marginPercent: 10,
  };
  const priorEvidence = ["education_change", "relationship_change"].map((dimensionCode, index) => ({
    questionId: `prior-${index}`,
    opportunityId: `opportunity-${index}`,
    partitionId: `partition-${index}`,
    dimensionCode,
    candidateScores: { "05:10": 1 },
    informationGain: 0.5,
  }));
  const previous = { ...medium, confidence: "low" as const, eventCount: 2, domainCount: 2 };
  const flow = scoringFlow({ initialCandidate: previous, candidate: medium, priorEvidence });
  const pending = await flow.service.answerDynamicChoice(ownerId, {
    caseId: dynamicCase().id,
    actionId,
    turnVersion: 7,
    questionId: persistedQuestion.questionId,
    optionId: persistedQuestion.options[0].optionId,
  });
  if (pending.nextAction.kind !== "score_pending") throw new Error("expected pending score");

  const terminal = await flow.service.pollDynamicScoringJob(ownerId, dynamicCase().id, pending.nextAction.jobId);
  const resumed = await flow.service.resumeDynamic(ownerId, dynamicCase().id);

  assert.equal(terminal.nextAction.kind, "present_medium_result");
  assert.deepEqual(resumed.nextAction, terminal.nextAction);
});
