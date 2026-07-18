import { z } from "zod";
import { candidateResultSchema, journeySnapshotSchema, lifeEventSchema } from "./birth-time-journey.ts";
import { deriveJourneyPermissions, evidenceDraftSchema, journeyPermissionsSchema, journeyProgressSchema, nextActionSchema } from "./birth-time-journey-turn.ts";
import type { NextAction } from "./birth-time-journey-turn.ts";

export const answerSchema = z.enum(["A", "B", "C", "D"]);
const rectificationQuestionSchema = z.object({
  id: z.string(), prompt: z.string(), round: z.number().int().min(1).optional(),
  options: z.array(z.object({ key: answerSchema, label: z.string() }).strict().readonly()).readonly().optional(),
}).strict().readonly();
const candidateVargaSampleSchema = z.object({
  ascendantSign: z.string().nullable(), d4Sign: z.string().nullable(), d9Sign: z.string().nullable(),
  d10Sign: z.string().nullable(), d24Sign: z.string().nullable(), d30Sign: z.string().nullable(),
}).strict().readonly();
export const questionnaireSchema = z.object({
  questions: z.array(rectificationQuestionSchema).readonly(), samples: z.array(candidateVargaSampleSchema).readonly(), raw: z.record(z.unknown()).readonly(),
}).strict().readonly();
export const scoringFields = {
  answeredCount: z.number().int().min(0),
  candidateClusterRankings: z.array(z.object({ cluster: z.string(), score: z.number() }).strict().readonly()).readonly(),
  raw: z.record(z.unknown()).readonly(),
} as const;
const versionedScoringSchema = z.object({
  ...scoringFields, nextRound: z.number().int().min(1).nullable(), nextRoundQuestions: z.array(rectificationQuestionSchema).readonly(),
}).strict().readonly();
export const responseCore = { caseId: z.string().uuid(), snapshot: journeySnapshotSchema, questionnaire: questionnaireSchema.nullable() } as const;

export class JourneyResponseInvariantError extends Error {
  readonly name = "JourneyResponseInvariantError";
}

function assertNever(value: never): never {
  throw new JourneyResponseInvariantError(`Unexpected journey action: ${String(value)}`);
}

function resultActionId(action: NextAction): string | null | undefined {
  switch (action.kind) {
    case "present_low_result": case "present_medium_result": case "candidate_saved": case "request_candidate_confirmation": return action.resultId;
    case "ask_baseline_evidence": case "ask_adaptive_evidence": case "review_evidence_draft": case "score_pending":
    case "retry_scoring": case "ready": case "paused": return undefined;
    default: return assertNever(action);
  }
}

function actionMatchesProgress(value: {
  readonly nextAction: NextAction;
  readonly progress: z.infer<typeof journeyProgressSchema>;
  readonly candidateResult: z.infer<typeof candidateResultSchema> | null;
  readonly snapshot: z.infer<typeof journeySnapshotSchema>;
  readonly evidenceDraft: z.infer<typeof evidenceDraftSchema> | null;
}): boolean {
  switch (value.nextAction.kind) {
    case "ask_baseline_evidence":
      return value.progress.phase === "baseline" && (value.progress.confirmedEvidenceCount < 3 || value.progress.baselineDomainCount < 2) && value.nextAction.question.phase === "baseline" && value.candidateResult === null && (value.snapshot.state === "rectifying" || value.snapshot.state === "candidate") && value.snapshot.input === "rectification_questions" && value.snapshot.route === "rectification";
    case "ask_adaptive_evidence":
      return value.progress.phase === "adaptive" && value.progress.adaptiveRound >= 1 && value.progress.adaptiveRound <= value.progress.maxAdaptiveRounds && value.nextAction.question.phase === "adaptive" && value.candidateResult?.confidence === "low" && value.snapshot.state === "rectifying" && value.snapshot.route === "rectification";
    case "review_evidence_draft": return value.progress.phase === "review" && value.snapshot.input === "life_events" && value.evidenceDraft?.draftId === value.nextAction.draftId;
    case "score_pending": case "retry_scoring": return value.progress.phase === "scoring" && value.snapshot.route === "rectification";
    case "present_low_result": return value.progress.phase === "result"
      ? (value.candidateResult === null || value.candidateResult.confidence === "low") && value.snapshot.state === "candidate"
      : value.progress.phase === "adaptive" && value.progress.adaptiveRound >= value.progress.maxAdaptiveRounds && value.candidateResult?.confidence === "low";
    case "present_medium_result": return value.progress.phase === "result" && value.candidateResult?.confidence === "medium" && value.snapshot.state === "candidate";
    case "candidate_saved": return value.progress.phase === "result" && value.candidateResult?.confidence === "medium" && value.snapshot.state === "candidate";
    case "request_candidate_confirmation": return value.progress.phase === "result" && value.candidateResult?.confidence === "high" && value.snapshot.state === "confirming";
    case "ready": return value.progress.phase === "ready" && value.snapshot.state === "ready" && value.snapshot.route === "direct_chart";
    case "paused": return value.progress.phase === "paused" && value.snapshot.state !== "ready";
    default: return assertNever(value.nextAction);
  }
}

const versionedJourneyResponseSchema = z.object({
  ...responseCore, scoring: versionedScoringSchema.nullable(), answers: z.record(answerSchema).readonly(), lifeEvents: z.array(lifeEventSchema).readonly(), candidateResult: candidateResultSchema.nullable(),
  turnVersion: z.number().int().nonnegative(), nextAction: nextActionSchema, progress: journeyProgressSchema, permissions: journeyPermissionsSchema, evidenceDraft: evidenceDraftSchema.nullable(),
}).strict().superRefine((value, context) => {
  const confirmedTime = value.snapshot.state === "ready" ? value.snapshot.activeTime : null;
  const expectedPermissions = deriveJourneyPermissions(value.candidateResult, confirmedTime);
  const guardedConfirmation = value.snapshot.state === "confirming" && value.snapshot.input === "candidate_confirmation" && value.snapshot.confidence === "high" && value.snapshot.activeTime === null && value.candidateResult?.confidence === "high" && value.candidateResult.winningSegment !== null;
  if (value.snapshot.route === "direct_chart" && value.snapshot.activeTime === null) context.addIssue({ code: z.ZodIssueCode.custom, path: ["snapshot", "activeTime"], message: "direct chart requires an active time" });
  if (value.snapshot.route === "rectification" && value.snapshot.canApply && !guardedConfirmation) context.addIssue({ code: z.ZodIssueCode.custom, path: ["snapshot", "canApply"], message: "rectification application requires guarded candidate confirmation" });
  if (value.permissions.canConfirmCandidate !== expectedPermissions.canConfirmCandidate) context.addIssue({ code: z.ZodIssueCode.custom, path: ["permissions", "canConfirmCandidate"], message: "candidate confirmation permission must be derived from the scored result" });
  const actionResult = resultActionId(value.nextAction);
  if (actionResult !== undefined && actionResult !== (value.candidateResult?.resultId ?? null)) context.addIssue({ code: z.ZodIssueCode.custom, path: ["nextAction", "resultId"], message: "result actions must reference the current candidate result" });
  if (!actionMatchesProgress(value)) context.addIssue({ code: z.ZodIssueCode.custom, path: ["progress", "phase"], message: "journey action must agree with deterministic progress and snapshot" });
  if (value.nextAction.kind === "request_candidate_confirmation" && (!guardedConfirmation || !value.permissions.canConfirmCandidate)) context.addIssue({ code: z.ZodIssueCode.custom, path: ["nextAction"], message: "candidate confirmation requires the derived confirmation permission" });
  if (value.nextAction.kind === "ready") {
    const candidateAllowsTime = value.candidateResult === null ? value.snapshot.route === "direct_chart" : value.candidateResult.confidence === "high" && value.candidateResult.winningSegment?.representativeTime === value.nextAction.activeTime;
    if (value.snapshot.activeTime !== value.nextAction.activeTime || !candidateAllowsTime) context.addIssue({ code: z.ZodIssueCode.custom, path: ["nextAction", "activeTime"], message: "ready action must match a confirmed snapshot and eligible candidate" });
  }
}).readonly();

export type JourneyClientResponse = z.infer<typeof versionedJourneyResponseSchema>;
export type JourneyAnswer = z.infer<typeof answerSchema>;

export function parseVersionedJourneyResponse(value: unknown): JourneyClientResponse {
  return versionedJourneyResponseSchema.parse(value);
}
