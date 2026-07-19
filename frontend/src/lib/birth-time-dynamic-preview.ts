import { parseJourneyResponse } from "./birth-time-journey-client.ts";
import type { DynamicJourneyClientResponse } from "./birth-time-journey-response-schema.ts";
import type { DynamicNextAction } from "./birth-time-journey-turn-protocol.ts";
import type { CandidateResult } from "./birth-time-evidence.ts";

const caseId = "7299894c-10a8-4b45-91d1-339007282c50";
const resultId = "345087cc-7e7f-4b37-90e5-f0c0a6e5b7a7";
const jobId = "5da741ba-4713-4c27-9cf4-a85e52dc4658";

class DynamicPreviewInvariantError extends Error {
  readonly name = "DynamicPreviewInvariantError";
}

const questions = [
  {
    questionId: "education-shift",
    prompt: "哪段时间更接近一次明显的升学、转学或学习方向变化？",
    options: [
      { optionId: "earlier", label: "更接近 2007—2009 年", kind: "primary" },
      { optionId: "later", label: "更接近 2010—2012 年", kind: "primary" },
      { optionId: "unknown", label: "不记得", kind: "unknown" },
      { optionId: "unmatched", label: "都不符合", kind: "unmatched" },
    ],
  },
  {
    questionId: "relocation-shift",
    prompt: "第一次明显离开熟悉环境，更接近下面哪个阶段？",
    options: [
      { optionId: "school", label: "求学阶段", kind: "primary" },
      { optionId: "work", label: "开始工作之后", kind: "primary" },
      { optionId: "unknown-2", label: "不记得", kind: "unknown" },
      { optionId: "unmatched-2", label: "都不符合", kind: "unmatched" },
    ],
  },
] as const;

const candidate = {
  resultId,
  confidence: "medium",
  canApply: false,
  winningSegment: {
    startTime: "05:38",
    endTime: "05:49",
    representativeTime: "05:43",
    widthMinutes: 12,
  },
  eventCount: 3,
  domainCount: 0,
  topScore: 14.4,
  secondScore: 12.1,
  marginPercent: 15.97,
  reasons: [],
  evidence: [],
  algorithmVersion: "birth-time-dynamic-scoring-v2",
} satisfies CandidateResult;

const highCandidate = {
  ...candidate,
  confidence: "high",
  canApply: true,
  winningSegment: { ...candidate.winningSegment, widthMinutes: 5 },
  eventCount: 4,
  domainCount: 3,
  marginPercent: 24,
} satisfies CandidateResult;

const terminalLowCandidate = {
  ...candidate,
  confidence: "low",
  winningSegment: {
    startTime: "05:18",
    endTime: "05:24",
    representativeTime: "05:21",
    widthMinutes: 7,
  },
  eventCount: 4,
  domainCount: 3,
} satisfies CandidateResult;

function response(input: {
  readonly nextAction: DynamicNextAction;
  readonly phase: "question" | "clarification" | "scoring" | "result" | "ready" | "paused";
  readonly turnVersion?: number;
  readonly answeredCount?: number;
  readonly effectiveAnswerCount?: number;
  readonly candidateResult?: CandidateResult | null;
  readonly snapshotState?: "rectifying" | "candidate" | "confirming" | "ready";
  readonly activeTime?: string | null;
}): DynamicJourneyClientResponse {
  const parsed = parseJourneyResponse({
    caseId,
    snapshot: {
      state: input.snapshotState ?? "rectifying",
      assistantIntent: "start_standard_rectification",
      input: input.phase === "ready" ? "none" : input.phase === "result" ? "candidate_actions" : "rectification_questions",
      route: input.phase === "ready" ? "direct_chart" : "rectification",
      confidence: input.candidateResult?.confidence ?? null,
      canApply: input.nextAction.kind === "request_candidate_confirmation",
      activeTime: input.activeTime ?? null,
      reportedRange: { label: "04:00—07:59", startTime: "04:00", endTime: "07:59" },
    },
    questionnaire: null,
    scoring: null,
    answers: {},
    lifeEvents: [],
    candidateResult: input.candidateResult ?? null,
    journeyProtocol: "dynamic-choice-v2",
    turnVersion: input.turnVersion ?? 1,
    nextAction: input.nextAction,
    progress: {
      phase: input.phase,
      answeredCount: input.answeredCount ?? 0,
      effectiveAnswerCount: input.effectiveAnswerCount ?? 0,
      currentRange: { startTime: "04:00", endTime: "07:59" },
      previousRange: null,
      plateauCount: 0,
    },
    permissions: { canConfirmCandidate: input.nextAction.kind === "request_candidate_confirmation" },
    evidenceDraft: null,
  });
  if (parsed.journeyProtocol !== "dynamic-choice-v2") {
    throw new DynamicPreviewInvariantError("Dynamic preview parsed as legacy journey");
  }
  return parsed;
}

export function dynamicBirthTimePreview(
  state: "generating" | "question-retry" | "question" | "clarification" | "scoring" | "scoring-retry" | "low" | "terminal-low" | "medium" | "confirmation" | "ready" | "paused" = "question",
): DynamicJourneyClientResponse {
  switch (state) {
    case "generating": return response({ nextAction: { kind: "generate_dynamic_question" }, phase: "question" });
    case "question-retry": return response({ nextAction: { kind: "retry_question_generation" }, phase: "question" });
    case "question": return response({ nextAction: { kind: "ask_dynamic_choice", question: questions[0] }, phase: "question" });
    case "clarification": return response({ nextAction: { kind: "clarify_unmatched_answer", questionId: questions[0].questionId }, phase: "clarification", answeredCount: 1, turnVersion: 2 });
    case "scoring": return response({ nextAction: { kind: "score_pending", jobId }, phase: "scoring", answeredCount: 1, effectiveAnswerCount: 1, turnVersion: 2 });
    case "scoring-retry": return response({ nextAction: { kind: "retry_scoring", jobId }, phase: "scoring", answeredCount: 1, effectiveAnswerCount: 1, turnVersion: 2 });
    case "low": return response({ nextAction: { kind: "present_low_result", resultId: null }, phase: "result", answeredCount: 2, effectiveAnswerCount: 1, snapshotState: "candidate", turnVersion: 3 });
    case "terminal-low": return response({ nextAction: { kind: "present_low_result", resultId }, phase: "result", answeredCount: 4, effectiveAnswerCount: 3, candidateResult: terminalLowCandidate, snapshotState: "rectifying", turnVersion: 4 });
    case "medium": return response({ nextAction: { kind: "present_medium_result", resultId }, phase: "result", answeredCount: 3, effectiveAnswerCount: 2, candidateResult: candidate, snapshotState: "candidate", turnVersion: 4 });
    case "confirmation": return response({ nextAction: { kind: "request_candidate_confirmation", resultId }, phase: "result", answeredCount: 4, effectiveAnswerCount: 4, candidateResult: highCandidate, snapshotState: "confirming", turnVersion: 5 });
    case "ready": return response({ nextAction: { kind: "ready", activeTime: "05:43" }, phase: "ready", answeredCount: 4, effectiveAnswerCount: 4, candidateResult: highCandidate, snapshotState: "ready", activeTime: "05:43", turnVersion: 6 });
    case "paused": return response({ nextAction: { kind: "paused" }, phase: "paused", turnVersion: 2 });
  }
}

export type DynamicPreviewCommand =
  | { readonly kind: "select"; readonly optionId: string }
  | { readonly kind: "reframe" }
  | { readonly kind: "finish" }
  | { readonly kind: "pause" }
  | { readonly kind: "resume" }
  | { readonly kind: "retry_scoring" };

export function advanceDynamicBirthTimePreview(
  turn: DynamicJourneyClientResponse,
  command: DynamicPreviewCommand,
): DynamicJourneyClientResponse {
  switch (command.kind) {
    case "select": {
      const action = turn.nextAction;
      if (action.kind !== "ask_dynamic_choice") return turn;
      const option = action.question.options.find((item) => item.optionId === command.optionId);
      if (!option) return turn;
      const answeredCount = turn.progress.answeredCount + 1;
      const effectiveAnswerCount = turn.progress.effectiveAnswerCount + (option.kind === "primary" ? 1 : 0);
      switch (option.kind) {
        case "unmatched": return response({
          nextAction: { kind: "clarify_unmatched_answer", questionId: action.question.questionId },
          phase: "clarification",
          answeredCount,
          effectiveAnswerCount,
          turnVersion: turn.turnVersion + 1,
        });
        case "primary": {
          if (action.question.questionId === questions[0].questionId) {
            return response({
              nextAction: { kind: "ask_dynamic_choice", question: questions[1] },
              phase: "question",
              answeredCount,
              effectiveAnswerCount,
              turnVersion: turn.turnVersion + 1,
            });
          }
          return response({
            nextAction: { kind: "present_medium_result", resultId },
            phase: "result",
            answeredCount,
            effectiveAnswerCount,
            candidateResult: candidate,
            snapshotState: "candidate",
            turnVersion: turn.turnVersion + 1,
          });
        }
        case "unknown": {
          if (action.question.questionId === questions[0].questionId) {
            return response({
              nextAction: { kind: "ask_dynamic_choice", question: questions[1] },
              phase: "question",
              answeredCount,
              effectiveAnswerCount,
              turnVersion: turn.turnVersion + 1,
            });
          }
          return response({
            nextAction: { kind: "present_low_result", resultId: null },
            phase: "result",
            answeredCount,
            effectiveAnswerCount,
            snapshotState: "candidate",
            turnVersion: turn.turnVersion + 1,
          });
        }
      }
    }
    case "reframe": {
      if (turn.nextAction.kind === "clarify_unmatched_answer"
        && turn.nextAction.questionId === questions[1].questionId) {
        return response({
          nextAction: { kind: "present_low_result", resultId: null },
          phase: "result",
          answeredCount: turn.progress.answeredCount,
          effectiveAnswerCount: turn.progress.effectiveAnswerCount,
          snapshotState: "candidate",
          turnVersion: turn.turnVersion + 1,
        });
      }
      return response({
        nextAction: { kind: "ask_dynamic_choice", question: questions[1] },
        phase: "question",
        answeredCount: turn.progress.answeredCount,
        effectiveAnswerCount: turn.progress.effectiveAnswerCount,
        turnVersion: turn.turnVersion + 1,
      });
    }
    case "finish": return response({
      nextAction: { kind: "present_low_result", resultId: null },
      phase: "result",
      answeredCount: turn.progress.answeredCount,
      effectiveAnswerCount: turn.progress.effectiveAnswerCount,
      snapshotState: "candidate",
      turnVersion: turn.turnVersion + 1,
    });
    case "pause": return dynamicBirthTimePreview("paused");
    case "resume": return dynamicBirthTimePreview("question");
    case "retry_scoring": return dynamicBirthTimePreview("medium");
  }
}
