import { z } from "zod";
import type { CalculationSpec, CandidateMinute, LifeEventRevision } from "./contracts.ts";
import { rectificationV4AlgorithmVersion } from "./contracts.ts";

const uuid = z.string().uuid();
const hash = z.string().regex(/^[a-f0-9]{64}$/);
const dateSensitivitySchema = z.object({
  event_id: uuid,
  declared_date_range: z.object({ start: z.string(), end: z.string(), precision: z.string() }),
  sample_dates: z.array(z.string()).min(1).max(12),
  winner_retention_rate: z.number().min(0).max(1),
  score_variance: z.number().nonnegative(),
  candidate_cluster_retention_rate: z.number().min(0).max(1),
}).passthrough();
const diagnosticsSchema = z.object({
  primary_cluster_retention_rate: z.number().min(0).max(1),
  leave_one_event_out_retention_rate: z.number().min(0).max(1),
  leave_one_domain_out_retention_rate: z.number().min(0).max(1),
  date_sensitivity_retention_rate: z.number().min(0).max(1),
  neighbor_support_minutes: z.number().int().nonnegative(),
  primary_secondary_margin_percent: z.number().min(0).max(100),
  cluster_mass_ratio: z.number().min(0).max(1),
  unstable_event_ids: z.array(uuid),
  most_discriminating_layers: z.array(z.string()),
  event_date_sensitivity: z.array(dateSensitivitySchema),
  candidate_splits: z.array(z.object({
    left_cluster: z.object({ start: z.string(), end: z.string() }),
    right_cluster: z.object({ start: z.string(), end: z.string() }),
    technique_layers: z.array(z.string()),
    event_ids: z.array(uuid),
  }).passthrough()),
}).passthrough();
const featureSchema = z.object({
  calculation_spec_hash: hash,
  algorithm_version: z.literal(rectificationV4AlgorithmVersion),
  candidate_count: z.number().int().positive(),
  feature_hash: hash,
  features: z.array(z.object({
    time: z.string(),
    ascendant_degree: z.number().nullable(),
    ascendant_sign_index: z.number().int().min(0).max(11).nullable(),
    varga_ascendants: z.record(z.string(), z.number().int().min(0).max(11)),
    arudha_signs: z.object({ A7: z.number().int().min(0).max(11).nullable(), A10: z.number().int().min(0).max(11).nullable(), UL: z.number().int().min(0).max(11).nullable() }),
    available_layers: z.array(z.string()), blocked_layers: z.array(z.string()),
    fingerprints: z.record(z.string(), z.string()),
  }).passthrough()),
}).passthrough();
const responseSchema = z.object({
  result_id: uuid,
  algorithm_version: z.literal(rectificationV4AlgorithmVersion),
  calculation_spec_hash: hash,
  candidate_scores: z.array(z.object({
    time: z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/), score: z.number().finite(),
    supporting_event_ids: z.array(uuid), conflicting_event_ids: z.array(uuid),
  }).strict()).min(1).max(1_440),
  robustness: z.object({
    neighbor_support_minutes: z.number().int().nonnegative(),
    leave_one_out_retention_rate: z.number().min(0).max(1),
    leave_one_domain_out_retention_rate: z.number().min(0).max(1),
    date_sensitivity_retention_rate: z.number().min(0).max(1),
  }).passthrough(),
  diagnostics: diagnosticsSchema,
  candidate_feature_snapshot: featureSchema,
  event_contribution_matrix: z.record(z.string(), z.record(z.string(), z.object({
    points: z.number(), rule_ids: z.array(z.string()), technique_layers: z.array(z.string()),
  }).passthrough())),
  missing_layers: z.array(z.string()),
  can_confirm_exact_minute: z.literal(false),
}).passthrough();

export type CandidateEngineResult = Readonly<{
  resultId: string;
  calculationSpecHash: string;
  candidates: readonly CandidateMinute[];
  robustness: { neighborSupportMinutes: number; leaveOneOutRetentionRate: number; leaveOneDomainOutRetentionRate: number; dateSensitivityRetentionRate: number };
  diagnostics: z.infer<typeof diagnosticsSchema>;
  featureSnapshot: z.infer<typeof featureSchema>;
  contributionMatrix: z.infer<typeof responseSchema>["event_contribution_matrix"];
  missingLayers: readonly string[];
}>;

export interface RectificationV4CandidateEngine {
  score(input: { readonly calculationSpec: CalculationSpec; readonly events: readonly LifeEventRevision[] }): Promise<CandidateEngineResult>;
}

export function createRectificationV4CandidateEngine(options: { readonly apiBase: string; readonly fetchImpl?: typeof fetch }): RectificationV4CandidateEngine {
  const fetchImpl = options.fetchImpl ?? fetch;
  return { async score({ calculationSpec, events }) {
    const response = await fetchImpl(`${options.apiBase}/api/rectification/v5/score`, {
      method: "POST", headers: { "content-type": "application/json" }, signal: AbortSignal.timeout(5 * 60_000),
      body: JSON.stringify({
        birth_date: calculationSpec.birthDate, start_time: calculationSpec.candidateRange.start, end_time: calculationSpec.candidateRange.end,
        lat: calculationSpec.latitude, lon: calculationSpec.longitude, tz: calculationSpec.timezoneOffsetHours,
        ...(Object.hasOwn(calculationSpec, "birthTimeSource") ? { birth_time_source: calculationSpec.birthTimeSource } : {}),
        ...(Object.hasOwn(calculationSpec, "timezoneId") ? { timezone_id: calculationSpec.timezoneId } : {}),
        ...(Object.hasOwn(calculationSpec, "timezoneSource") ? { timezone_source: calculationSpec.timezoneSource } : {}),
        ...(Object.hasOwn(calculationSpec, "localTimeStatus") ? { local_time_status: calculationSpec.localTimeStatus } : {}),
        events: events.map((event) => ({
          id: event.eventId, domain: event.domain, event_kind: event.eventKind,
          date_start: event.dateRange.start, date_end: event.dateRange.end, precision: event.dateRange.precision, summary: event.summary,
          ...(Object.hasOwn(event, "dateSource") ? { date_source: event.dateSource } : {}),
          ...(Object.hasOwn(event, "dateReliability") ? { date_reliability: event.dateReliability } : {}),
          ...(Object.hasOwn(event, "dateCorroboration") ? { date_corroboration: event.dateCorroboration } : {}),
          ...(Object.hasOwn(event, "dateConflictStatus") ? { date_conflict_status: event.dateConflictStatus } : {}),
        })),
      }),
    });
    const payload: unknown = await response.json();
    if (!response.ok) throw new Error(`rectification_v5_engine_${response.status}`);
    const parsed = responseSchema.parse(payload);
    return {
      resultId: parsed.result_id,
      calculationSpecHash: parsed.calculation_spec_hash,
      candidates: parsed.candidate_scores.map((candidate) => ({ time: candidate.time, score: candidate.score, supportingEventIds: candidate.supporting_event_ids, conflictingEventIds: candidate.conflicting_event_ids })),
      robustness: {
        neighborSupportMinutes: parsed.robustness.neighbor_support_minutes,
        leaveOneOutRetentionRate: parsed.robustness.leave_one_out_retention_rate,
        leaveOneDomainOutRetentionRate: parsed.robustness.leave_one_domain_out_retention_rate,
        dateSensitivityRetentionRate: parsed.robustness.date_sensitivity_retention_rate,
      },
      diagnostics: parsed.diagnostics,
      featureSnapshot: parsed.candidate_feature_snapshot,
      contributionMatrix: parsed.event_contribution_matrix,
      missingLayers: parsed.missing_layers,
    };
  }};
}
