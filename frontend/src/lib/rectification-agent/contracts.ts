import { z } from "zod";
import { clockTimeSchema, eventKindSchema, eventSubjectSchema, evidenceDomainSchema, relatedPersonSchema, rectificationAnalysisTraceSchema, rectificationDeploymentModeSchema } from "../rectification-v4/contracts.ts";

const uuid = z.string().uuid();
const hash = z.string().regex(/^[a-f0-9]{64}$/);
const nonblank = (max: number) => z.string().trim().min(1).max(max);

export const CURRENT_RECTIFICATION_SKILL_VERSION = "birth-time-rectification-v6" as const;
export const CURRENT_RECTIFICATION_PROMPT_VERSION = "rectification-director-v2" as const;

export const rectificationDiagnosticSchema = z.enum([
  "leave_one_event_out",
  "leave_one_domain_out",
  "date_sensitivity",
  "neighbor_stability",
  "candidate_split",
]);
export type RectificationDiagnostic = z.infer<typeof rectificationDiagnosticSchema>;

export const targetDispositionSchema = z.enum([
  "resolved",
  "unknown",
  "declined",
  "direction_change",
  "answered_other_event",
  "unresolved",
  "not_applicable",
]);

export const evidenceProposalSchema = z.object({
  operation: z.enum(["create", "revise", "ignore"]),
  targetEventId: uuid.nullable(),
  sourceSpan: nonblank(4_000),
  dateText: nonblank(80).nullable(),
  proposedSummary: nonblank(1_000),
  proposedDomain: evidenceDomainSchema,
  proposedEventKind: eventKindSchema,
  proposedSubject: eventSubjectSchema,
  proposedRelatedPerson: relatedPersonSchema.nullable(),
  confidence: z.enum(["high", "medium", "low"]),
}).strict();
export type EvidenceProposal = z.infer<typeof evidenceProposalSchema>;

export const rectificationFocusSchema = z.object({
  mode: z.enum([
    "clarify_existing_event",
    "collect_independent_event",
    "pair_related_event",
    "resolve_conflict",
    "distinguish_candidate_clusters",
  ]),
  targetEventId: uuid.nullable(),
  domain: evidenceDomainSchema.nullable(),
  requestedFacts: z.array(z.enum([
    "year",
    "month",
    "day_or_period",
    "subject",
    "event_type",
    "event_stage",
    "independent_event",
    "paired_event",
  ])).max(3),
  rationaleCodes: z.array(nonblank(80)).max(8),
}).strict();
export type RectificationFocus = z.infer<typeof rectificationFocusSchema>;

const directorActionSchema = z.discriminatedUnion("type", [
  z.object({
    type: z.literal("ask_question"),
    focus: rectificationFocusSchema,
    question: nonblank(240),
    optionalQuickReplies: z.array(z.object({ label: nonblank(40), value: nonblank(120) }).strict()).max(4),
  }).strict(),
  z.object({ type: z.literal("request_diagnostic"), diagnostic: rectificationDiagnosticSchema }).strict(),
  z.object({ type: z.literal("offer_candidate_range"), snapshotId: uuid }).strict(),
  z.object({ type: z.literal("stop_low_confidence"), reasonCodes: z.array(nonblank(80)).min(1).max(8) }).strict(),
]);

export const rectificationTurnPlanSchema = z.object({
  contractVersion: z.literal("rectification-turn-plan-v1"),
  targetDisposition: targetDispositionSchema,
  evidenceProposals: z.array(evidenceProposalSchema).max(8),
  action: directorActionSchema,
  publicReply: z.object({
    acknowledgement: nonblank(1_000),
    candidateCommentary: nonblank(1_000).nullable(),
    limitation: nonblank(1_000).nullable(),
  }).strict(),
}).strict();
export type RectificationTurnPlan = z.infer<typeof rectificationTurnPlanSchema>;

export const rectificationCaseDossierSchema = z.object({
  case: z.object({
    candidateWindow: z.object({ start: clockTimeSchema, end: clockTimeSchema }).strict(),
    birthDate: nonblank(10),
    location: z.object({
      latitude: z.number().finite(),
      longitude: z.number().finite(),
      timezoneId: z.string().nullable(),
      timezoneOffsetHours: z.number().finite(),
    }).strict(),
    birthTimeSource: z.string().nullable(),
    algorithmVersion: nonblank(120),
  }).strict(),
  conversation: z.object({
    recentRawTurns: z.array(z.object({ question: z.string(), answer: z.string() }).strict()).max(12),
    earlierConversationSummary: z.string().nullable(),
  }).strict(),
  eventLedger: z.array(z.object({
    eventId: uuid,
    revision: z.number().int().positive(),
    summary: nonblank(1_000),
    rawText: nonblank(4_000),
    domain: evidenceDomainSchema,
    eventKind: eventKindSchema,
    subject: eventSubjectSchema,
    relatedPerson: relatedPersonSchema.nullable(),
    dateRange: z.object({ start: nonblank(10), end: nonblank(10), precision: nonblank(20), label: nonblank(80) }).strict(),
    scoreability: nonblank(40),
    status: z.enum(["active", "superseded", "pending"]),
  }).strict()),
  interviewState: z.object({
    currentTargetEventId: uuid.nullable(),
    declinedDomains: z.array(evidenceDomainSchema),
    unresolvedTargets: z.array(uuid),
    pendingEvidence: z.array(z.object({
      rawText: nonblank(4_000),
      reasonCode: z.enum(["date_unresolved", "event_unparsed"]),
      targetEventId: uuid.nullable(),
      createdAt: z.string().datetime({ offset: true }),
    }).strict()).max(100),
    askedTopics: z.array(z.string()).max(50),
    turnCount: z.number().int().nonnegative(),
    targetDisposition: targetDispositionSchema,
  }).strict(),
  candidateState: z.object({
    hasSnapshot: z.boolean(),
    publicRangeAllowed: z.boolean(),
    rangeChanged: z.boolean(),
    topClusters: z.array(z.object({ rank: z.number().int(), widthMinutes: z.number().int(), stability: z.enum(["stable", "unstable"]) }).strict()).max(4),
    contrasts: z.array(z.object({ techniqueLayers: z.array(z.string()), relevantEventIds: z.array(uuid) }).strict()).max(8),
    eventDiagnostics: z.array(z.object({ eventId: uuid, winnerRetentionRate: z.number(), scoreVariance: z.number() }).strict()).max(100),
    gateReasons: z.array(z.string()).max(20),
    currentSnapshotId: uuid.nullable(),
  }).strict(),
  capabilities: z.object({
    supportedDomains: z.array(evidenceDomainSchema),
    supportedEventKinds: z.array(eventKindSchema),
    maxQuestionsPerTurn: z.literal(1),
    maxDiagnosticsPerRun: z.number().int().min(0).max(2),
    forbiddenPublicClaims: z.array(z.string()),
  }).strict(),
}).strict();
export type RectificationCaseDossier = z.infer<typeof rectificationCaseDossierSchema>;

export const rectificationDecisionSchema = z.union([
  z.object({
    action: z.literal("ask_question"),
    opportunityId: uuid,
    narrativeFocus: z.array(z.enum(["latest_event", "candidate_change", "date_precision", "uncertainty"])).max(3),
  }).strict(),
  z.object({ action: z.literal("ask_question"), focus: rectificationFocusSchema, question: nonblank(240) }).strict(),
  z.object({ action: z.literal("run_diagnostic"), diagnostic: rectificationDiagnosticSchema }).strict(),
  z.object({ action: z.literal("offer_candidate_range"), snapshotId: uuid }).strict(),
  z.object({ action: z.literal("stop_low_confidence"), reasonCodes: z.array(nonblank(80)).min(1).max(8) }).strict(),
]);
export type RectificationDecision = z.infer<typeof rectificationDecisionSchema>;

export const semanticQuestionKindSchema = z.enum([
  "clarify_intake",
  "clarify_event_subject",
  "refine_event_date",
  "pair_related_event",
  "ask_new_event",
  "resolve_event_conflict",
  "disambiguate_candidate_split",
]);
export type SemanticQuestionKind = z.infer<typeof semanticQuestionKindSchema>;

export const requestedQuestionFieldSchema = z.enum([
  "event_year",
  "event_month",
  "event_day",
  "event_range",
  "event_subject",
  "event_stage",
  "new_dated_event",
]);
export type RequestedQuestionField = z.infer<typeof requestedQuestionFieldSchema>;

export const forbiddenQuestionMoveSchema = z.enum([
  "switch_target_event",
  "ask_multiple_questions",
  "claim_exact_birth_minute",
  "invent_event",
  "invent_date",
  "expose_private_score",
  "expose_internal_id",
  "expose_technique_trace",
]);
export type ForbiddenQuestionMove = z.infer<typeof forbiddenQuestionMoveSchema>;

const opportunityMetrics = {
  expectedInformationGain: z.number().finite().min(0).max(1),
  dateSensitivity: z.number().finite().min(0).max(1),
  candidateSplitRelevance: z.number().finite().min(0).max(1),
  domainCoverageGain: z.number().finite().min(0).max(1),
  recallEase: z.number().finite().min(0).max(1),
  novelty: z.number().finite().min(0).max(1),
  repetitionPenalty: z.number().finite().min(0).max(1),
  privacyCost: z.number().finite().min(0).max(1),
  utility: z.number().finite(),
  active: z.boolean(),
} as const;

export const semanticQuestionOpportunitySchema = z.object({
  contractVersion: z.literal("semantic-question-v2"),
  opportunityId: uuid,
  kind: semanticQuestionKindSchema,
  domain: evidenceDomainSchema,
  targetEventId: uuid.nullable(),
  goal: nonblank(500),
  requestedFields: z.array(requestedQuestionFieldSchema).min(1).max(4),
  anchors: z.array(nonblank(240)).max(8),
  contextFacts: z.array(nonblank(500)).max(16),
  forbiddenMoves: z.array(forbiddenQuestionMoveSchema).min(1).max(8),
  fallbackPrompt: nonblank(1_000),
  reason: nonblank(500),
  ...opportunityMetrics,
}).strict();
export type SemanticQuestionOpportunity = z.infer<typeof semanticQuestionOpportunitySchema>;

const legacyQuestionOpportunitySchema = z.object({ prompt: nonblank(1_000) }).passthrough();

function legacyUuid(value: string): string {
  let hashValue = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hashValue ^= value.charCodeAt(index);
    hashValue = Math.imul(hashValue, 16777619);
  }
  const block = (hashValue >>> 0).toString(16).padStart(8, "0");
  return `${block}-${block.slice(0, 4)}-4${block.slice(1, 4)}-8${block.slice(1, 4)}-${block}${block.slice(0, 4)}`;
}

const defaultForbiddenMoves: SemanticQuestionOpportunity["forbiddenMoves"] = [
  "switch_target_event",
  "ask_multiple_questions",
  "claim_exact_birth_minute",
  "invent_event",
  "invent_date",
  "expose_private_score",
  "expose_internal_id",
  "expose_technique_trace",
];

function numberFrom(value: unknown, fallback: number): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function requestedFieldsFor(kind: SemanticQuestionKind): SemanticQuestionOpportunity["requestedFields"] {
  if (kind === "clarify_event_subject") return ["event_subject"];
  if (kind === "refine_event_date") return ["event_month"];
  if (kind === "disambiguate_candidate_split") return ["event_stage"];
  if (kind === "ask_new_event" || kind === "pair_related_event") return ["new_dated_event"];
  return ["event_range"];
}

export function normalizeQuestionOpportunity(value: unknown): SemanticQuestionOpportunity {
  const semantic = semanticQuestionOpportunitySchema.safeParse(value);
  if (semantic.success) return semantic.data;
  const legacy = legacyQuestionOpportunitySchema.parse(value) as Record<string, unknown> & { prompt: string };
  const kind = semanticQuestionKindSchema.safeParse(legacy.kind).success
    ? semanticQuestionKindSchema.parse(legacy.kind)
    : "clarify_intake";
  const domain = evidenceDomainSchema.safeParse(legacy.domain).success
    ? evidenceDomainSchema.parse(legacy.domain)
    : "other";
  const targetEventId = uuid.safeParse(legacy.targetEventId).success ? uuid.parse(legacy.targetEventId) : null;
  const reason = typeof legacy.reason === "string" && legacy.reason.trim() ? legacy.reason.trim().slice(0, 500) : "历史问题机会兼容读取。";
  return semanticQuestionOpportunitySchema.parse({
    contractVersion: "semantic-question-v2",
    opportunityId: uuid.safeParse(legacy.opportunityId).success ? legacy.opportunityId : legacyUuid(legacy.prompt),
    kind,
    domain,
    targetEventId,
    goal: reason,
    requestedFields: requestedFieldsFor(kind),
    anchors: [],
    contextFacts: [],
    forbiddenMoves: defaultForbiddenMoves,
    fallbackPrompt: legacy.prompt,
    reason,
    expectedInformationGain: numberFrom(legacy.expectedInformationGain, .5),
    dateSensitivity: numberFrom(legacy.dateSensitivity, .5),
    candidateSplitRelevance: numberFrom(legacy.candidateSplitRelevance, .5),
    domainCoverageGain: numberFrom(legacy.domainCoverageGain, 0),
    recallEase: numberFrom(legacy.recallEase, .5),
    novelty: numberFrom(legacy.novelty, .5),
    repetitionPenalty: numberFrom(legacy.repetitionPenalty, 0),
    privacyCost: numberFrom(legacy.privacyCost, 0),
    utility: numberFrom(legacy.utility, .5),
    active: typeof legacy.active === "boolean" ? legacy.active : true,
  });
}

export const questionOpportunitySchema = z.union([
  semanticQuestionOpportunitySchema,
  legacyQuestionOpportunitySchema,
]).transform(normalizeQuestionOpportunity);
export type QuestionOpportunity = z.output<typeof questionOpportunitySchema>;

export const eventDateSensitivitySchema = z.object({
  eventId: uuid,
  declaredDateRange: z.object({ start: nonblank(10), end: nonblank(10), precision: nonblank(20) }).strict(),
  sampleDates: z.array(nonblank(10)).min(1).max(12),
  winnerRetentionRate: z.number().finite().min(0).max(1),
  scoreVariance: z.number().finite().nonnegative(),
  candidateClusterRetentionRate: z.number().finite().min(0).max(1),
}).strict();

export const candidateSplitSchema = z.object({
  leftCluster: z.object({ start: clockTimeSchema, end: clockTimeSchema }).strict(),
  rightCluster: z.object({ start: clockTimeSchema, end: clockTimeSchema }).strict(),
  techniqueLayers: z.array(nonblank(80)).max(40),
  eventIds: z.array(uuid).max(100),
}).strict();

export const vedAstroCandidateMetricSchema = z.object({
  role: z.enum(["primary", "runner_up"]),
  requestedEventCount: z.number().int().nonnegative().max(20),
  successfulEventCount: z.number().int().nonnegative().max(20),
  matchedEventCount: z.number().int().nonnegative().max(20),
  eventHitCount: z.number().int().nonnegative(),
  signalLift: z.number().finite(),
}).strict();

export const vedAstroPostValidationSchema = z.object({
  contractVersion: z.literal("vedastro-post-validation-v1"),
  provider: z.literal("vedastro_official"),
  status: z.enum(["pass", "blocked", "not_validated"]),
  providerStatus: nonblank(80),
  blockers: z.array(nonblank(120)).max(20),
  primaryCandidateTime: clockTimeSchema.nullable(),
  runnerUpCandidateTime: clockTimeSchema.nullable(),
  eligibleEventCount: z.number().int().nonnegative().max(100),
  selectedEventCount: z.number().int().nonnegative().max(20),
  unsupportedEventCount: z.number().int().nonnegative().max(100),
  candidateMetrics: z.array(vedAstroCandidateMetricSchema).max(2),
  minuteSensitiveValidation: z.object({
    comparisonReady: z.boolean(),
    discriminated: z.boolean(),
    discriminatedLayers: z.array(nonblank(80)).max(10),
  }).strict(),
  validationHash: hash,
  validatedAt: z.string().datetime({ offset: true }),
  canConfirmExactMinute: z.literal(false),
}).strict();
export type VedAstroPostValidation = z.infer<typeof vedAstroPostValidationSchema>;

export const diagnosticsSummarySchema = z.object({
  id: uuid,
  caseId: uuid,
  snapshotId: uuid,
  primaryClusterRetentionRate: z.number().finite().min(0).max(1),
  leaveOneEventOutRetentionRate: z.number().finite().min(0).max(1),
  leaveOneDomainOutRetentionRate: z.number().finite().min(0).max(1),
  dateSensitivityRetentionRate: z.number().finite().min(0).max(1),
  neighborSupportMinutes: z.number().int().min(0).max(1_440),
  primarySecondaryMarginPercent: z.number().finite().min(0).max(100),
  clusterMassRatio: z.number().finite().min(0).max(1),
  unstableEventIds: z.array(uuid).max(100),
  mostDiscriminatingLayers: z.array(nonblank(80)).max(40),
  eventDateSensitivity: z.array(eventDateSensitivitySchema).max(100),
  candidateSplits: z.array(candidateSplitSchema).max(20),
  externalValidation: vedAstroPostValidationSchema.optional(),
  calculationHash: hash,
  createdAt: z.string().datetime({ offset: true }),
}).strict();
export type DiagnosticsSummary = z.infer<typeof diagnosticsSummarySchema>;

export const candidateFeatureSnapshotSchema = z.object({
  id: uuid,
  caseId: uuid,
  calculationSpecHash: hash,
  algorithmVersion: nonblank(120),
  candidateCount: z.number().int().positive().max(1_440),
  featureHash: hash,
  features: z.array(z.object({
    time: clockTimeSchema,
    ascendantDegree: z.number().finite().min(0).max(360).nullable(),
    ascendantSignIndex: z.number().int().min(0).max(11).nullable(),
    vargaAscendants: z.record(z.string(), z.number().int().min(0).max(11)),
    arudhaSigns: z.object({ A7: z.number().int().min(0).max(11).nullable(), A10: z.number().int().min(0).max(11).nullable(), UL: z.number().int().min(0).max(11).nullable() }).strict(),
    availableLayers: z.array(nonblank(80)).max(80),
    blockedLayers: z.array(nonblank(80)).max(80),
    fingerprints: z.record(z.string(), z.string()),
  }).strict()).max(1_440),
  createdAt: z.string().datetime({ offset: true }),
}).strict();
export type CandidateFeatureSnapshot = z.infer<typeof candidateFeatureSnapshotSchema>;

export const toolCallTraceSchema = z.object({
  tool: nonblank(120),
  diagnostic: rectificationDiagnosticSchema.nullable(),
  outcome: z.enum(["succeeded", "failed", "rejected"]),
  durationMs: z.number().int().min(0).max(300_000),
  errorCode: nonblank(120).nullable(),
}).strict();
export type ToolCallTrace = z.infer<typeof toolCallTraceSchema>;

export const validatedDecisionSchema = z.object({
  decision: rectificationDecisionSchema,
  mode: z.enum(["agent", "deterministic_fallback"]),
  validationIssues: z.array(nonblank(120)).max(20),
  selectedOpportunity: questionOpportunitySchema.nullable(),
}).strict();
export type ValidatedDecision = z.infer<typeof validatedDecisionSchema>;

export const publicMessageSchema = z.object({
  acknowledgement: nonblank(1_000),
  candidateUpdate: nonblank(1_000).nullable(),
  limitation: nonblank(1_000).nullable(),
  question: nonblank(1_000).nullable(),
}).strict();
export type PublicMessage = z.infer<typeof publicMessageSchema>;

export const storedPublicMessageSchema = publicMessageSchema.extend({
  analysisTrace: rectificationAnalysisTraceSchema.optional(),
}).strict();
export type StoredPublicMessage = z.infer<typeof storedPublicMessageSchema>;

export const agentRunSchema = z.object({
  id: uuid,
  caseId: uuid,
  jobId: uuid,
  caseVersion: z.number().int().nonnegative(),
  modelId: nonblank(120).nullable(),
  skillVersion: nonblank(120),
  promptVersion: nonblank(120),
  deploymentSha: nonblank(80).nullable(),
  deploymentMode: rectificationDeploymentModeSchema,
  decision: rectificationDecisionSchema.nullable(),
  validatedDecision: validatedDecisionSchema,
  toolCalls: z.array(toolCallTraceSchema).max(8),
  fallbackReason: nonblank(120).nullable(),
  inputTokenCount: z.number().int().nonnegative().nullable(),
  outputTokenCount: z.number().int().nonnegative().nullable(),
  latencyMs: z.number().int().nonnegative().max(300_000),
  createdAt: z.string().datetime({ offset: true }),
}).strict();
export type AgentRun = z.infer<typeof agentRunSchema>;

export type RectificationDecisionValidation = Readonly<{
  valid: boolean;
  decision: RectificationDecision | null;
  issues: readonly string[];
}>;

export function validateRectificationDecision(input: Readonly<{
  decision: unknown;
  caseId?: string;
  snapshotId?: string | null;
  opportunities: readonly QuestionOpportunity[];
  diagnostics: DiagnosticsSummary;
  candidateRangeOfferAllowed: boolean;
  usedDiagnostics?: readonly RectificationDiagnostic[];
  toolCallCount?: number;
  maxToolCalls?: number;
}>): RectificationDecisionValidation {
  const parsed = rectificationDecisionSchema.safeParse(input.decision);
  if (!parsed.success) return { valid: false, decision: null, issues: ["decision_schema_invalid"] };
  const decision = parsed.data;
  const issues: string[] = [];
  if (input.caseId && input.diagnostics.caseId !== input.caseId) issues.push("diagnostics_case_mismatch");
  if ((input.toolCallCount ?? 0) > (input.maxToolCalls ?? 2)) issues.push("tool_call_budget_exceeded");
  if (decision.action === "ask_question" && "opportunityId" in decision) {
    const opportunity = input.opportunities.find((item) => item.opportunityId === decision.opportunityId && item.active);
    if (!opportunity) issues.push("opportunity_not_active");
    if (opportunity?.kind === "clarify_event_subject" && !opportunity.targetEventId) issues.push("subject_clarification_requires_target_event");
  }
  if (decision.action === "offer_candidate_range") {
    if (!input.candidateRangeOfferAllowed) issues.push("candidate_range_gate_failed");
    if (!input.snapshotId || decision.snapshotId !== input.snapshotId || input.diagnostics.snapshotId !== input.snapshotId) issues.push("snapshot_not_current");
  }
  if (decision.action === "run_diagnostic" && input.usedDiagnostics?.includes(decision.diagnostic)) issues.push("diagnostic_already_run");
  return { valid: issues.length === 0, decision: issues.length === 0 ? decision : null, issues };
}
