import assert from "node:assert/strict";
import { z } from "zod";
import { createBirthTimeGuideService } from "../src/lib/birth-time-guide-service.ts";
import type { BirthTimeGuideGenerator } from "../src/lib/birth-time-guide-agent.ts";
import { candidateResultSchema } from "../src/lib/birth-time-evidence.ts";
import { createGuidedCandidateActions } from "../src/lib/birth-time-guided-candidate.ts";
import {
  createBirthTimeJourneyService,
  type LegacyBirthTimeJourneyEngine,
  type DynamicVersionedJourneyResponse,
  type StoredRectificationCase,
  type VersionedJourneyResponse,
} from "../src/lib/birth-time-journey-service.ts";
import { journeyMetric } from "../src/lib/birth-time-journey-telemetry.ts";
import {
  guidedCase,
  journeyCaseId,
  memoryStore,
  unusedJourneyEngine,
} from "./birth-time-journey-test-support.ts";

export const actionIds = [
  "00000000-0000-4000-8000-000000000001",
  "00000000-0000-4000-8000-000000000002",
  "00000000-0000-4000-8000-000000000003",
  "00000000-0000-4000-8000-000000000004",
  "00000000-0000-4000-8000-000000000005",
  "00000000-0000-4000-8000-000000000006",
  "00000000-0000-4000-8000-000000000007",
  "00000000-0000-4000-8000-000000000008",
  "00000000-0000-4000-8000-000000000009",
  "00000000-0000-4000-8000-000000000010",
  "00000000-0000-4000-8000-000000000011",
  "00000000-0000-4000-8000-000000000012",
  "00000000-0000-4000-8000-000000000013",
  "00000000-0000-4000-8000-000000000014",
  "00000000-0000-4000-8000-000000000015",
  "00000000-0000-4000-8000-000000000016",
] as const;

type Confidence = "low" | "medium" | "high";

export function candidate(confidence: Confidence, resultId: string) {
  return candidateResultSchema.parse({
    resultId,
    confidence,
    canApply: confidence === "high",
    winningSegment: confidence === "low"
      ? null
      : { startTime: "14:22", endTime: "14:26", representativeTime: "14:24", widthMinutes: 5 },
    eventCount: confidence === "high" ? 4 : 3,
    domainCount: confidence === "high" ? 4 : 3,
    topScore: confidence === "high" ? 18 : 14,
    secondScore: confidence === "high" ? 8 : 12,
    marginPercent: confidence === "high" ? 55 : 14,
    reasons: confidence === "low" ? ["Candidate scores remain close."] : [],
    evidence: [],
    algorithmVersion: "birth-time-event-scoring-v1",
  });
}

export type JourneyHarness = ReturnType<typeof createHarness>;

function createFakeAgent(): BirthTimeGuideGenerator {
  let nextYear = 2010;
  return {
    async generate(prompt: string) {
      const value = z.record(z.unknown()).parse(JSON.parse(prompt));
      if (value.task === "select_question_variant") return { text: '{"variant":"gentle"}' };
      const domain = z.string().parse(value.requiredDomain);
      const year = String(nextYear);
      nextYear += 1;
      return { text: JSON.stringify({ domain, precision: "year", date: year }) };
    },
  };
}

export function createHarness(input: {
  readonly initial: StoredRectificationCase;
  readonly result: ReturnType<typeof candidate>;
  readonly resultAfterAdaptive?: ReturnType<typeof candidate>;
  readonly failFirstScore?: boolean;
}) {
  const memory = memoryStore(input.initial);
  let scoreEventsCalls = 0;
  const engine: LegacyBirthTimeJourneyEngine = {
    ...unusedJourneyEngine,
    async scoreEvents() {
      scoreEventsCalls += 1;
      if (input.failFirstScore === true && scoreEventsCalls === 1) throw new Error("fake engine offline");
      return scoreEventsCalls > 1 && input.resultAfterAdaptive
        ? input.resultAfterAdaptive
        : input.result;
    },
  };
  const service = createBirthTimeJourneyService({ store: memory.store, engine });
  const guide = createBirthTimeGuideService({
    generator: createFakeAgent(),
    loadCase: memory.store.loadCase,
    proposeEvidenceDraft: service.proposeEvidenceDraft,
  });
  return {
    memory,
    service,
    guide,
    candidateActions: createGuidedCandidateActions({ store: memory.store }),
    scoreEventsCalls: () => scoreEventsCalls,
  };
}

export function assertLegalTurn(
  turn: VersionedJourneyResponse | DynamicVersionedJourneyResponse,
): asserts turn is VersionedJourneyResponse {
  if (turn.journeyProtocol === "dynamic-choice-v2") {
    assert.fail("legacy flow unexpectedly resumed a dynamic journey");
  }
  assert.ok(turn.nextAction, "every legal journey response has nextAction");
  assert.ok(turn.turnVersion >= 0);
  switch (turn.nextAction.kind) {
    case "ask_baseline_evidence":
    case "ask_adaptive_evidence":
      assert.ok(turn.nextAction.question.questionId.length > 0);
      break;
    case "review_evidence_draft":
      assert.equal(turn.evidenceDraft?.draftId, turn.nextAction.draftId);
      break;
    case "score_pending":
    case "retry_scoring":
      assert.ok(turn.nextAction.jobId.length > 0);
      assert.equal(turn.progress.phase, "scoring");
      break;
    case "present_low_result":
      assert.equal(turn.candidateResult?.confidence, "low");
      assert.equal(turn.permissions.canConfirmCandidate, false);
      assert.equal(turn.snapshot.activeTime, null);
      assert.equal(turn.nextAction.resultId, turn.candidateResult?.resultId ?? null);
      break;
    case "present_medium_result":
    case "candidate_saved":
      assert.equal(turn.candidateResult?.confidence, "medium");
      assert.equal(turn.permissions.canConfirmCandidate, false);
      assert.equal(turn.snapshot.activeTime, null);
      assert.equal(turn.nextAction.resultId, turn.candidateResult?.resultId ?? null);
      break;
    case "request_candidate_confirmation":
      assert.equal(turn.candidateResult?.confidence, "high");
      assert.equal(turn.permissions.canConfirmCandidate, true);
      assert.equal(turn.snapshot.state, "confirming");
      assert.equal(turn.snapshot.activeTime, null);
      assert.equal(turn.nextAction.resultId, turn.candidateResult?.resultId ?? null);
      assert.ok(turn.candidateResult?.winningSegment !== null);
      break;
    case "ready":
      assert.equal(turn.snapshot.state, "ready");
      assert.equal(turn.snapshot.route, "direct_chart");
      assert.equal(turn.snapshot.activeTime, turn.nextAction.activeTime);
      break;
    case "paused":
      assert.equal(turn.progress.phase, "paused");
      break;
    default: {
      const exhaustive: never = turn.nextAction;
      assert.fail(`unexpected action ${String(exhaustive)}`);
    }
  }
}

export async function confirmDirectEvidence(input: {
  readonly harness: JourneyHarness;
  readonly turn: VersionedJourneyResponse;
  readonly proposalActionId: string;
  readonly confirmActionId: string;
  readonly date: string;
}): Promise<VersionedJourneyResponse> {
  assert.ok(
    input.turn.nextAction.kind === "ask_baseline_evidence"
      || input.turn.nextAction.kind === "ask_adaptive_evidence",
  );
  const reviewed = await input.harness.service.proposeEvidenceDraft(
    "user-1",
    journeyCaseId,
    input.proposalActionId,
    input.turn.turnVersion,
    { domain: input.turn.nextAction.question.domain, precision: "year", date: input.date },
  );
  assertLegalTurn(reviewed);
  assert.equal(reviewed.nextAction.kind, "review_evidence_draft");
  const confirmed = await input.harness.service.confirmEvidenceDraft(
    "user-1",
    journeyCaseId,
    input.confirmActionId,
    reviewed.turnVersion,
    reviewed.nextAction.draftId,
  );
  assertLegalTurn(confirmed);
  return confirmed;
}

export async function confirmGuideEvidence(input: {
  readonly harness: JourneyHarness;
  readonly turn: VersionedJourneyResponse;
  readonly actionId: (typeof actionIds)[number];
  readonly year: string;
}): Promise<VersionedJourneyResponse> {
  assert.equal(input.turn.nextAction.kind, "ask_baseline_evidence");
  const guideDraft = await input.harness.guide.draftEvidence("user-1", {
    caseId: journeyCaseId,
    actionId: input.actionId,
    turnVersion: input.turn.turnVersion,
    message: `${input.year} 年发生了一次明显变化`,
  });
  assert.equal(guideDraft.type, "evidence_draft");
  assertLegalTurn(guideDraft.turn);
  assert.equal(guideDraft.turn.nextAction.kind, "review_evidence_draft");
  const confirmed = await input.harness.service.confirmEvidenceDraft(
    "user-1",
    journeyCaseId,
    actionIds[actionIds.indexOf(input.actionId) + 1] ?? actionIds[0],
    guideDraft.turn.turnVersion,
    guideDraft.turn.nextAction.draftId,
  );
  assertLegalTurn(confirmed);
  return confirmed;
}

export async function reachScoring(input: {
  readonly harness: JourneyHarness;
  readonly useGuide?: boolean;
}): Promise<VersionedJourneyResponse> {
  let turn = await input.harness.service.resume("user-1", journeyCaseId);
  assertLegalTurn(turn);
  if (input.useGuide === true) {
    turn = await confirmGuideEvidence({ harness: input.harness, turn, actionId: actionIds[0], year: "2010" });
    turn = await confirmGuideEvidence({ harness: input.harness, turn, actionId: actionIds[2], year: "2011" });
    turn = await confirmGuideEvidence({ harness: input.harness, turn, actionId: actionIds[4], year: "2012" });
  } else {
    turn = await confirmDirectEvidence({ harness: input.harness, turn, proposalActionId: actionIds[0], confirmActionId: actionIds[1], date: "2010" });
    turn = await confirmDirectEvidence({ harness: input.harness, turn, proposalActionId: actionIds[2], confirmActionId: actionIds[3], date: "2011" });
    turn = await confirmDirectEvidence({ harness: input.harness, turn, proposalActionId: actionIds[4], confirmActionId: actionIds[5], date: "2012" });
  }
  assert.equal(turn.nextAction.kind, "score_pending");
  return turn;
}

export { guidedCase, journeyCaseId, journeyMetric };
