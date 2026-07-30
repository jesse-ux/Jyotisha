import { z } from "zod";

export const rectificationV4Protocol = "rectification-evidence-v4" as const;
export const rectificationAgentV5Protocol = "rectification-evidence-v5" as const;
export const rectificationDeploymentModeSchema = z.enum(["v4_legacy", "v5_shadow", "v5_agent"]);
export type RectificationDeploymentMode = z.infer<typeof rectificationDeploymentModeSchema>;
export const rectificationV4AlgorithmVersion = "rectification-v5-matrix-scoring-1" as const;

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
  "reasoning",
  "rendering",
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
  "self_health_event",
  "family_health_event",
  "family_bereavement",
  "relationship_change",
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

export const eventSubjectSchema = z.enum(["self", "family", "partner", "other"]);
export type EventSubject = z.infer<typeof eventSubjectSchema>;

export const relatedPersonSchema = z.enum(["father", "mother", "grandparent", "sibling", "partner"]);
export type RelatedPerson = z.infer<typeof relatedPersonSchema>;

export const scoreabilitySchema = z.enum(["scoreable", "context_only", "pending_review", "unsupported"]);
export type Scoreability = z.infer<typeof scoreabilitySchema>;

const eventDateProvenanceFields = {
  dateSource: z.string().trim().min(1).max(120).nullable().optional(),
  dateReliability: z.string().trim().min(1).max(120).nullable().optional(),
  dateCorroboration: z.string().trim().min(1).max(1_000).nullable().optional(),
  dateConflictStatus: z.string().trim().min(1).max(120).nullable().optional(),
} as const;

export const lifeEventRevisionSchema = z.object({
  id: z.string().uuid(),
  eventId: z.string().uuid(),
  revision: z.number().int().positive(),
  domain: evidenceDomainSchema,
  eventKind: eventKindSchema,
  subject: eventSubjectSchema,
  relatedPerson: relatedPersonSchema.nullable(),
  summary: z.string().trim().min(1).max(1_000),
  rawText: z.string().trim().min(1).max(4_000),
  dateRange: eventDateRangeSchema,
  ...eventDateProvenanceFields,
  scoreability: scoreabilitySchema,
  supersedesRevisionId: z.string().uuid().nullable(),
  createdAt: z.string().datetime({ offset: true }),
}).strict();
export type LifeEventRevision = z.infer<typeof lifeEventRevisionSchema>;

export const pendingEvidenceSchema = z.object({
  id: z.string().uuid(),
  caseId: z.string().uuid(),
  turnId: z.string().uuid(),
  rawText: z.string().trim().min(1).max(4_000),
  reasonCode: z.enum(["date_unresolved", "event_unparsed"]),
  targetEventId: z.string().uuid().nullable(),
  resolvedEventId: z.string().uuid().nullable(),
  createdAt: z.string().datetime({ offset: true }),
  resolvedAt: z.string().datetime({ offset: true }).nullable(),
}).strict();
export type PendingEvidence = z.infer<typeof pendingEvidenceSchema>;

export const calculationSpecSchema = z.object({
  version: z.literal("rectification-calculation-spec-v4"),
  birthDate: calendarDateSchema,
  candidateRange: z.object({ start: clockTimeSchema, end: clockTimeSchema }).strict(),
  latitude: z.number().finite().min(-90).max(90),
  longitude: z.number().finite().min(-180).max(180),
  timezoneOffsetHours: z.number().finite().min(-14).max(14),
  birthTimeSource: z.enum([
    "hospital_record",
    "family_exact",
    "approximate",
    "period_only",
    "unknown",
    "legacy_import",
  ]).nullable().optional(),
  timezoneId: z.string().trim().min(1).max(120).nullable().optional(),
  timezoneSource: z.string().trim().min(1).max(80).nullable().optional(),
  localTimeStatus: z.enum(["resolved", "not_provided", "ambiguous", "nonexistent"]).nullable().optional(),
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

const robustnessValueSchema = z.object({
  neighborSupportMinutes: z.number().int().nonnegative(),
  leaveOneOutRetentionRate: z.number().finite().min(0).max(1),
  leaveOneDomainOutRetentionRate: z.number().finite().min(0).max(1),
  dateSensitivityRetentionRate: z.number().finite().min(0).max(1),
  calculationSpecHashMatched: z.boolean(),
}).strict();
export type Robustness = z.infer<typeof robustnessValueSchema>;
export const robustnessSchema: z.ZodType<Robustness> = z.preprocess((value) => {
  if (!value || typeof value !== "object" || Array.isArray(value) || "leaveOneDomainOutRetentionRate" in value) return value;
  return { ...value, leaveOneDomainOutRetentionRate: 0.8 };
}, robustnessValueSchema) as z.ZodType<Robustness>;

const candidateSnapshotBaseSchema = z.object({
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

export type CandidateSnapshot = z.infer<typeof candidateSnapshotBaseSchema>;
export const candidateSnapshotSchema: z.ZodType<CandidateSnapshot> = candidateSnapshotBaseSchema.transform((snapshot) => {
  if (snapshot.robustness.leaveOneDomainOutRetentionRate >= 0.8) return snapshot;
  const reason = "leave_one_domain_out_not_stable";
  return {
    ...snapshot,
    canAcceptRange: false,
    gateReasons: snapshot.gateReasons.includes(reason)
      ? snapshot.gateReasons
      : [...snapshot.gateReasons, reason].slice(0, 20),
  };
});

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
  protocol: z.union([z.literal(rectificationV4Protocol), z.literal(rectificationAgentV5Protocol)]),
  version: z.number().int().nonnegative(),
  status: rectificationV4CaseStatusSchema,
  phase: rectificationV4PhaseSchema,
  calculationSpec: calculationSpecSchema,
  calculationSpecHash: z.string().regex(/^[a-f0-9]{64}$/),
  evidenceSetHash: z.string().regex(/^[a-f0-9]{64}$/),
  currentQuestion: rectificationV4QuestionSchema.nullable(),
  latestSnapshot: candidateSnapshotSchema.nullable(),
  orchestrationModelId: z.string().trim().min(1).max(120).nullable(),
  narrationModelId: z.string().trim().min(1).max(120).nullable(),
  skillVersion: z.string().trim().min(1).max(120),
  promptVersion: z.string().trim().min(1).max(120),
  algorithmVersion: z.string().trim().min(1).max(120),
  deploymentMode: rectificationDeploymentModeSchema,
  agentMode: z.enum(["agent", "deterministic_fallback"]),
  featureSnapshotId: z.string().uuid().nullable(),
  latestDiagnosticsId: z.string().uuid().nullable(),
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
  subject: eventSubjectSchema,
  relatedPerson: relatedPersonSchema.nullable(),
  summary: z.string().trim().min(1).max(1_000),
  rawText: z.string().trim().min(1).max(4_000),
  dateRange: eventDateRangeSchema,
  ...eventDateProvenanceFields,
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

export const rectificationAnalysisStageSchema = z.object({
  phase: z.enum([
    "extracting_evidence",
    "scoring_candidates",
    "checking_robustness",
    "planning_question",
    "reasoning",
    "rendering",
  ]),
  label: z.string().trim().min(1).max(120),
  status: z.enum(["completed", "failed"]),
  durationMs: z.number().int().min(0).max(300_000).nullable(),
}).strict();

export const rectificationAnalysisToolCallSchema = z.object({
  category: z.enum(["candidate_engine", "diagnostic", "agent_diagnostic"]),
  label: z.string().trim().min(1).max(120),
  outcome: z.enum(["succeeded", "failed", "rejected"]),
  durationMs: z.number().int().min(0).max(300_000).nullable(),
}).strict();

export const rectificationAnalysisTraceSchema = z.object({
  status: z.enum(["completed", "failed", "legacy"]),
  stages: z.array(rectificationAnalysisStageSchema).max(12),
  toolCalls: z.array(rectificationAnalysisToolCallSchema).max(16),
  techniques: z.array(z.string().trim().min(1).max(120)).max(24),
  reasoningSummary: z.string().trim().min(1).max(500).nullable(),
  reasoningSource: z.enum(["provider_summary", "none"]),
}).strict();
export type RectificationAnalysisTrace = z.infer<typeof rectificationAnalysisTraceSchema>;

export const rectificationAnalysisItemSchema = z.object({
  sourceTurnId: z.string().uuid(),
  trace: rectificationAnalysisTraceSchema,
}).strict();
export type RectificationAnalysisItem = z.infer<typeof rectificationAnalysisItemSchema>;

export const rectificationV4ApiResponseSchema = z.object({
  case: rectificationV4CaseSchema,
  job: rectificationV4JobSchema.nullable(),
  events: z.array(lifeEventRevisionSchema),
  turns: z.array(rectificationV4TurnSchema),
  analysis: z.array(rectificationAnalysisItemSchema).optional(),
}).strict();
export type RectificationV4ApiResponse = z.infer<typeof rectificationV4ApiResponseSchema>;

export const rectificationV4HandoffStatusSchema = z.enum([
  "pending",
  "claimed",
  "in_progress",
  "consumed",
]);

export const rectificationV4HandoffSchema = z.object({
  protocol: z.union([z.literal(rectificationV4Protocol), z.literal(rectificationAgentV5Protocol)]),
  caseId: z.string().uuid(),
  caseVersion: z.number().int().nonnegative(),
  question: z.string().trim().min(1).max(500),
  questionFingerprint: z.string().regex(/^[0-9a-f]{64}$/),
  requestId: z.string().uuid(),
  status: rectificationV4HandoffStatusSchema,
  acceptedRange: z.object({ start: clockTimeSchema, end: clockTimeSchema }).strict().nullable(),
}).strict();
export type RectificationV4Handoff = z.infer<typeof rectificationV4HandoffSchema>;
