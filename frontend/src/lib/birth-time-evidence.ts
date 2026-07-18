import { z } from "zod";
import type { JourneySnapshot } from "./birth-time-journey.ts";

const timeSchema = z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/);
export const lifeEventDomainSchema = z.enum([
  "education",
  "relocation",
  "relationship",
  "career",
  "health_pressure",
]);

export const lifeEventPrecisionSchema = z.enum(["year", "month", "day"]);

const lifeEventBase = {
  id: z.string().uuid(),
  domain: lifeEventDomainSchema,
} as const;

const supportedYearSchema = z.string().regex(/^(19|20)\d{2}$/).refine(
  (value) => Number(value) <= new Date().getFullYear(),
  "event year cannot be in the future",
);

const monthDateSchema = z.string().regex(/^(19|20)\d{2}-(0[1-9]|1[0-2])$/).refine(
  (value) => value <= new Date().toISOString().slice(0, 7),
  "event month cannot be in the future",
);

const dayDateSchema = z.string().regex(/^(19|20)\d{2}-(0[1-9]|1[0-2])-([0-2]\d|3[01])$/).refine(
  (value) => {
    const [year, month, day] = value.split("-").map(Number);
    const parsed = new Date(Date.UTC(year, month - 1, day));
    return parsed.getUTCFullYear() === year
      && parsed.getUTCMonth() === month - 1
      && parsed.getUTCDate() === day
      && value <= new Date().toISOString().slice(0, 10);
  },
  "event day must be a real past or present calendar date",
);

export const lifeEventSchema = z.discriminatedUnion("precision", [
  z.object({ ...lifeEventBase, precision: z.literal("year"), date: supportedYearSchema }).strict(),
  z.object({ ...lifeEventBase, precision: z.literal("month"), date: monthDateSchema }).strict(),
  z.object({ ...lifeEventBase, precision: z.literal("day"), date: dayDateSchema }).strict(),
]).readonly();

export type LifeEvent = z.infer<typeof lifeEventSchema>;

export const evidenceDraftProposalSchema = z.object({
  domain: lifeEventDomainSchema,
  precision: lifeEventPrecisionSchema.nullable(),
  date: z.string().trim().min(1).max(10).nullable(),
}).strict().readonly();

export type EvidenceDraftProposal = z.infer<typeof evidenceDraftProposalSchema>;

export const evidenceDraftSchema = z.object({
  draftId: z.string().uuid(),
  questionId: z.string().trim().min(1).max(120),
  domain: lifeEventDomainSchema,
  precision: lifeEventPrecisionSchema.nullable(),
  date: z.string().trim().min(1).max(10).nullable(),
  status: z.literal("draft"),
  needsReview: z.boolean(),
}).strict().readonly().superRefine((value, context) => {
  if ((value.precision === null || value.date === null) && !value.needsReview) {
    context.addIssue({
      code: z.ZodIssueCode.custom,
      path: ["needsReview"],
      message: "incomplete evidence drafts require review",
    });
  }
});

export type EvidenceDraft = z.infer<typeof evidenceDraftSchema>;

const candidateEvidenceSchema = z.object({
  eventId: z.string().uuid(),
  domain: lifeEventDomainSchema,
  candidateTime: timeSchema,
  ruleIds: z.array(z.string().trim().min(1)),
  points: z.number(),
}).strict().readonly();

export const candidateResultSchema = z.object({
  resultId: z.string().uuid(),
  confidence: z.enum(["low", "medium", "high"]),
  canApply: z.boolean(),
  winningSegment: z.object({
    startTime: timeSchema,
    endTime: timeSchema,
    representativeTime: timeSchema,
    widthMinutes: z.number().int().min(1).max(1_440),
  }).strict().readonly().nullable(),
  eventCount: z.number().int().min(0).max(6),
  domainCount: z.number().int().min(0).max(5),
  topScore: z.number(),
  secondScore: z.number(),
  marginPercent: z.number().min(0),
  reasons: z.array(z.string().trim().min(1)),
  evidence: z.array(candidateEvidenceSchema),
  algorithmVersion: z.string().trim().min(1),
}).strict().readonly().superRefine((value, context) => {
  const eligible = value.confidence === "high" && highCandidateMeetsSafetyGates(value);
  if (value.confidence === "high" && value.eventCount < 4) {
    context.addIssue({
      code: z.ZodIssueCode.custom,
      path: ["eventCount"],
      message: "high candidates require at least four events",
    });
  }
  if (value.confidence === "high" && value.domainCount < 3) {
    context.addIssue({
      code: z.ZodIssueCode.custom,
      path: ["domainCount"],
      message: "high candidates require at least three domains",
    });
  }
  if (value.confidence === "high" && value.winningSegment === null) {
    context.addIssue({
      code: z.ZodIssueCode.custom,
      path: ["winningSegment"],
      message: "high candidates require a winning segment",
    });
  }
  if (value.confidence === "high" && value.winningSegment !== null && value.winningSegment.widthMinutes > 5) {
    context.addIssue({
      code: z.ZodIssueCode.custom,
      path: ["winningSegment", "widthMinutes"],
      message: "high candidate segments cannot exceed five minutes",
    });
  }
  if (value.confidence === "high" && value.marginPercent < 20) {
    context.addIssue({
      code: z.ZodIssueCode.custom,
      path: ["marginPercent"],
      message: "high candidates require at least twenty percent margin",
    });
  }
  if (value.canApply !== eligible) {
    context.addIssue({
      code: z.ZodIssueCode.custom,
      path: ["canApply"],
      message: "only a high candidate with a winning segment can be confirmed",
    });
  }
});

export type CandidateResult = z.infer<typeof candidateResultSchema>;

function highCandidateMeetsSafetyGates(value: {
  readonly confidence: CandidateResult["confidence"];
  readonly winningSegment: CandidateResult["winningSegment"];
  readonly eventCount: number;
  readonly domainCount: number;
  readonly marginPercent: number;
}): boolean {
  return value.confidence === "high"
    && value.winningSegment !== null
    && value.eventCount >= 4
    && value.domainCount >= 3
    && value.winningSegment.widthMinutes <= 5
    && value.marginPercent >= 20;
}

export class CandidateConfirmationError extends Error {
  readonly name = "CandidateConfirmationError";
}

export function withCandidateResult(
  snapshot: JourneySnapshot,
  result: CandidateResult,
): JourneySnapshot {
  switch (result.confidence) {
    case "low":
      return {
        ...snapshot,
        state: "rectifying",
        assistantIntent: "explain_event_evidence_insufficient",
        input: "life_events",
        confidence: "low",
        canApply: false,
        activeTime: null,
      };
    case "medium":
      return {
        ...snapshot,
        state: "candidate",
        assistantIntent: "present_candidate_result",
        input: "candidate_actions",
        confidence: "medium",
        canApply: false,
        activeTime: null,
      };
    case "high":
      return {
        ...snapshot,
        state: "confirming",
        assistantIntent: "confirm_candidate_time",
        input: "candidate_confirmation",
        confidence: "high",
        canApply: true,
        activeTime: null,
      };
  }
}

export function withConfirmedCandidate(
  snapshot: JourneySnapshot,
  result: CandidateResult,
  confirmedTime: string,
): JourneySnapshot {
  if (
    snapshot.state !== "confirming"
    || !snapshot.canApply
    || !highCandidateMeetsSafetyGates(result)
    || !result.canApply
    || result.winningSegment?.representativeTime !== confirmedTime
  ) {
    throw new CandidateConfirmationError();
  }
  return {
    ...snapshot,
    state: "ready",
    assistantIntent: "confirmed_candidate_time",
    input: "none",
    route: "direct_chart",
    confidence: "high",
    canApply: false,
    activeTime: confirmedTime,
  };
}
