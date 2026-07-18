import { createDynamicTurnPersistence } from "../src/lib/birth-time-journey-dynamic-persistence.ts";
import type {
  DynamicStoredRectificationCase,
  LegacyStoredRectificationCase,
} from "../src/lib/birth-time-journey-service.ts";

export const caseId = "45857b75-4718-4590-aaf5-7113a03ea765";
export const ownerId = "12dc56f0-1f17-4a2f-86bf-1056ab78def9";
export const actionId = "a9890e09-d535-46f0-9a36-86017515a5a1";
export const currentRange = { startTime: "05:00", endTime: "06:00" } as const;

export const snapshot = {
  state: "rectifying",
  assistantIntent: "continue_rectification_questions",
  input: "rectification_questions",
  route: "rectification",
  confidence: null,
  canApply: false,
  activeTime: null,
  reportedRange: { label: "05:00—06:00", startTime: "05:00", endTime: "06:00" },
} as const;

export const persistedQuestion = {
  questionId: "11111111-1111-4111-8111-111111111111",
  opportunityId: "career-window",
  dimensionCode: "career_change",
  estimatedInformationGain: 0.7,
  scoringVersion: "birth-time-choice-scoring-v2",
  source: "fallback",
  questionFingerprint: "question-fingerprint",
  candidatePartitionFingerprint: "partition-fingerprint",
  prompt: "哪一个时间段更接近这次工作变化？",
  options: [
    {
      optionId: "22222222-2222-4222-8222-222222222222",
      label: "较早阶段",
      kind: "primary",
      partitionId: "window-a",
      candidateScores: { "05:10": 0.8 },
    },
    {
      optionId: "33333333-3333-4333-8333-333333333333",
      label: "较晚阶段",
      kind: "primary",
      partitionId: "window-b",
      candidateScores: { "05:50": 0.7 },
    },
    {
      optionId: "44444444-4444-4444-8444-444444444444",
      label: "不确定 / 不记得",
      kind: "unknown",
      partitionId: null,
      candidateScores: null,
    },
    {
      optionId: "55555555-5555-4555-8555-555555555555",
      label: "都不符合",
      kind: "unmatched",
      partitionId: null,
      candidateScores: null,
    },
  ],
} as const;

export const dynamicTurnState = {
  journeyProtocol: "dynamic-choice-v2",
  turnVersion: 7,
  nextAction: {
    kind: "ask_dynamic_choice",
    question: {
      questionId: persistedQuestion.questionId,
      prompt: persistedQuestion.prompt,
      options: persistedQuestion.options.map(({ optionId, label, kind }) => ({ optionId, label, kind })),
    },
  },
  progress: {
    phase: "question",
    answeredCount: 1,
    effectiveAnswerCount: 1,
    currentRange,
    previousRange: null,
    plateauCount: 0,
  },
  permissions: { canConfirmCandidate: false },
} as const;

export const dynamicControl = {
  asOfDate: "2026-07-18",
  answeredCount: 1,
  effectiveAnswerCount: 1,
  plateauCount: 0,
  questionFingerprints: [persistedQuestion.questionFingerprint],
  partitionFingerprints: [persistedQuestion.candidatePartitionFingerprint],
  dismissedOpportunityIds: [],
  recentRanges: [currentRange],
  pausedAction: null,
} as const;

const publicRow = {
  id: caseId,
  user_id: ownerId,
  journey_protocol: "dynamic-choice-v2",
  journey_snapshot: snapshot,
  questionnaire: {},
  answers: { legacy: "A" },
  scoring_result: {},
  reported_date: "1993-04-17",
  life_events: [],
  candidate_result: {},
  turn_version: 7,
  turn_state: dynamicTurnState,
  evidence_draft: null,
  processed_action_ids: [],
  adaptive_round: 0,
  asked_domains: [],
};

export const privateRow = {
  case_id: caseId,
  user_id: ownerId,
  candidate_model: { candidates: ["05:10", "05:50"] },
  current_choice_question: persistedQuestion,
  choice_answers: [{
    questionId: "prior-question",
    optionId: "prior-option",
    kind: "primary",
    opportunityId: "prior-opportunity",
    answeredAt: "2026-07-18T08:00:00.000Z",
  }],
  choice_evidence: [{
    questionId: "prior-question",
    opportunityId: "prior-opportunity",
    partitionId: "prior-partition",
    dimensionCode: "relocation_change",
    candidateScores: { "05:10": 0.6, "05:50": 0.2 },
    informationGain: 0.4,
  }],
  dynamic_control: dynamicControl,
  agent_context: ["用户只记得大概阶段"],
};

export function loadClient(
  privateState: typeof privateRow | null,
  omitProcessedActions = false,
) {
  const { processed_action_ids: ignoredReceipts, ...rowWithoutReceipts } = publicRow;
  void ignoredReceipts;
  return {
    from(table: string) {
      const row = table === "birth_time_rectification_cases"
        ? omitProcessedActions ? rowWithoutReceipts : publicRow
        : table === "birth_time_rectification_dynamic_state"
          ? privateState
          : { latitude: 31.2304, longitude: 121.4737, timezone_offset: 8 };
      const query = {
        select() { return query; },
        eq() { return query; },
        async maybeSingle() { return { data: row, error: null }; },
      };
      return query;
    },
  };
}

export function dynamicCase(): DynamicStoredRectificationCase {
  return {
    id: caseId,
    userId: ownerId,
    journeyProtocol: "dynamic-choice-v2",
    snapshot,
    questionnaire: null,
    answers: { legacy: "A" },
    lifeEvents: [],
    candidateResult: null,
    turnVersion: 7,
    dynamicTurnState,
    processedActionIds: [],
    candidateModel: privateRow.candidate_model,
    currentChoiceQuestion: persistedQuestion,
    choiceAnswers: [],
    choiceEvidence: [],
    dynamicControl,
    agentContext: privateRow.agent_context,
  };
}

export function rpcPersistence() {
  let saved = dynamicCase();
  const calls: { readonly name: string; readonly args: Readonly<Record<string, unknown>> }[] = [];
  return {
    calls,
    persistence: createDynamicTurnPersistence({
      async rpc(name: string, args: Readonly<Record<string, unknown>>) {
        calls.push({ name, args });
        const receivedAction = String(args.p_action_id ?? "");
        if (saved.processedActionIds.includes(receivedAction)) {
          return { data: saved.turnVersion, error: null };
        }
        if (args.p_expected_version !== saved.turnVersion) {
          return { data: null, error: { message: "stale_birth_time_dynamic_turn" } };
        }
        saved = {
          ...saved,
          turnVersion: saved.turnVersion + 1,
          dynamicTurnState: { ...saved.dynamicTurnState, turnVersion: saved.turnVersion + 1 },
          processedActionIds: [...saved.processedActionIds, receivedAction],
        };
        return { data: saved.turnVersion, error: null };
      },
    }, async () => saved, () => "2026-07-18"),
  };
}

export function legacyCase(active: boolean): LegacyStoredRectificationCase {
  return {
    id: caseId,
    userId: ownerId,
    snapshot,
    questionnaire: null,
    answers: { q1: "A" },
    lifeEvents: [{ id: "event-1", domain: "career", precision: "year", date: "2019" }],
    candidateResult: null,
    turnVersion: 4,
    turnState: {
      turnVersion: 4,
      nextAction: active
        ? {
            kind: "ask_baseline_evidence",
            question: {
              questionId: "legacy-question",
              phase: "baseline",
              domain: "career",
              requestedPrecision: ["year"],
              allowUnknown: true,
              purposeCode: "legacy",
              plannerVersion: "legacy-v1",
            },
          }
        : { kind: "present_low_result", resultId: null },
      progress: {
        phase: active ? "baseline" : "result",
        baselineDomainCount: 1,
        confirmedEvidenceCount: 1,
        adaptiveRound: 0,
        maxAdaptiveRounds: 3,
      },
      permissions: { canConfirmCandidate: false },
      evidenceDraft: null,
    },
    evidenceDraft: null,
    processedActionIds: [],
    persistedProgress: { adaptiveRound: 0, askedDomains: ["career"] },
  };
}
