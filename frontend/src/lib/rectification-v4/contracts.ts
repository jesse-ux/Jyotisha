import { z } from "zod";

export const rectificationV4Protocol = "rectification-evidence-v4" as const;
export const rectificationV4AlgorithmVersion = "rectification-v4-range-scoring-1" as const;

export const rectificationV4CaseStatusSchema = z.enum([
  "awaiting_answer",
  "processing",
  "range_ready",
  "paused",
  "abandoned",
]);
export type RectificationV4CaseStatus = z.infer<typeof rectificationV4CaseStatusSchema>;

export const rectificationV4PhaseSchema = z.enum([
  "collecting_evidence",
  "extracting_evidence",
  "scoring_candidates",
  "checking_robustness",
  "planning_question",
  "complete",
]);
export type RectificationV4Phase = z.infer<typeof rectificationV4PhaseSchema>;

export const evidenceDomainSchema = z.enum([
  "education",
  "relocation",
  "relationship",
  "career",
  "finance",
  "health_pressure",
  "family",
  "other",
]);
export type EvidenceDomain = z.infer<typeof evidenceDomainSchema>;

export const eventKindSchema = z.enum([
  "education_milestone",
  "relocation",
  "relationship_start",
  "relationship_end",
  "career_change",
  "finance_change",
  "health_event",
  "family_event",
  "other",
]);
export type EventKind = z.infer<typeof eventKindSchema>;

export const datePrecisionSchema = z.enum(["day", "month", "quarter", "year", "range"]);
export type DatePrecision = z.infer<typeof datePrecisionSchema>;

export const calendarDateSchema = z.string().regex(/^\d{4}-\d{2}-\d{2}$/);
export const clockTimeSchema = z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/);

export const eventDateRangeSchema = z.object({
  start: calendarDateSchema,
  end: calendarDateSchema,
  precision: datePrecisionSchema,
  label: z.string().trim().min(1).max(80),
}).strict().superRefine((value, context) => {
  if (value.start > value.end) {
    context.addIssue({ code: "custom", message: "event date range start must not exceed end" });
  }
});
export type EventDateRange = z.infer<typeof eventDateRangeSchema>;

export const scoreabilitySchema = z.enum(["scoreable", "context_only"]);
export type Scoreability = z.infer<typeof scoreabilitySchema>;

export const lifeEventRevisionSchema = z.object({
  id: z.string().uuid(),
  eventId: z.string().uuid(),
  revision: z.number().int().positive(),
  domain: evidenceDomainSchema,
  eventKind: eventKindSchema,
  summary: z.string().trim().min(1).max(1_000),
  rawText: z.string().trim().min(1).max(4_000),
  dateRange: eventDateRangeSchema,
  scoreability: scoreabilitySchema,
  supersedesRevisionId: z.string().uuid().nullable(),
  createdAt: z.string().datetime({ offset: true }),
}).strict();
export type LifeEventRevision = z.infer<typeof lifeEventRevisionSchema>;

export const calculationSpecSchema = z.object({
  version: z.literal("rectification-calculation-spec-v4"),
  birthDate: calendarDateSchema,
  candidateRange: z.object({ start: clockTimeSchema, end: clockTimeSchema }).strict(),
  latitude: z.number().finite().min(-90).max(90),
  longitude: z.number().finite().min(-180).max(180),
  timezoneOffsetHours: z.number().finite().min(-14).max(14),
  ayanamsa: z.literal("lahiri"),
  nodeMode: z.literal("mean"),
  minuteStep: z.literal(1),
}).strict();
export type CalculationSpec = z.infer<typeof calculationSpecSchema>;

export const candidateMinuteSchema = z.object({
  time: clockTimeSchema,
  score: z.number().finite(),
  supportingEventIds: z.array(z.string().uuid()),
  conflictingEventIds: z.array(z.string().uuid()),
}).strict();
export type CandidateMinute = z.infer<typeof candidateMinuteSchema>;

export const candidateClusterSchema = z.object({
  rank: z.number().int().positive(),
  startTime: clockTimeSchema,
  endTime: clockTimeSchema,
  representativeTime: clockTimeSchema,
  widthMinutes: z.number().int().positive(),
  peakScore: z.number().finite(),
  scoreMass: z.number().finite().nonnegative(),
}).strict();
export type CandidateCluster = z.infer<typeof candidateClusterSchema>;

export const robustnessSchema = z.object({
  neighborSupportMinutes: z.number().int().nonnegative(),
  leaveOneOutRetentionRate: z.number().finite().min(0).max(1),
  dateSensitivityRetentionRate: z.number().finite().min(0).max(1),
  calculationSpecHashMatched: z.boolean(),
}).strict();
export type Robustness = z.infer<typeof robustnessSchema>;

export const candidateSnapshotSchema = z.object({
  id: z.string().uuid(),
  caseId: z.string().uuid(),
  caseVersion: z.number().int().nonnegative(),
  evidenceSetHash: z.string().regex(/^[a-f0-9]{64}$/),
  calculationSpecHash: z.string().regex(/^[a-f0-9]{64}$/),
  algorithmVersion: z.literal(rectificationV4AlgorithmVersion),
  candidates: z.array(candidateMinuteSchema).min(1).max(1_440),
  clusters: z.array(candidateClusterSchema).max(20),
  robustness: robustnessSchema,
  canConfirmExactMinute: z.literal(false),
  canAcceptRange: z.boolean(),
  gateReasons: z.array(z.string().trim().min(1).max(120)).max(20),
  createdAt: z.string().datetime({ offset: true }),
}).strict();
export type CandidateSnapshot = z.infer<typeof candidateSnapshotSchema>;

export const rectificationV4QuestionSchema = z.object({
  id: z.string().uuid(),
  domain: evidenceDomainSchema,
  targetEventId: z.string().uuid().nullable(),
  prompt: z.string().trim().min(1).max(1_000),
  recallCost: z.enum(["low", "medium", "high"]),
  reason: z.string().trim().min(1).max(240),
}).strict();
export type RectificationV4Question = z.infer<typeof rectificationV4QuestionSchema>;

export const rectificationV4TurnSchema = z.object({
  id: z.string().uuid(),
  caseId: z.string().uuid(),
  caseVersion: z.number().int().positive(),
  questionId: z.string().uuid().nullable(),
  questionDomain: evidenceDomainSchema.nullable(),
  questionTargetEventId: z.string().uuid().nullable(),
  question: z.string().trim().min(1).max(1_000),
  answer: z.string().max(4_000),
  modelId: z.string().trim().min(1).max(120).nullable(),
  actionId: z.string().uuid(),
  createdAt: z.string().datetime({ offset: true }),
}).strict();
export type RectificationV4Turn = z.infer<typeof rectificationV4TurnSchema>;

export const rectificationV4CaseSchema = z.object({
  id: z.string().uuid(),
  userId: z.string().uuid(),
  protocol: z.literal(rectificationV4Protocol),
  version: z.number().int().nonnegative(),
  status: rectificationV4CaseStatusSchema,
  phase: rectificationV4PhaseSchema,
  calculationSpec: calculationSpecSchema,
  calculationSpecHash: z.string().regex(/^[a-f0-9]{64}$/),
  evidenceSetHash: z.string().regex(/^[a-f0-9]{64}$/),
  currentQuestion: rectificationV4QuestionSchema.nullable(),
  latestSnapshot: candidateSnapshotSchema.nullable(),
  acceptedRange: z.object({ start: clockTimeSchema, end: clockTimeSchema }).strict().nullable(),
  createdAt: z.string().datetime({ offset: true }),
  updatedAt: z.string().datetime({ offset: true }),
}).strict();
export type RectificationV4Case = z.infer<typeof rectificationV4CaseSchema>;

export const createCaseRequestSchema = z.object({
  actionId: z.string().uuid(),
  uncertaintyMinutes: z.number().int().min(5).max(720).optional(),
}).strict();

export const answerRequestSchema = z.object({
  actionId: z.string().uuid(),
  expectedCaseVersion: z.number().int().nonnegative(),
  answer: z.string().trim().min(1).max(4_000),
  modelId: z.string().trim().min(1).max(120).nullable().optional(),
}).strict();

export const reviseEventRequestSchema = z.object({
  actionId: z.string().uuid(),
  expectedCaseVersion: z.number().int().nonnegative(),
  domain: evidenceDomainSchema,
  eventKind: eventKindSchema,
  summary: z.string().trim().min(1).max(1_000),
  rawText: z.string().trim().min(1).max(4_000),
  dateRange: eventDateRangeSchema,
  scoreability: scoreabilitySchema.optional(),
}).strict();

export const caseActionRequestSchema = z.object({
  actionId: z.string().uuid(),
  expectedCaseVersion: z.number().int().nonnegative(),
}).strict();

export const acceptRangeRequestSchema = caseActionRequestSchema.extend({
  startTime: clockTimeSchema,
  endTime: clockTimeSchema,
}).strict();

export const rectificationV4JobSchema = z.object({
  id: z.string().uuid(),
  caseId: z.string().uuid(),
  status: z.enum(["pending", "processing", "completed", "failed", "stale"]),
  phase: rectificationV4PhaseSchema,
  expectedCaseVersion: z.number().int().nonnegative(),
  evidenceSetHash: z.string().regex(/^[a-f0-9]{64}$/),
  calculationSpecHash: z.string().regex(/^[a-f0-9]{64}$/),
  errorCode: z.string().trim().min(1).max(120).nullable(),
  createdAt: z.string().datetime({ offset: true }),
  updatedAt: z.string().datetime({ offset: true }),
}).strict();
export type RectificationV4Job = z.infer<typeof rectificationV4JobSchema>;

export const rectificationV4ApiResponseSchema = z.object({
  case: rectificationV4CaseSchema,
  job: rectificationV4JobSchema.nullable(),
  events: z.array(lifeEventRevisionSchema),
  turns: z.array(rectificationV4TurnSchema),
}).strict();
export type RectificationV4ApiResponse = z.infer<typeof rectificationV4ApiResponseSchema>;

export const rectificationV4HandoffStatusSchema = z.enum([
  "pending",
  "claimed",
  "in_progress",
  "consumed",
]);

export const rectificationV4HandoffSchema = z.object({
  protocol: z.literal(rectificationV4Protocol),
  caseId: z.string().uuid(),
  caseVersion: z.number().int().nonnegative(),
  question: z.string().trim().min(1).max(500),
  questionFingerprint: z.string().regex(/^[0-9a-f]{64}$/),
  requestId: z.string().uuid(),
  status: rectificationV4HandoffStatusSchema,
  acceptedRange: z.object({ start: clockTimeSchema, end: clockTimeSchema }).strict().nullable(),
}).strict();
export type RectificationV4Handoff = z.infer<typeof rectificationV4HandoffSchema>;
