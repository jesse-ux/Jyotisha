import { z } from "zod";
import { boundedJson } from "./json-bounds.ts";

const actionIdSchema = z.string().uuid();
const caseIdSchema = z.string().uuid();
const turnVersionSchema = z.number().int().nonnegative();
const timeSchema = z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/);
const evidenceDomainSchema = z.enum([
  "career",
  "education",
  "relocation",
  "relationship",
  "family",
  "other",
]);

const boundedNonblankText = (maximum: number) => z.string()
  .min(1)
  .max(maximum)
  .refine((value) => value.trim().length > 0, "text must contain a non-whitespace character");

const actionCommandSchema = z.object({
  caseId: caseIdSchema,
  actionId: actionIdSchema,
  turnVersion: turnVersionSchema,
});

/**
 * The only browser-to-server commands for conversational-evidence-v3.
 * Calculation inputs and technical receipts are server-owned and deliberately absent.
 */
export const conversationalRectificationCommandSchema = z.discriminatedUnion("type", [
  z.object({
    type: z.literal("start"),
    actionId: actionIdSchema,
    pendingConsultationQuestion: z.string().trim().min(1).max(500).nullable().optional(),
  }).strict(),
  actionCommandSchema.extend({
    type: z.literal("resume"),
  }).strict(),
  actionCommandSchema.extend({
    type: z.literal("answer"),
    domain: evidenceDomainSchema.optional(),
    answer: z.string().trim().min(1).max(4_000),
  }).strict(),
  actionCommandSchema.extend({
    type: z.literal("pause"),
  }).strict(),
  actionCommandSchema.extend({
    type: z.literal("abandon"),
  }).strict(),
  actionCommandSchema.extend({
    type: z.literal("confirm"),
    time: timeSchema,
  }).strict(),
]);

export type ConversationalRectificationCommand = z.infer<typeof conversationalRectificationCommandSchema>;

const candidateSchema = boundedJson(z.object({
  status: z.enum(["declared", "pending_validation", "ready_for_confirmation", "confirmed"]),
  representativeTime: timeSchema.nullable(),
  rangeStart: timeSchema.nullable(),
  rangeEnd: timeSchema.nullable(),
}).strict(), 512);

const technicalReceiptSchema = boundedJson(z.object({
  calculationVersion: boundedNonblankText(80),
  stableLayers: boundedJson(z.array(boundedNonblankText(80)).max(20), 4_096),
  sensitiveLayers: boundedJson(z.array(boundedNonblankText(80)).max(20), 4_096),
  candidateDifferenceRefs: z.array(boundedNonblankText(120)).max(40),
}).strict(), 8_192);

const evidenceRequestSchema = boundedJson(z.object({
  domains: z.array(evidenceDomainSchema).min(2).max(4),
  datePrecision: z.enum(["month_preferred", "year_accepted"]),
  freeTextAllowed: z.literal(true),
}).strict(), 2_048);

const evidenceRecapEntrySchema = boundedJson(z.object({
  id: z.string().uuid(),
  summary: boundedNonblankText(1_000),
  dateLabel: boundedNonblankText(80),
}).strict(), 4_096);
const evidenceRecapSchema = boundedJson(
  z.array(evidenceRecapEntrySchema).max(20),
  24_576,
);

export const conversationalRectificationTurnSchema = boundedJson(z.object({
  caseId: caseIdSchema,
  journeyProtocol: z.literal("conversational-evidence-v3"),
  status: z.enum(["active", "paused", "confirming", "completed", "abandoned"]),
  turnVersion: turnVersionSchema,
  narrative: boundedNonblankText(12_000),
  candidate: candidateSchema,
  technicalReceipt: technicalReceiptSchema,
  evidenceRequest: evidenceRequestSchema.nullable(),
  evidenceRecap: evidenceRecapSchema,
  actions: z.array(z.enum([
    "answer",
    "pause",
    "abandon",
    "confirm",
    "continue_original_question",
  ])).max(5),
  pendingConsultationQuestion: boundedNonblankText(500).nullable(),
}).strict(), 65_536);

export type ConversationalRectificationTurn = z.infer<typeof conversationalRectificationTurnSchema>;
