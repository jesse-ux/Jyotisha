import { z } from "zod";

export {
  candidateResultSchema,
  lifeEventSchema,
  withCandidateResult,
  withConfirmedCandidate,
} from "./birth-time-evidence.ts";

const dateSchema = z.string().regex(/^\d{4}-\d{2}-\d{2}$/);
const timeSchema = z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/);
const locationSchema = z.object({
  lat: z.number().min(-90).max(90),
  lon: z.number().min(-180).max(180),
  tz: z.number().min(-12).max(14),
}).readonly();

const exactFields = {
  date: dateSchema,
  reportedTime: timeSchema,
  location: locationSchema,
} as const;

export const birthTimeAssessmentSchema = z.union([
  z.object({
    ...exactFields,
    source: z.literal("hospital_record"),
    uncertaintyBeforeMinutes: z.literal(2),
    uncertaintyAfterMinutes: z.literal(2),
  }).readonly(),
  z.object({
    ...exactFields,
    source: z.literal("family_exact"),
    uncertaintyBeforeMinutes: z.union([z.literal(5), z.literal(10), z.literal(15)]),
    uncertaintyAfterMinutes: z.union([z.literal(5), z.literal(10), z.literal(15)]),
  }).readonly().refine(
    (value) => value.uncertaintyBeforeMinutes === value.uncertaintyAfterMinutes,
    { message: "family uncertainty must be symmetric" },
  ),
  z.object({
    ...exactFields,
    source: z.literal("approximate"),
    uncertaintyBeforeMinutes: z.union([z.literal(15), z.literal(30), z.literal(60)]),
    uncertaintyAfterMinutes: z.union([z.literal(15), z.literal(30), z.literal(60)]),
  }).readonly().refine(
    (value) => value.uncertaintyBeforeMinutes === value.uncertaintyAfterMinutes,
    { message: "approximate uncertainty must be symmetric" },
  ),
  z.object({
    date: dateSchema,
    source: z.literal("period_only"),
    period: z.enum(["early_morning", "morning", "afternoon", "evening", "late_night"]),
    location: locationSchema,
  }).readonly(),
  z.object({
    date: dateSchema,
    source: z.literal("unknown"),
    clue: z.string().trim().max(240).default(""),
    location: locationSchema,
  }).readonly(),
]);

export type BirthTimeAssessment = z.infer<typeof birthTimeAssessmentSchema>;

export type ScanStability =
  | { readonly kind: "stable" }
  | { readonly kind: "sensitive" }
  | { readonly kind: "unavailable" }
  | { readonly kind: "not_required" };

export const journeySnapshotSchema = z.object({
  state: z.enum(["rectifying", "candidate", "confirming", "ready"]),
  assistantIntent: z.enum([
    "confirm_stable_record",
    "explain_sensitive_boundary",
    "explain_assessment_unavailable",
    "start_light_rectification",
    "start_standard_rectification",
    "start_period_rectification",
    "collect_time_clues",
    "continue_rectification_questions",
    "present_saved_candidate_range",
    "collect_dated_life_events",
    "explain_event_evidence_insufficient",
    "present_candidate_result",
    "confirm_candidate_time",
    "confirmed_candidate_time",
  ]),
  input: z.enum([
    "none",
    "rectification_questions",
    "time_clue",
    "life_events",
    "candidate_actions",
    "candidate_confirmation",
  ]),
  route: z.enum(["direct_chart", "rectification"]),
  confidence: z.enum(["low", "medium", "high"]).nullable(),
  canApply: z.boolean(),
  activeTime: z.string().nullable(),
  reportedRange: z.object({
    label: z.string(),
    startTime: z.string().nullable(),
    endTime: z.string().nullable(),
  }).readonly(),
}).readonly();

export type JourneySnapshot = z.infer<typeof journeySnapshotSchema>;

export type RectificationScoring = {
  readonly answeredCount: number;
  readonly candidateClusterRankings: readonly {
    readonly cluster: string;
    readonly score: number;
  }[];
  readonly nextRound?: number | null;
  readonly nextRoundQuestions?: readonly unknown[];
};

class UnexpectedJourneyVariantError extends Error {
  readonly name = "UnexpectedJourneyVariantError";

  constructor(value: never) {
    super(`Unexpected birth-time journey variant: ${JSON.stringify(value)}`);
  }
}

const periodRanges = {
  early_morning: { label: "04:00—07:59", startTime: "04:00", endTime: "07:59" },
  morning: { label: "08:00—11:59", startTime: "08:00", endTime: "11:59" },
  afternoon: { label: "12:00—17:59", startTime: "12:00", endTime: "17:59" },
  evening: { label: "18:00—22:59", startTime: "18:00", endTime: "22:59" },
  late_night: { label: "23:00—03:59", startTime: "23:00", endTime: "03:59" },
} as const;

function shiftedTime(time: string, offsetMinutes: number): string {
  const [hourText, minuteText] = time.split(":");
  const minutes = Number(hourText) * 60 + Number(minuteText) + offsetMinutes;
  const normalized = (minutes + 24 * 60) % (24 * 60);
  return `${String(Math.floor(normalized / 60)).padStart(2, "0")}:${String(normalized % 60).padStart(2, "0")}`;
}

function exactRange(time: string, before: number, after: number): JourneySnapshot["reportedRange"] {
  const startTime = shiftedTime(time, -before);
  const endTime = shiftedTime(time, after);
  return { label: `${startTime}—${endTime}`, startTime, endTime };
}

function rectificationSnapshot(
  assistantIntent: JourneySnapshot["assistantIntent"],
  reportedRange: JourneySnapshot["reportedRange"],
  input: JourneySnapshot["input"] = "rectification_questions",
): JourneySnapshot {
  return {
    state: "rectifying",
    assistantIntent,
    input,
    route: "rectification",
    confidence: null,
    canApply: false,
    activeTime: null,
    reportedRange,
  };
}

export function assessBirthTime(
  assessment: BirthTimeAssessment,
  scanStability: ScanStability,
): JourneySnapshot {
  switch (assessment.source) {
    case "hospital_record": {
      const reportedRange = exactRange(assessment.reportedTime, 2, 2);
      switch (scanStability.kind) {
        case "stable":
          return {
            state: "ready",
            assistantIntent: "confirm_stable_record",
            input: "none",
            route: "direct_chart",
            confidence: "high",
            canApply: true,
            activeTime: assessment.reportedTime,
            reportedRange,
          };
        case "sensitive":
          return rectificationSnapshot("explain_sensitive_boundary", reportedRange);
        case "unavailable":
        case "not_required":
          return rectificationSnapshot("explain_assessment_unavailable", reportedRange);
        default:
          throw new UnexpectedJourneyVariantError(scanStability);
      }
    }
    case "family_exact":
      return rectificationSnapshot(
        "start_light_rectification",
        exactRange(assessment.reportedTime, assessment.uncertaintyBeforeMinutes, assessment.uncertaintyAfterMinutes),
      );
    case "approximate":
      return rectificationSnapshot(
        "start_standard_rectification",
        exactRange(assessment.reportedTime, assessment.uncertaintyBeforeMinutes, assessment.uncertaintyAfterMinutes),
      );
    case "period_only":
      return rectificationSnapshot("start_period_rectification", periodRanges[assessment.period]);
    case "unknown":
      return rectificationSnapshot(
        "collect_time_clues",
        { label: "全天待确认", startTime: null, endTime: null },
        "time_clue",
      );
    default:
      throw new UnexpectedJourneyVariantError(assessment);
  }
}

export function withRectificationScoring(
  snapshot: JourneySnapshot,
  scoring: RectificationScoring,
): JourneySnapshot {
  if (snapshot.route === "direct_chart") return snapshot;
  const questionnaireComplete = scoring.nextRound === null
    && scoring.nextRoundQuestions?.length === 0
    && scoring.answeredCount > 0;
  if (questionnaireComplete) {
    return {
      ...snapshot,
      state: "rectifying",
      assistantIntent: "collect_dated_life_events",
      input: "life_events",
      confidence: null,
      canApply: false,
      activeTime: null,
    };
  }
  const hasCandidate = scoring.answeredCount >= 3 && scoring.candidateClusterRankings.length > 0;
  return {
    ...snapshot,
    state: hasCandidate ? "candidate" : "rectifying",
    assistantIntent: hasCandidate ? "present_saved_candidate_range" : "continue_rectification_questions",
    canApply: false,
    activeTime: null,
  };
}
