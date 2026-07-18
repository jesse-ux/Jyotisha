import { z } from "zod";
import { evidenceDraftSchema } from "./birth-time-evidence.ts";
import { publicDynamicChoiceQuestionSchema, timeRangeSchema } from "./birth-time-dynamic-choice.ts";
import type { EvidenceDraft } from "./birth-time-evidence.ts";
import type { PublicDynamicChoiceQuestion, TimeRange } from "./birth-time-dynamic-choice.ts";
import type { QuestionSpec } from "./birth-time-question-planner.ts";

const timeSchema = z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/);

export const questionSpecSchema: z.ZodType<QuestionSpec> = z.object({
  questionId: z.string().trim().min(1),
  phase: z.enum(["baseline", "adaptive"]),
  domain: z.enum(["education", "relocation", "relationship", "career", "health_pressure"]),
  requestedPrecision: z.array(z.enum(["day", "month", "year"])).min(1),
  allowUnknown: z.literal(true),
  purposeCode: z.string().trim().min(1),
  plannerVersion: z.string().trim().min(1),
}).strict().readonly();

export const journeyProgressSchema = z.object({
  phase: z.enum(["baseline", "adaptive", "review", "scoring", "result", "ready", "paused"]),
  baselineDomainCount: z.number().int().min(0),
  confirmedEvidenceCount: z.number().int().min(0),
  adaptiveRound: z.number().int().min(0),
  maxAdaptiveRounds: z.literal(3),
}).strict().readonly();

export type JourneyProgress = z.infer<typeof journeyProgressSchema>;

export const journeyPermissionsSchema = z.object({
  canConfirmCandidate: z.boolean(),
}).strict().readonly();

export type JourneyPermissions = z.infer<typeof journeyPermissionsSchema>;

export { evidenceDraftSchema };
export type { EvidenceDraft };

export const nextActionSchema = z.discriminatedUnion("kind", [
  z.object({ kind: z.literal("ask_baseline_evidence"), question: questionSpecSchema }).strict(),
  z.object({ kind: z.literal("ask_adaptive_evidence"), question: questionSpecSchema }).strict(),
  z.object({ kind: z.literal("review_evidence_draft"), draftId: z.string().uuid() }).strict(),
  z.object({ kind: z.literal("score_pending"), jobId: z.string().uuid() }).strict(),
  z.object({ kind: z.literal("retry_scoring"), jobId: z.string().uuid() }).strict(),
  z.object({ kind: z.literal("present_low_result"), resultId: z.string().uuid().nullable() }).strict(),
  z.object({ kind: z.literal("present_medium_result"), resultId: z.string().uuid() }).strict(),
  z.object({ kind: z.literal("candidate_saved"), resultId: z.string().uuid() }).strict(),
  z.object({ kind: z.literal("request_candidate_confirmation"), resultId: z.string().uuid() }).strict(),
  z.object({ kind: z.literal("ready"), activeTime: timeSchema }).strict(),
  z.object({ kind: z.literal("paused") }).strict(),
]).readonly();

export type NextAction = z.infer<typeof nextActionSchema>;

export const dynamicNextActionSchema = z.discriminatedUnion("kind", [
  z.object({ kind: z.literal("generate_dynamic_question") }).strict(),
  z.object({ kind: z.literal("ask_dynamic_choice"), question: publicDynamicChoiceQuestionSchema }).strict(),
  z.object({ kind: z.literal("clarify_unmatched_answer"), questionId: z.string().trim().min(1) }).strict(),
  z.object({ kind: z.literal("retry_question_generation") }).strict(),
  z.object({ kind: z.literal("score_pending"), jobId: z.string().trim().min(1) }).strict(),
  z.object({ kind: z.literal("retry_scoring"), jobId: z.string().trim().min(1) }).strict(),
  z.object({ kind: z.literal("present_low_result"), resultId: z.string().trim().min(1).nullable() }).strict(),
  z.object({ kind: z.literal("present_medium_result"), resultId: z.string().trim().min(1) }).strict(),
  z.object({ kind: z.literal("request_candidate_confirmation"), resultId: z.string().trim().min(1) }).strict(),
  z.object({ kind: z.literal("ready"), activeTime: timeSchema }).strict(),
  z.object({ kind: z.literal("paused") }).strict(),
]).readonly();

export type DynamicNextAction = z.infer<typeof dynamicNextActionSchema>;

export const dynamicJourneyProgressSchema = z.object({
  phase: z.enum(["question", "clarification", "scoring", "result", "ready", "paused"]),
  answeredCount: z.number().int().min(0),
  effectiveAnswerCount: z.number().int().min(0),
  currentRange: timeRangeSchema,
  previousRange: timeRangeSchema.nullable(),
  plateauCount: z.number().int().min(0),
}).strict().readonly();

export type DynamicJourneyProgress = z.infer<typeof dynamicJourneyProgressSchema>;

export type { PublicDynamicChoiceQuestion, TimeRange };

export const journeyTurnStateSchema = z.object({
  turnVersion: z.number().int().nonnegative(),
  nextAction: nextActionSchema,
  progress: journeyProgressSchema,
  permissions: journeyPermissionsSchema,
  evidenceDraft: evidenceDraftSchema.nullable(),
}).strict().readonly();

export type JourneyTurnState = z.infer<typeof journeyTurnStateSchema>;
