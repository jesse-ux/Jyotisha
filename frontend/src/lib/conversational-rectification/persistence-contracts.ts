import { z } from "zod";
import { conversationalRectificationTurnSchema } from "./contracts.ts";
import { boundedJson } from "./json-bounds.ts";

const uuidSchema = z.string().uuid();
const timeSchema = z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/);
const boundedText = (maximum: number) => z.string()
  .min(1)
  .max(maximum)
  .refine((value) => value.trim().length > 0, "text must contain a non-whitespace character");

const birthDateSchema = z.string().regex(/^\d{4}-\d{2}-\d{2}$/).refine((value) => {
  const [year, month, day] = value.split("-").map(Number);
  if (year === undefined || month === undefined || day === undefined) return false;
  if (year < 1_000 || year > 9_999 || month < 1 || month > 12 || day < 1) return false;
  const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const days = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  return day <= (days[month - 1] ?? 0);
}, "invalid calendar date");

const locationCodeSchema = boundedText(80);
const birthplaceSchema = boundedJson(z.object({
  city: boundedText(120).optional(),
  countryCode: z.string().regex(/^[A-Z0-9-]{1,8}$/).optional(),
  provinceCode: locationCodeSchema.optional(),
  cityCode: locationCodeSchema.optional(),
  districtCode: locationCodeSchema.optional(),
  latitude: z.number().finite().min(-90).max(90).optional(),
  longitude: z.number().finite().min(-180).max(180).optional(),
  timezoneOffset: z.number().finite().min(-12).max(14),
}).strict().superRefine((value, context) => {
  if (!value.city && !value.cityCode) {
    context.addIssue({ code: "custom", message: "city or cityCode is required" });
  }
  if ((value.latitude === undefined) !== (value.longitude === undefined)) {
    context.addIssue({ code: "custom", message: "coordinates must be supplied as a pair" });
  }
}), 4_096);

const clueSchema = z.string().max(240).nullable();
const commonBirthFields = {
  birthDate: birthDateSchema,
  birthTimeClue: clueSchema,
  birthplace: birthplaceSchema,
} as const;
const periodSchema = z.enum([
  "early_morning",
  "morning",
  "afternoon",
  "evening",
  "late_night",
]);

const hospitalDeclarationSchema = z.object({
  ...commonBirthFields,
  source: z.literal("hospital_record"),
  reportedTime: timeSchema,
  uncertaintyBeforeMinutes: z.literal(2),
  uncertaintyAfterMinutes: z.literal(2),
}).strict();
const familyDeclarationSchema = z.object({
  ...commonBirthFields,
  source: z.literal("family_exact"),
  reportedTime: timeSchema,
  uncertaintyBeforeMinutes: z.union([z.literal(5), z.literal(10), z.literal(15)]),
  uncertaintyAfterMinutes: z.union([z.literal(5), z.literal(10), z.literal(15)]),
}).strict().refine(
  (value) => value.uncertaintyBeforeMinutes === value.uncertaintyAfterMinutes,
  "family uncertainty must be symmetric",
);
const approximateDeclarationSchema = z.object({
  ...commonBirthFields,
  source: z.literal("approximate"),
  reportedTime: timeSchema,
  uncertaintyBeforeMinutes: z.union([z.literal(15), z.literal(30), z.literal(60)]),
  uncertaintyAfterMinutes: z.union([z.literal(15), z.literal(30), z.literal(60)]),
}).strict().refine(
  (value) => value.uncertaintyBeforeMinutes === value.uncertaintyAfterMinutes,
  "approximate uncertainty must be symmetric",
);
const periodDeclarationSchema = z.object({
  ...commonBirthFields,
  source: z.literal("period_only"),
  reportedPeriod: periodSchema,
}).strict();
const unknownDeclarationSchema = z.object({
  ...commonBirthFields,
  source: z.literal("unknown"),
}).strict();
const legacyDeclarationSchema = z.object({
  ...commonBirthFields,
  source: z.literal("legacy_import"),
  reportedTime: timeSchema.optional(),
  reportedPeriod: periodSchema.optional(),
  uncertaintyBeforeMinutes: z.number().int().min(0).max(720).optional(),
  uncertaintyAfterMinutes: z.number().int().min(0).max(720).optional(),
}).strict().superRefine((value, context) => {
  const hasTime = typeof value.reportedTime === "string";
  const hasPeriod = typeof value.reportedPeriod === "string";
  if (hasTime && hasPeriod) {
    context.addIssue({ code: "custom", message: "legacy declaration has two time modes" });
  }
  const before = value.uncertaintyBeforeMinutes;
  const after = value.uncertaintyAfterMinutes;
  if ((before === undefined) !== (after === undefined)
    || (!hasTime && (before !== undefined || after !== undefined))) {
    context.addIssue({ code: "custom", message: "legacy uncertainty is incoherent" });
  }
});

export const declaredBirthInputSchema = boundedJson(z.union([
  hospitalDeclarationSchema,
  familyDeclarationSchema,
  approximateDeclarationSchema,
  periodDeclarationSchema,
  unknownDeclarationSchema,
  legacyDeclarationSchema,
]), 12_000);
export type DeclaredBirthInput = z.infer<typeof declaredBirthInputSchema>;

const evidenceDomainSchema = z.enum([
  "career",
  "education",
  "relocation",
  "relationship",
  "family",
  "other",
]);
const scoredEvidenceSchema = boundedJson(z.object({
  evidenceId: uuidSchema,
  domain: evidenceDomainSchema,
  candidateTime: timeSchema.nullable(),
  score: z.number().finite().min(-1_000_000).max(1_000_000),
  ruleRefs: z.array(boundedText(120)).max(40),
}).strict(), 8_192);
const futureWindowSchema = boundedJson(z.object({
  label: boundedText(240),
  startDate: birthDateSchema,
  endDate: birthDateSchema,
  scoreable: z.literal(false),
}).strict().refine((value) => value.startDate <= value.endDate, "window order is invalid"), 2_048);
const privateWorkingStateSchema = boundedJson(z.object({
  phase: z.enum(["initial", "collecting_evidence", "rescoring", "ready", "confirmed"]),
  iteration: z.number().int().min(0).max(100),
  notes: z.array(boundedText(240)).max(20),
}).strict(), 8_192);

export const privateCandidateSchema = boundedJson(z.object({
  resultId: uuidSchema.nullable().optional(),
  representativeTime: timeSchema.nullable().optional(),
  rangeStart: timeSchema.nullable().optional(),
  rangeEnd: timeSchema.nullable().optional(),
  calculationVersion: boundedText(80),
  candidateWeights: z.array(z.number().finite().min(0).max(1)).max(1_440).optional(),
  candidateModelRefs: z.array(boundedText(120)).max(80).optional(),
  d1Stability: z.enum(["stable", "sensitive", "unavailable"]).optional(),
  boundaryDistanceMinutes: z.number().int().min(0).max(1_440).nullable().optional(),
  supportedSensitiveLayers: z.array(boundedText(80)).max(40).optional(),
  scoredHistoricalEvidence: z.array(scoredEvidenceSchema).max(100).optional(),
  suggestedDomains: z.array(evidenceDomainSchema).max(6).optional(),
  futureWindows: z.array(futureWindowSchema).max(20).optional(),
  workingState: privateWorkingStateSchema.optional(),
}).strict().superRefine((value, context) => {
  const hasRangeStart = value.rangeStart !== undefined;
  const hasRangeEnd = value.rangeEnd !== undefined;
  if (hasRangeStart !== hasRangeEnd
    || (hasRangeStart && (value.rangeStart === null) !== (value.rangeEnd === null))) {
    context.addIssue({ code: "custom", message: "candidate range must be supplied as a pair" });
  }
}), 65_536);
export type PrivateCandidate = z.infer<typeof privateCandidateSchema>;

export const validationReceiptSchema = boundedJson(z.object({
  modelId: boundedText(120),
  schemaValidated: z.boolean(),
  validatorVersion: boundedText(80).optional(),
  validatedAt: z.string().max(40).datetime({ offset: true }).optional(),
  retryCount: z.number().int().min(0).max(2).optional(),
  fallbackUsed: z.boolean().optional(),
  issues: z.array(boundedText(240)).max(20).optional(),
}).strict(), 8_192);
export type ValidationReceipt = z.infer<typeof validationReceiptSchema>;

export const lifeEventEvidenceSchema = boundedJson(z.object({
  id: uuidSchema,
  rawText: boundedText(4_000),
  domain: evidenceDomainSchema,
  eventSummary: boundedText(1_000),
  dateValue: boundedText(80).nullable(),
  datePrecision: z.enum(["day", "month", "year", "range", "unknown"]),
  extractionStatus: z.enum(["clear", "needs_clarification", "corrected"]),
  scoreable: z.boolean().optional(),
}).strict(), 16_384);
export type LifeEventEvidence = z.infer<typeof lifeEventEvidenceSchema>;

const mutationKindSchema = z.enum([
  "create",
  "save_turn",
  "pause",
  "abandon",
  "confirm",
  "import_legacy",
  "reserve_fee",
  "complete_fee",
  "release_fee",
  "recover_fee",
]);
export const conversationalRectificationActionReceiptRequestSchema = boundedJson(z.object({
  kind: mutationKindSchema,
  userId: uuidSchema,
  caseId: uuidSchema,
  expectedVersion: z.number().int().nonnegative(),
  actionId: uuidSchema,
  requestFingerprint: z.string().regex(/^[0-9a-f]{64}$/),
}).strict(), 2_048);

export const billingReceiptResponseSchema = boundedJson(z.object({
  success: z.boolean(),
  credits: z.number().int().nonnegative().nullable(),
  billing_state: z.enum(["reserved", "charged", "released", "migration_waived"]).nullable(),
  error_code: boundedText(80).nullable(),
}).strict(), 2_048);

export const storedCaseRowSchema = boundedJson(z.object({
  case_id: uuidSchema,
  user_id: uuidSchema,
  status: z.enum(["starting", "active", "paused", "confirming", "completed", "abandoned"]),
  turn_version: z.number().int().nonnegative(),
  revision_of_case_id: uuidSchema.nullable(),
  imported_from_case_id: uuidSchema.nullable(),
  baseline_active_time: timeSchema.nullable(),
  pending_consultation_question: boundedText(500).nullable(),
  billing_state: z.enum(["reserved", "charged", "released", "migration_waived"]).nullable(),
  latest_turn: conversationalRectificationTurnSchema,
  declared_birth_input: declaredBirthInputSchema.optional(),
  private_candidate: privateCandidateSchema.optional(),
  event_evidence: z.array(lifeEventEvidenceSchema).max(2_000).optional(),
  validation_receipts: z.array(validationReceiptSchema).max(2_000).optional(),
}).strict(), 4_194_304);

const publicStoredCaseRowSchema = storedCaseRowSchema.refine(
  (value) => value.declared_birth_input === undefined
    && value.private_candidate === undefined
    && value.event_evidence === undefined
    && value.validation_receipts === undefined,
  "action receipt response cannot contain private state",
);

export const conversationalRectificationActionReceiptResponseSchema = z.union([
  billingReceiptResponseSchema,
  boundedJson(publicStoredCaseRowSchema, 69_632),
]);
