import { z } from "zod";
import type { CalculationSpec, CandidateMinute, LifeEventRevision } from "./contracts.ts";
import { rectificationV4AlgorithmVersion } from "./contracts.ts";

const responseSchema = z.object({
  result_id: z.string().uuid(),
  algorithm_version: z.literal(rectificationV4AlgorithmVersion),
  calculation_spec_hash: z.string().regex(/^[a-f0-9]{64}$/),
  candidate_scores: z.array(z.object({
    time: z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/),
    score: z.number().finite(),
    supporting_event_ids: z.array(z.string().uuid()),
    conflicting_event_ids: z.array(z.string().uuid()),
  }).strict()).min(1).max(1_440),
  robustness: z.object({
    neighbor_support_minutes: z.number().int().nonnegative(),
    leave_one_out_retention_rate: z.number().finite().min(0).max(1),
    date_sensitivity_retention_rate: z.number().finite().min(0).max(1),
  }).passthrough(),
  missing_layers: z.array(z.string()),
  can_confirm_exact_minute: z.literal(false),
}).passthrough();

export type CandidateEngineResult = Readonly<{
  resultId: string;
  calculationSpecHash: string;
  candidates: readonly CandidateMinute[];
  robustness: {
    readonly neighborSupportMinutes: number;
    readonly leaveOneOutRetentionRate: number;
    readonly dateSensitivityRetentionRate: number;
  };
  missingLayers: readonly string[];
}>;

export interface RectificationV4CandidateEngine {
  score(input: { readonly calculationSpec: CalculationSpec; readonly events: readonly LifeEventRevision[] }): Promise<CandidateEngineResult>;
}

export function createRectificationV4CandidateEngine(options: {
  readonly apiBase: string;
  readonly fetchImpl?: typeof fetch;
}): RectificationV4CandidateEngine {
  const fetchImpl = options.fetchImpl ?? fetch;
  return {
    async score({ calculationSpec, events }) {
      const response = await fetchImpl(`${options.apiBase}/api/active_rectification_events_v4`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          birth_date: calculationSpec.birthDate,
          start_time: calculationSpec.candidateRange.start,
          end_time: calculationSpec.candidateRange.end,
          lat: calculationSpec.latitude,
          lon: calculationSpec.longitude,
          tz: calculationSpec.timezoneOffsetHours,
          events: events.map((event) => ({
            id: event.eventId,
            domain: event.domain,
            event_kind: event.eventKind,
            date_start: event.dateRange.start,
            date_end: event.dateRange.end,
            precision: event.dateRange.precision,
            summary: event.summary,
          })),
        }),
        signal: AbortSignal.timeout(5 * 60_000),
      });
      const payload: unknown = await response.json();
      if (!response.ok) throw new Error(`rectification_v4_engine_${response.status}`);
      const parsed = responseSchema.parse(payload);
      return {
        resultId: parsed.result_id,
        calculationSpecHash: parsed.calculation_spec_hash,
        candidates: parsed.candidate_scores.map((candidate) => ({
          time: candidate.time,
          score: candidate.score,
          supportingEventIds: candidate.supporting_event_ids,
          conflictingEventIds: candidate.conflicting_event_ids,
        })),
        robustness: {
          neighborSupportMinutes: parsed.robustness.neighbor_support_minutes,
          leaveOneOutRetentionRate: parsed.robustness.leave_one_out_retention_rate,
          dateSensitivityRetentionRate: parsed.robustness.date_sensitivity_retention_rate,
        },
        missingLayers: parsed.missing_layers,
      };
    },
  };
}
