import { z } from "zod";
import { candidateResultSchema, lifeEventSchema } from "./birth-time-journey.ts";
import type { LifeEvent } from "./birth-time-evidence.ts";
import { deriveJourneyPermissions } from "./birth-time-journey-turn.ts";
import type { NextAction } from "./birth-time-journey-turn.ts";
import { birthTimeJourneyRequestSchema } from "./birth-time-journey-request.ts";
import { JourneyResponseInvariantError, answerSchema, parseVersionedJourneyResponse, responseCore, scoringFields } from "./birth-time-journey-response-schema.ts";
import type { JourneyAnswer, JourneyClientResponse } from "./birth-time-journey-response-schema.ts";
import { postJson } from "./birth-time-client-transport.ts";
import {
  birthTimeGuideRequestSchema,
  guideDraftEnvelopeSchema,
  guideQuestionResponseSchema,
} from "./birth-time-guide-agent.ts";

const legacyScoringSchema = z.object({ ...scoringFields, nextRound: z.number().int().min(1).nullable().default(null), nextRoundQuestions: z.array(z.object({ id: z.string(), prompt: z.string(), round: z.number().int().min(1).optional(), options: z.array(z.object({ key: answerSchema, label: z.string() }).strict()).optional() }).strict()).default([]) }).strict();
const legacyJourneyResponseSchema = z.object({
  ...responseCore, scoring: legacyScoringSchema.nullable(), answers: z.record(answerSchema).default({}), lifeEvents: z.array(lifeEventSchema).default([]), candidateResult: candidateResultSchema.nullable().default(null),
}).superRefine((value, context) => {
  const guardedConfirmation = value.snapshot.state === "confirming" && value.snapshot.input === "candidate_confirmation" && value.snapshot.confidence === "high" && value.snapshot.activeTime === null && value.candidateResult?.confidence === "high" && value.candidateResult.canApply;
  if (value.snapshot.route === "rectification" && value.snapshot.canApply && !guardedConfirmation) context.addIssue({ code: z.ZodIssueCode.custom, path: ["snapshot", "canApply"], message: "rectification can apply only through a guarded confirmation state" });
  if (value.snapshot.state === "confirming" && !guardedConfirmation) context.addIssue({ code: z.ZodIssueCode.custom, path: ["snapshot", "state"], message: "candidate confirmation requires a matching high-confidence result" });
  if (value.snapshot.route === "direct_chart" && !value.snapshot.activeTime) context.addIssue({ code: z.ZodIssueCode.custom, path: ["snapshot", "activeTime"], message: "direct chart requires an active time" });
});

const errorPayloadSchema = z.object({
  message: z.string().optional(),
  error: z.string().optional(),
});

export type { JourneyClientResponse, JourneyAnswer } from "./birth-time-journey-response-schema.ts";
export { birthTimeJourneyRequestSchema } from "./birth-time-journey-request.ts";

export class BirthTimeJourneyRequestError extends Error {
  readonly name = "BirthTimeJourneyRequestError";
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function assertNever(value: never): never {
  throw new JourneyResponseInvariantError(`Unexpected candidate confidence: ${String(value)}`);
}

function legacyNextAction(value: z.infer<typeof legacyJourneyResponseSchema>): NextAction {
  if (value.snapshot.state === "ready" && value.snapshot.activeTime) {
    return { kind: "ready", activeTime: value.snapshot.activeTime };
  }
  const result = value.candidateResult;
  if (!result) return { kind: "paused" };
  switch (result.confidence) {
    case "high":
      return { kind: "request_candidate_confirmation", resultId: result.resultId };
    case "medium":
      return { kind: "present_medium_result", resultId: result.resultId };
    case "low":
      return { kind: "present_low_result", resultId: result.resultId };
    default:
      return assertNever(result.confidence);
  }
}

function legacyProgress(value: z.infer<typeof legacyJourneyResponseSchema>) {
  return {
    phase: value.snapshot.state === "ready"
      ? "ready"
      : value.candidateResult
        ? "result"
        : "paused",
    baselineDomainCount: 0,
    confirmedEvidenceCount: value.lifeEvents.length,
    adaptiveRound: 0,
    maxAdaptiveRounds: 3,
  } as const;
}

function normalizeLegacyJourneyResponse(
  value: z.infer<typeof legacyJourneyResponseSchema>,
): JourneyClientResponse {
  const confirmedTime = value.snapshot.state === "ready" ? value.snapshot.activeTime : null;
  return {
    ...value,
    turnVersion: 0,
    nextAction: legacyNextAction(value),
    progress: legacyProgress(value),
    permissions: deriveJourneyPermissions(value.candidateResult, confirmedTime),
    evidenceDraft: null,
  };
}

export function parseJourneyResponse(value: unknown): JourneyClientResponse {
  const version = z.object({ turnVersion: z.unknown().optional() }).passthrough().parse(value);
  if (version.turnVersion !== undefined) return parseVersionedJourneyResponse(value);
  return normalizeLegacyJourneyResponse(legacyJourneyResponseSchema.parse(value));
}

async function sendJourneyEvent(event: Readonly<Record<string, unknown>>, signal?: AbortSignal) {
  const request = birthTimeJourneyRequestSchema.parse(event);
  const { response, payload } = await postJson({
    url: "/api/birth-time-journey",
    body: JSON.stringify(request),
    retryLostResponse: "actionId" in request,
    ...(signal ? { signal } : {}),
  });
  if (!response.ok) {
    const parsedError = errorPayloadSchema.safeParse(payload);
    const message = parsedError.success
      ? parsedError.data.message ?? parsedError.data.error ?? "生时评估暂时不可用"
      : "生时评估暂时不可用";
    throw new BirthTimeJourneyRequestError(response.status, message);
  }
  return parseJourneyResponse(payload);
}

export function requestBirthTimeAssessment() {
  return sendJourneyEvent({ type: "assess" });
}

export function answerBirthTimeQuestion(
  caseId: string,
  questionId: string,
  answer: JourneyAnswer,
) {
  return sendJourneyEvent({ type: "answer_question", caseId, questionId, answer });
}

export function resumeBirthTimeJourney(caseId: string) {
  return sendJourneyEvent({ type: "resume", caseId });
}

export function pollBirthTimeScoring(caseId: string, jobId: string, signal?: AbortSignal) {
  return sendJourneyEvent({ type: "poll_scoring", caseId, jobId }, signal);
}

export function answerDynamicBirthTimeChoice(input: {
  readonly caseId: string;
  readonly actionId: string;
  readonly turnVersion: number;
  readonly questionId: string;
  readonly optionId: string;
}) {
  return sendJourneyEvent({ type: "answer_dynamic_choice", ...input });
}

export function submitBirthTimeLifeEvents(caseId: string, events: readonly LifeEvent[]) {
  return sendJourneyEvent({ type: "submit_life_events", caseId, events });
}

export function saveBirthTimeCandidate(caseId: string, resultId: string) {
  return sendJourneyEvent({ type: "save_candidate", caseId, resultId });
}

export function confirmBirthTimeCandidate(
  caseId: string,
  resultId: string,
  time: string,
) {
  return sendJourneyEvent({ type: "confirm_candidate", caseId, resultId, time });
}

export function confirmBirthTimeEvidenceDraft(
  caseId: string,
  actionId: string,
  turnVersion: number,
  draftId: string,
) {
  return sendJourneyEvent({ type: "confirm_evidence_draft", caseId, actionId, turnVersion, draftId });
}

export function skipBirthTimeEvidenceQuestion(caseId: string, actionId: string, turnVersion: number) {
  return sendJourneyEvent({ type: "skip_evidence_question", caseId, actionId, turnVersion });
}

export function pauseBirthTimeRectification(caseId: string, actionId: string, turnVersion: number) {
  return sendJourneyEvent({ type: "pause_rectification", caseId, actionId, turnVersion });
}

export function finishBirthTimeRectification(caseId: string, actionId: string, turnVersion: number) {
  return sendJourneyEvent({ type: "finish_rectification", caseId, actionId, turnVersion });
}

async function sendGuideEvent(event: Readonly<Record<string, unknown>>): Promise<unknown> {
  const request = birthTimeGuideRequestSchema.parse(event);
  const { response, payload } = await postJson({
    url: "/api/birth-time-guide",
    body: JSON.stringify(request),
    retryLostResponse: "actionId" in request,
  });
  if (!response.ok) {
    const parsedError = errorPayloadSchema.safeParse(payload);
    const message = parsedError.success
      ? parsedError.data.message ?? parsedError.data.error ?? "生时引导暂时不可用"
      : "生时引导暂时不可用";
    throw new BirthTimeJourneyRequestError(response.status, message);
  }
  return payload;
}

export async function requestBirthTimeGuidePrompt(caseId: string) {
  const payload = await sendGuideEvent({ type: "render_question", caseId });
  return guideQuestionResponseSchema.parse(payload);
}

export async function draftBirthTimeEvidence(
  caseId: string,
  actionId: string,
  turnVersion: number,
  message: string,
) {
  const payload = await sendGuideEvent({
    type: "draft_evidence",
    caseId,
    actionId,
    turnVersion,
    message,
  });
  const envelope = guideDraftEnvelopeSchema.parse(payload);
  return { ...envelope, turn: parseJourneyResponse(envelope.turn) };
}

export async function generateDynamicBirthTimeQuestion(
  caseId: string,
  actionId: string,
  turnVersion: number,
) {
  const payload = await sendGuideEvent({
    type: "generate_dynamic_question",
    caseId,
    actionId,
    turnVersion,
  });
  return parseJourneyResponse(payload);
}

export async function reframeUnmatchedBirthTimeAnswer(input: {
  readonly caseId: string;
  readonly actionId: string;
  readonly turnVersion: number;
  readonly questionId: string;
  readonly note: string;
}) {
  return parseJourneyResponse(await sendGuideEvent({ type: "reframe_unmatched", ...input }));
}
