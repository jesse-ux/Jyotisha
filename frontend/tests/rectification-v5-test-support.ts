import { randomUUID } from "node:crypto";
import type { CandidateEngineResult } from "../src/lib/rectification-v4/candidate-engine.ts";
import { vedAstroPostValidationSchema, type VedAstroPostValidation } from "../src/lib/rectification-agent/contracts.ts";
import type { CalculationSpec, CandidateMinute, LifeEventRevision } from "../src/lib/rectification-v4/contracts.ts";
import { rectificationV4AlgorithmVersion } from "../src/lib/rectification-v4/contracts.ts";
import { calculationSpecHash } from "../src/lib/rectification-v4/fingerprints.ts";

export function v5EngineResult(
  calculationSpec: CalculationSpec,
  events: readonly LifeEventRevision[],
  candidates: readonly CandidateMinute[] = [
    { time: "05:13", score: 100, supportingEventIds: events.map((event) => event.eventId), conflictingEventIds: [] },
    { time: "05:14", score: 99, supportingEventIds: events.map((event) => event.eventId), conflictingEventIds: [] },
    { time: "05:15", score: 98, supportingEventIds: events.map((event) => event.eventId), conflictingEventIds: [] },
  ],
): CandidateEngineResult {
  const specHash = calculationSpecHash(calculationSpec);
  return {
    resultId: randomUUID(),
    calculationSpecHash: specHash,
    candidates,
    robustness: {
      neighborSupportMinutes: 3,
      leaveOneOutRetentionRate: 1,
      leaveOneDomainOutRetentionRate: 1,
      dateSensitivityRetentionRate: .9,
    },
    diagnostics: {
      primary_cluster_retention_rate: 1,
      leave_one_event_out_retention_rate: 1,
      leave_one_domain_out_retention_rate: 1,
      date_sensitivity_retention_rate: .9,
      neighbor_support_minutes: 3,
      primary_secondary_margin_percent: 20,
      cluster_mass_ratio: .9,
      unstable_event_ids: [],
      most_discriminating_layers: ["D9", "D10"],
      event_date_sensitivity: events.map((event) => ({
        event_id: event.eventId,
        declared_date_range: { start: event.dateRange.start, end: event.dateRange.end, precision: event.dateRange.precision },
        sample_dates: [event.dateRange.start, event.dateRange.end].filter((value, index, values) => values.indexOf(value) === index),
        winner_retention_rate: 1,
        score_variance: 0,
        candidate_cluster_retention_rate: 1,
      })),
      candidate_splits: [],
    },
    featureSnapshot: {
      calculation_spec_hash: specHash,
      algorithm_version: rectificationV4AlgorithmVersion,
      candidate_count: candidates.length,
      feature_hash: "f".repeat(64),
      features: candidates.map((candidate, index) => ({
        time: candidate.time,
        ascendant_degree: index,
        ascendant_sign_index: 0,
        varga_ascendants: { D1: 0, D9: index % 12 },
        arudha_signs: { A7: 1, A10: 2, UL: 3 },
        available_layers: ["D1", "D9", "D10"],
        blocked_layers: ["KP_cusps"],
        fingerprints: { static: `${candidate.time}:${index}` },
      })),
    },
    contributionMatrix: Object.fromEntries(events.map((event) => [
      event.eventId,
      Object.fromEntries(candidates.map((candidate) => [candidate.time, {
        points: candidate.supportingEventIds.includes(event.eventId) ? 1 : candidate.conflictingEventIds.includes(event.eventId) ? -1 : 0,
        rule_ids: ["fixture:rule"],
        technique_layers: ["D9"],
      }])),
    ])),
    missingLayers: ["KP_cusps"],
  };
}

export function passingVedAstroValidation(
  candidateTimes: readonly [string, string],
  overrides: Partial<VedAstroPostValidation> = {},
): VedAstroPostValidation {
  return vedAstroPostValidationSchema.parse({
    contractVersion: "vedastro-post-validation-v1",
    provider: "vedastro_official",
    status: "pass",
    providerStatus: "pass",
    blockers: [],
    primaryCandidateTime: candidateTimes[0],
    runnerUpCandidateTime: candidateTimes[1],
    eligibleEventCount: 5,
    selectedEventCount: 3,
    unsupportedEventCount: 0,
    candidateMetrics: [
      { role: "primary", requestedEventCount: 3, successfulEventCount: 3, matchedEventCount: 3, eventHitCount: 5, signalLift: 4 },
      { role: "runner_up", requestedEventCount: 3, successfulEventCount: 3, matchedEventCount: 2, eventHitCount: 3, signalLift: 2 },
    ],
    minuteSensitiveValidation: { comparisonReady: true, discriminated: true, discriminatedLayers: ["D9"] },
    validationHash: "a".repeat(64),
    validatedAt: "2026-07-30T00:00:00.000Z",
    canConfirmExactMinute: false,
    ...overrides,
  });
}

export async function withV5Mode<T>(mode: "v4_legacy" | "v5_shadow" | "v5_agent", run: () => Promise<T>): Promise<T> {
  const keys = ["RECTIFICATION_AGENT_V5_ENABLED", "RECTIFICATION_AGENT_V5_SHADOW", "RECTIFICATION_AGENT_V5_CANARY_PERCENT"] as const;
  const before = Object.fromEntries(keys.map((key) => [key, process.env[key]]));
  process.env.RECTIFICATION_AGENT_V5_ENABLED = mode === "v4_legacy" ? "0" : "1";
  process.env.RECTIFICATION_AGENT_V5_SHADOW = mode === "v5_shadow" ? "1" : "0";
  process.env.RECTIFICATION_AGENT_V5_CANARY_PERCENT = "100";
  try { return await run(); } finally {
    for (const key of keys) {
      if (before[key] === undefined) delete process.env[key];
      else process.env[key] = before[key];
    }
  }
}
