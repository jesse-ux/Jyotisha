import { z } from "zod";
import {
  birthTimeAssessmentSchema,
  type BirthTimeAssessment,
} from "./birth-time-journey.ts";
import type {
  RectificationAnswer,
  RectificationQuestionnaire,
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
  options: z.array(optionSchema).optional(),
});

const signSchema = z.object({ sign: z.string().trim().min(1) }).nullable().optional();
const sampleSchema = z.object({
  ascendant: signSchema,
  varga_lagna: z.object({
    D9: signSchema,
    D10: signSchema,
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
    questions: parsed.questions.map((question) => ({
      id: question.id,
      prompt: question.prompt,
      ...(question.options ? { options: question.options } : {}),
    })),
    samples: parsed.candidate_scan.samples.map((sample) => ({
      ascendantSign: sample.ascendant?.sign ?? null,
      d9Sign: sample.varga_lagna?.D9?.sign ?? null,
      d10Sign: sample.varga_lagna?.D10?.sign ?? null,
    })),
    raw: parsed,
  };
}

export function parseRectificationScoring(value: unknown) {
  const parsed = scoringSchema.parse(value);
  return {
    answeredCount: parsed.answered_count,
    candidateClusterRankings: parsed.candidate_cluster_rankings,
    raw: parsed,
  };
}

export function parseRectificationAnswer(value: unknown): RectificationAnswer {
  return z.enum(["A", "B", "C", "D"]).parse(value);
}
