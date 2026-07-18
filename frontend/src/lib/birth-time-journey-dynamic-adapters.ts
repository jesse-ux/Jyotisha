import { z } from "zod";
import {
  candidateDifferenceBuildSchema,
  dynamicChoiceScoringResultSchema,
} from "./birth-time-dynamic-choice-internal.ts";
import { candidateResultSchema } from "./birth-time-evidence.ts";
import {
  DYNAMIC_QUESTION_LABEL_MAX_LENGTH,
  DYNAMIC_QUESTION_PROMPT_MAX_LENGTH,
} from "./birth-time-dynamic-question-limits.ts";
import type {
  CandidateDifferenceBuild,
  DynamicChoiceScoringResult,
} from "./birth-time-dynamic-choice-internal.ts";

const candidateTimeSchema = z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/);
const apiRangeSchema = z.object({
  start_time: candidateTimeSchema,
  end_time: candidateTimeSchema,
}).strict();
const partitionSchema = z.object({
  partition_id: z.string().trim().min(1),
  descriptor: z.string().trim().min(1),
  fallback_label: z.string().trim().min(1).max(DYNAMIC_QUESTION_LABEL_MAX_LENGTH),
  candidate_scores: z.record(candidateTimeSchema, z.number().finite().nonnegative()),
}).strict();
const opportunitySchema = z.object({
  opportunity_id: z.string().trim().min(1),
  dimension_code: z.string().trim().min(1),
  neutral_context: z.string().trim().min(1),
  estimated_information_gain: z.number().finite().nonnegative(),
  candidate_partition_fingerprint: z.string().trim().min(1),
  fallback_prompt: z.string().trim().min(1).max(DYNAMIC_QUESTION_PROMPT_MAX_LENGTH),
  partitions: z.array(partitionSchema).min(2).max(4),
}).strict().superRefine((value, context) => {
  if (new Set(value.partitions.map((item) => item.partition_id)).size !== value.partitions.length) {
    context.addIssue({
      code: z.ZodIssueCode.custom,
      path: ["partitions"],
      message: "opportunity partition ids must be unique",
    });
  }
});

function candidateTimes(startTime: string, endTime: string): Set<string> {
  const minute = (value: string) => {
    const [hour, part] = value.split(":").map(Number);
    return hour * 60 + part;
  };
  const time = (value: number) => (
    `${String(Math.floor(value / 60)).padStart(2, "0")}:${String(value % 60).padStart(2, "0")}`
  );
  const end = minute(endTime);
  let current = minute(startTime);
  const result = new Set([time(current)]);
  while (current !== end) {
    current = (current + 1) % 1_440;
    result.add(time(current));
  }
  return result;
}

const differenceApiSchema = z.object({
  success: z.literal(true),
  endpoint: z.literal("dynamic_rectification_opportunities"),
  case_id: z.string().trim().min(1),
  scoring_version: z.literal("birth-time-choice-scoring-v2"),
  current_range: apiRangeSchema,
  opportunities: z.array(opportunitySchema),
  asked_question_fingerprints: z.array(z.string().trim().min(1)),
  candidate_partition_fingerprints: z.array(z.string().trim().min(1)),
  recent_range_history: z.array(apiRangeSchema),
  candidate_model: z.record(z.unknown()),
}).strict().superRefine((value, context) => {
  if (new Set(value.opportunities.map((item) => item.opportunity_id)).size !== value.opportunities.length) {
    context.addIssue({
      code: z.ZodIssueCode.custom,
      path: ["opportunities"],
      message: "opportunity ids must be unique",
    });
  }
  const expected = candidateTimes(value.current_range.start_time, value.current_range.end_time);
  value.opportunities.forEach((opportunity, opportunityIndex) => {
    opportunity.partitions.forEach((partition, partitionIndex) => {
      const actual = Object.keys(partition.candidate_scores);
      if (actual.length !== expected.size || actual.some((item) => !expected.has(item))) {
        context.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["opportunities", opportunityIndex, "partitions", partitionIndex, "candidate_scores"],
          message: "candidate scores must exactly match the current range",
        });
      }
    });
  });
});

const winningSegmentSchema = z.object({
  start_time: candidateTimeSchema,
  end_time: candidateTimeSchema,
  representative_time: candidateTimeSchema,
  width_minutes: z.number().int(),
}).strict();
const dynamicScoreApiSchema = z.object({
  success: z.literal(true),
  endpoint: z.literal("dynamic_rectification_score"),
  result_id: z.string().uuid(),
  confidence: z.enum(["low", "medium", "high"]),
  can_apply: z.boolean(),
  winning_segment: winningSegmentSchema.nullable(),
  event_count: z.number().int(),
  domain_count: z.number().int(),
  top_score: z.number().finite(),
  second_score: z.number().finite(),
  margin_percent: z.number().finite(),
  reasons: z.array(z.string()),
  evidence: z.array(z.never()).max(0),
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
});

export function parseCandidateDifferenceBuild(value: unknown): CandidateDifferenceBuild {
  const parsed = differenceApiSchema.parse(value);
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
  const parsed = dynamicScoreApiSchema.parse(value);
  const segment = parsed.winning_segment;
  const candidate = candidateResultSchema.parse({
    resultId: parsed.result_id,
    confidence: parsed.confidence,
    canApply: parsed.can_apply,
    winningSegment: segment && {
      startTime: segment.start_time,
      endTime: segment.end_time,
      representativeTime: segment.representative_time,
      widthMinutes: segment.width_minutes,
    },
    eventCount: parsed.event_count,
    domainCount: parsed.domain_count,
    topScore: parsed.top_score,
    secondScore: parsed.second_score,
    marginPercent: parsed.margin_percent,
    reasons: parsed.reasons,
    evidence: [],
    algorithmVersion: parsed.algorithm_version,
  });
  return dynamicChoiceScoringResultSchema.parse({
    candidate,
    evidenceMode: parsed.evidence_mode,
    effectiveAnswerCount: parsed.effective_answer_count,
    dimensionCount: parsed.dimension_count,
  });
}
