import { z } from "zod";
import {
  birthTimeAssessmentSchema,
  candidateResultSchema,
  type BirthTimeAssessment,
} from "./birth-time-journey.ts";
import type { CandidateResult } from "./birth-time-evidence.ts";
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
    D2: signSchema,
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
  "finance",
  "health_pressure",
]);
const candidateResultApiSchema = z.object({
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
  evidence: z.array(z.object({
    event_id: z.string().uuid(),
    domain: eventDomainSchema,
    candidate_time: z.string(),
    rule_ids: z.array(z.string()),
    points: z.number(),
  })),
  algorithm_version: z.string(),
  technique_contract: z.object({
    calculation_status: z.enum(["not_started", "evaluated"]),
    used_divisional_charts: z.array(z.string()),
    used_arudha: z.array(z.string()),
    dasha_tracks: z.array(z.string()),
    missing_layers: z.array(z.string()),
    auxiliary_layers: z.array(z.string()).default([]),
    hard_blockers: z.array(z.string()),
  }).optional(),
}).passthrough();

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
      ...(sample.varga_lagna?.D2?.sign ? { d2Sign: sample.varga_lagna.D2.sign } : {}),
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
    ...(parsed.technique_contract ? { techniqueReceipt: {
      calculationStatus: parsed.technique_contract.calculation_status,
      usedDivisionalCharts: parsed.technique_contract.used_divisional_charts,
      usedArudha: parsed.technique_contract.used_arudha,
      dashaTracks: parsed.technique_contract.dasha_tracks,
      missingLayers: parsed.technique_contract.missing_layers,
      auxiliaryLayers: parsed.technique_contract.auxiliary_layers,
      hardBlockers: parsed.technique_contract.hard_blockers,
    } } : {}),
  });
}
