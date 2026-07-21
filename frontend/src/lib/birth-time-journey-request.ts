import { z } from "zod";
import { lifeEventSchema } from "./birth-time-journey.ts";

const caseIdSchema = z.string().uuid();
const actionIdSchema = z.string().uuid();
const turnVersionSchema = z.number().int().nonnegative();
const mutationFields = {
  caseId: caseIdSchema,
  actionId: actionIdSchema,
  turnVersion: turnVersionSchema,
} as const;
const revisionValidationId = "00000000-0000-4000-8000-000000000000";
const publicChoiceFields = {
  ...mutationFields,
  questionId: z.string().uuid(),
  optionId: z.string().uuid(),
} as const;

export const birthTimeJourneyRequestSchema = z.discriminatedUnion("type", [
  z.object({ type: z.literal("assess") }).strict(),
  z.object({ type: z.literal("resume"), caseId: caseIdSchema }).strict(),
  z.object({
    type: z.literal("poll_scoring"),
    caseId: caseIdSchema,
    jobId: z.string().uuid(),
  }).strict(),
  z.object({
    type: z.literal("answer_question"),
    caseId: caseIdSchema,
    questionId: z.string().trim().min(1).max(120),
    answer: z.enum(["A", "B", "C", "D"]),
  }).strict(),
  z.object({
    type: z.literal("submit_life_events"),
    caseId: caseIdSchema,
    events: z.array(lifeEventSchema).min(3).max(6).readonly(),
  }).strict(),
  z.object({
    type: z.literal("save_candidate"),
    caseId: caseIdSchema,
    resultId: z.string().uuid(),
  }).strict(),
  z.object({
    type: z.literal("confirm_candidate"),
    caseId: caseIdSchema,
    resultId: z.string().uuid(),
    time: z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/),
  }).strict(),
  z.object({
    type: z.literal("confirm_evidence_draft"),
    ...mutationFields,
    draftId: z.string().uuid(),
  }).strict(),
  z.object({ type: z.literal("skip_evidence_question"), ...mutationFields }).strict(),
  z.object({ type: z.literal("pause_rectification"), ...mutationFields }).strict(),
  z.object({ type: z.literal("finish_rectification"), ...mutationFields }).strict(),
  z.object({ type: z.literal("answer_dynamic_choice"), ...publicChoiceFields }).strict(),
  z.object({
    type: z.literal("revise_evidence_draft"),
    ...mutationFields,
    precision: z.enum(["year", "month", "day"]),
    date: z.string().trim().min(4).max(10),
  }).strict(),
  z.object({
    type: z.literal("save_guided_candidate"),
    ...mutationFields,
    resultId: z.string().uuid(),
  }).strict(),
  z.object({
    type: z.literal("confirm_guided_candidate"),
    ...mutationFields,
    resultId: z.string().uuid(),
    time: z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/),
  }).strict(),
  z.object({
    type: z.literal("confirm_dynamic_candidate"),
    ...mutationFields,
    resultId: z.string().uuid(),
    time: z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/),
  }).strict(),
]).superRefine((value, context) => {
  if (value.type === "revise_evidence_draft" && !lifeEventSchema.safeParse({
    id: revisionValidationId,
    domain: "education",
    precision: value.precision,
    date: value.date,
  }).success) {
    context.addIssue({
      code: z.ZodIssueCode.custom,
      path: ["date"],
      message: "evidence date must match its precision",
    });
  }
}).readonly();

export type BirthTimeJourneyRequest = z.infer<typeof birthTimeJourneyRequestSchema>;
