import { z } from "zod";
import {
  birthTimeAssessmentSchema,
  candidateResultSchema,
  type BirthTimeAssessment,
} from "./birth-time-journey.ts";
import type { CandidateResult } from "./birth-time-evidence.ts";
import {
  candidateDifferenceBuildSchema,
  dynamicChoiceScoringResultSchema,
} from "./birth-time-dynamic-choice-internal.ts";
import type {
  CandidateDifferenceBuild,
  DynamicChoiceScoringResult,
} from "./birth-time-dynamic-choice-internal.ts";
import type {
  RectificationAnswer,
  RectificationQuestion,
  RectificationQuestionnaire,
  RectificationScoringResult,
} from "./birth-time-journey-service.ts";

const profileSchema = z.object({
  birth_date: z.string(),
  reported_birth_time: z.string().nullable().optional(),
  birth_time_source: z.enum([
    "hospital_record",
    "family_exact",
    "approximate",
    "period_only",
    "unknown",
  ]),
  birth_time_period: z.enum([
    "early_morning",
    "morning",
    "afternoon",
    "evening",
    "late_night",
  ]).nullable().optional(),
  birth_time_clue: z.string().nullable().optional(),
  uncertainty_before_minutes: z.number().int().nullable().optional(),
  uncertainty_after_minutes: z.number().int().nullable().optional(),
  latitude: z.number(),
  longitude: z.number(),
  timezone_offset: z.number(),
});

const optionSchema = z.object({
  key: z.enum(["A", "B", "C", "D"]),
  label: z.string().trim().min(1),
});

const questionSchema = z.object({
  id: z.string().trim().min(1),
  prompt: z.string().trim().min(1),
  round: z.number().int().min(1).optional(),
  options: z.array(optionSchema).optional(),
}).passthrough();

const signSchema = z.object({ sign: z.string().trim().min(1) }).nullable().optional();
const sampleSchema = z.object({
  ascendant: signSchema,
  varga_lagna: z.object({
    D4: signSchema,
    D9: signSchema,
    D10: signSchema,
    D24: signSchema,
    D30: signSchema,
  }).optional(),
});

const questionnaireSchema = z.object({
  questions: z.array(questionSchema),
  candidate_scan: z.object({ samples: z.array(sampleSchema) }),
}).passthrough();

const scoringSchema = z.object({
  answered_count: z.number().int().min(0),
  candidate_cluster_rankings: z.array(z.object({
    cluster: z.string().trim().min(1),
    score: z.number(),
  })),
  next_round: z.number().int().min(1).nullable().default(null),
  next_round_questions: z.array(questionSchema).default([]),
}).passthrough();

const eventDomainSchema = z.enum([
  "education",
  "relocation",
  "relationship",
  "career",
  "health_pressure",
]);
const candidateEvidenceApiSchema = z.object({
  event_id: z.string().uuid(),
  domain: eventDomainSchema,
  candidate_time: z.string(),
  rule_ids: z.array(z.string()),
  points: z.number(),
}).strict();

const candidateResultApiFields = {
  result_id: z.string().uuid(),
  confidence: z.enum(["low", "medium", "high"]),
  can_apply: z.boolean(),
  winning_segment: z.object({
    start_time: z.string(),
    end_time: z.string(),
    representative_time: z.string(),
    width_minutes: z.number().int(),
  }).nullable(),
  event_count: z.number().int(),
  domain_count: z.number().int(),
  top_score: z.number(),
  second_score: z.number(),
  margin_percent: z.number(),
  reasons: z.array(z.string()),
  evidence: z.array(candidateEvidenceApiSchema),
  algorithm_version: z.string(),
} as const;
const candidateResultApiSchema = z.object(candidateResultApiFields).passthrough();

const apiCandidateTimeSchema = z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/);
const apiTimeRangeSchema = z.object({
  start_time: apiCandidateTimeSchema,
  end_time: apiCandidateTimeSchema,
}).strict();

const scoredPartitionApiSchema = z.object({
  partition_id: z.string().trim().min(1),
  descriptor: z.string().trim().min(1),
  fallback_label: z.string().trim().min(1).max(80),
  candidate_scores: z.record(apiCandidateTimeSchema, z.number().finite().nonnegative()),
}).strict();

function candidateTimes(startTime: string, endTime: string): Set<string> {
  const toMinute = (value: string) => {
    const [hour, minute] = value.split(":").map(Number);
    return hour * 60 + minute;
  };
  const toTime = (value: number) => `${String(Math.floor(value / 60)).padStart(2, "0")}:${String(value % 60).padStart(2, "0")}`;
  const end = toMinute(endTime);
  let current = toMinute(startTime);
  const result = new Set<string>([toTime(current)]);
  while (current !== end) {
    current = (current + 1) % 1_440;
    result.add(toTime(current));
  }
  return result;
}

const opportunityApiSchema = z.object({
  opportunity_id: z.string().trim().min(1),
  dimension_code: z.string().trim().min(1),
  neutral_context: z.string().trim().min(1),
  estimated_information_gain: z.number().finite().nonnegative(),
  candidate_partition_fingerprint: z.string().trim().min(1),
  fallback_prompt: z.string().trim().min(1).max(240),
  partitions: z.array(scoredPartitionApiSchema).min(2).max(4),
}).strict().superRefine((value, context) => {
  if (new Set(value.partitions.map((partition) => partition.partition_id)).size !== value.partitions.length) {
    context.addIssue({
      code: z.ZodIssueCode.custom,
      path: ["partitions"],
      message: "opportunity partition ids must be unique",
    });
  }
});

const candidateDifferenceApiSchema = z.object({
  success: z.literal(true),
  endpoint: z.literal("dynamic_rectification_opportunities"),
  case_id: z.string().trim().min(1),
  scoring_version: z.literal("birth-time-choice-scoring-v2"),
  current_range: apiTimeRangeSchema,
  opportunities: z.array(opportunityApiSchema),
  asked_question_fingerprints: z.array(z.string().trim().min(1)),
  candidate_partition_fingerprints: z.array(z.string().trim().min(1)),
  recent_range_history: z.array(apiTimeRangeSchema),
  candidate_model: z.record(z.unknown()),
}).strict().superRefine((value, context) => {
  if (new Set(value.opportunities.map((opportunity) => opportunity.opportunity_id)).size !== value.opportunities.length) {
    context.addIssue({
      code: z.ZodIssueCode.custom,
      path: ["opportunities"],
      message: "opportunity ids must be unique",
    });
  }
  const expectedCandidates = candidateTimes(
    value.current_range.start_time,
    value.current_range.end_time,
  );
  value.opportunities.forEach((opportunity, opportunityIndex) => {
    opportunity.partitions.forEach((partition, partitionIndex) => {
      const actualCandidates = Object.keys(partition.candidate_scores);
      if (
        actualCandidates.length !== expectedCandidates.size
        || actualCandidates.some((candidate) => !expectedCandidates.has(candidate))
      ) {
        context.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["opportunities", opportunityIndex, "partitions", partitionIndex, "candidate_scores"],
          message: "candidate scores must exactly match the current range",
        });
      }
    });
  });
});

const dynamicChoiceScoringApiSchema = z.object({
  success: z.literal(true),
  endpoint: z.literal("dynamic_rectification_score"),
  ...candidateResultApiFields,
  algorithm_version: z.literal("birth-time-choice-scoring-v2"),
  evidence_mode: z.literal("dynamic_choice"),
  effective_answer_count: z.number().int().min(0).max(10),
  dimension_count: z.number().int().min(0).max(5),
}).strict().superRefine((value, context) => {
  if (value.event_count !== value.effective_answer_count) {
    context.addIssue({
      code: z.ZodIssueCode.custom,
      path: ["event_count"],
      message: "event count must equal effective answer count",
    });
  }
  if (value.domain_count !== value.dimension_count) {
    context.addIssue({
      code: z.ZodIssueCode.custom,
      path: ["domain_count"],
      message: "domain count must equal dimension count",
    });
  }
  if (value.evidence.length !== 0) {
    context.addIssue({
      code: z.ZodIssueCode.custom,
      path: ["evidence"],
      message: "dynamic choice results cannot contain public dated-event evidence",
    });
  }
});

class UnexpectedProfileSourceError extends Error {
  readonly name = "UnexpectedProfileSourceError";

  constructor(source: never) {
    super(`Unexpected profile birth-time source: ${JSON.stringify(source)}`);
  }
}

export function parseBirthTimeProfile(value: unknown): BirthTimeAssessment {
  const profile = profileSchema.parse(value);
  const location = {
    lat: profile.latitude,
    lon: profile.longitude,
    tz: profile.timezone_offset,
  };
  switch (profile.birth_time_source) {
    case "hospital_record":
    case "family_exact":
    case "approximate":
      return birthTimeAssessmentSchema.parse({
        date: profile.birth_date,
        source: profile.birth_time_source,
        reportedTime: profile.reported_birth_time?.slice(0, 5),
        uncertaintyBeforeMinutes: profile.uncertainty_before_minutes,
        uncertaintyAfterMinutes: profile.uncertainty_after_minutes,
        location,
      });
    case "period_only":
      return birthTimeAssessmentSchema.parse({
        date: profile.birth_date,
        source: profile.birth_time_source,
        period: profile.birth_time_period,
        location,
      });
    case "unknown":
      return birthTimeAssessmentSchema.parse({
        date: profile.birth_date,
        source: profile.birth_time_source,
        clue: profile.birth_time_clue ?? "",
        location,
      });
    default:
      throw new UnexpectedProfileSourceError(profile.birth_time_source);
  }
}

export function parseRectificationQuestionnaire(value: unknown): RectificationQuestionnaire {
  const parsed = questionnaireSchema.parse(value);
  return {
    questions: parsed.questions.map(normalizeQuestion),
    samples: parsed.candidate_scan.samples.map((sample) => ({
      ascendantSign: sample.ascendant?.sign ?? null,
      d4Sign: sample.varga_lagna?.D4?.sign ?? null,
      d9Sign: sample.varga_lagna?.D9?.sign ?? null,
      d10Sign: sample.varga_lagna?.D10?.sign ?? null,
      d24Sign: sample.varga_lagna?.D24?.sign ?? null,
      d30Sign: sample.varga_lagna?.D30?.sign ?? null,
    })),
    raw: parsed,
  };
}

function normalizeQuestion(question: z.infer<typeof questionSchema>): RectificationQuestion {
  return {
    id: question.id,
    prompt: question.prompt,
    ...(question.round ? { round: question.round } : {}),
    ...(question.options ? { options: question.options } : {}),
  };
}

export function parseRectificationScoring(value: unknown): RectificationScoringResult {
  const parsed = scoringSchema.parse(value);
  return {
    answeredCount: parsed.answered_count,
    candidateClusterRankings: parsed.candidate_cluster_rankings,
    nextRound: parsed.next_round,
    nextRoundQuestions: parsed.next_round_questions.map(normalizeQuestion),
    raw: parsed,
  };
}

export function parseRectificationAnswer(value: unknown): RectificationAnswer {
  return z.enum(["A", "B", "C", "D"]).parse(value);
}

export function parseCandidateDifferenceBuild(value: unknown): CandidateDifferenceBuild {
  const parsed = candidateDifferenceApiSchema.parse(value);
  return candidateDifferenceBuildSchema.parse({
    packet: {
      caseId: parsed.case_id,
      scoringVersion: parsed.scoring_version,
      currentRange: {
        startTime: parsed.current_range.start_time,
        endTime: parsed.current_range.end_time,
      },
      opportunities: parsed.opportunities.map((opportunity) => ({
        opportunityId: opportunity.opportunity_id,
        dimensionCode: opportunity.dimension_code,
        neutralContext: opportunity.neutral_context,
        estimatedInformationGain: opportunity.estimated_information_gain,
        candidatePartitionFingerprint: opportunity.candidate_partition_fingerprint,
        fallbackPrompt: opportunity.fallback_prompt,
        partitions: opportunity.partitions.map((partition) => ({
          partitionId: partition.partition_id,
          descriptor: partition.descriptor,
          fallbackLabel: partition.fallback_label,
        })),
      })),
      askedQuestionFingerprints: parsed.asked_question_fingerprints,
      candidatePartitionFingerprints: parsed.candidate_partition_fingerprints,
      recentRangeHistory: parsed.recent_range_history.map((range) => ({
        startTime: range.start_time,
        endTime: range.end_time,
      })),
    },
    candidateModel: parsed.candidate_model,
    scoringPartitions: Object.fromEntries(parsed.opportunities.map((opportunity) => [
      opportunity.opportunity_id,
      opportunity.partitions.map((partition) => ({
        partitionId: partition.partition_id,
        descriptor: partition.descriptor,
        fallbackLabel: partition.fallback_label,
        candidateScores: partition.candidate_scores,
      })),
    ])),
  });
}

export function parseDynamicChoiceScoring(value: unknown): DynamicChoiceScoringResult {
  const parsed = dynamicChoiceScoringApiSchema.parse(value);
  return dynamicChoiceScoringResultSchema.parse({
    candidate: adaptCandidateResult(parsed),
    evidenceMode: parsed.evidence_mode,
    effectiveAnswerCount: parsed.effective_answer_count,
    dimensionCount: parsed.dimension_count,
  });
}

export function parseCandidateResult(value: unknown): CandidateResult {
  return adaptCandidateResult(candidateResultApiSchema.parse(value));
}

function adaptCandidateResult(parsed: z.infer<typeof candidateResultApiSchema>): CandidateResult {
  return candidateResultSchema.parse({
    resultId: parsed.result_id,
    confidence: parsed.confidence,
    canApply: parsed.can_apply,
    winningSegment: parsed.winning_segment
      ? {
          startTime: parsed.winning_segment.start_time,
          endTime: parsed.winning_segment.end_time,
          representativeTime: parsed.winning_segment.representative_time,
          widthMinutes: parsed.winning_segment.width_minutes,
        }
      : null,
    eventCount: parsed.event_count,
    domainCount: parsed.domain_count,
    topScore: parsed.top_score,
    secondScore: parsed.second_score,
    marginPercent: parsed.margin_percent,
    reasons: parsed.reasons,
    evidence: parsed.evidence.map((item) => ({
      eventId: item.event_id,
      domain: item.domain,
      candidateTime: item.candidate_time,
      ruleIds: item.rule_ids,
      points: item.points,
    })),
    algorithmVersion: parsed.algorithm_version,
  });
}
