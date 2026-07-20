import { z } from "zod";

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

export const conversationalRectificationTurnSchema = z.object({
  caseId: caseIdSchema,
  journeyProtocol: z.literal("conversational-evidence-v3"),
  status: z.enum(["active", "paused", "confirming", "completed", "abandoned"]),
  turnVersion: turnVersionSchema,
  narrative: z.string().trim().min(1).max(12_000),
  candidate: z.object({
    status: z.enum(["declared", "pending_validation", "ready_for_confirmation", "confirmed"]),
    representativeTime: timeSchema.nullable(),
    rangeStart: timeSchema.nullable(),
    rangeEnd: timeSchema.nullable(),
  }).strict(),
  technicalReceipt: z.object({
    calculationVersion: z.string().trim().min(1).max(80),
    stableLayers: z.array(z.string().trim().min(1).max(80)).max(20),
    sensitiveLayers: z.array(z.string().trim().min(1).max(80)).max(20),
    candidateDifferenceRefs: z.array(z.string().trim().min(1).max(120)).max(40),
  }).strict(),
  evidenceRequest: z.object({
    domains: z.array(evidenceDomainSchema).min(2).max(4),
    datePrecision: z.enum(["month_preferred", "year_accepted"]),
    freeTextAllowed: z.literal(true),
  }).strict().nullable(),
  evidenceRecap: z.array(z.object({
    id: z.string().uuid(),
    summary: z.string(),
    dateLabel: z.string(),
  }).strict()).max(20),
  actions: z.array(z.enum([
    "answer",
    "pause",
    "abandon",
    "confirm",
    "continue_original_question",
  ])).max(5),
  pendingConsultationQuestion: z.string().max(500).nullable(),
}).strict();

export type ConversationalRectificationTurn = z.infer<typeof conversationalRectificationTurnSchema>;
