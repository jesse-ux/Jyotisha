import { z } from "zod";
import type { VersionedJourneyResponse } from "./birth-time-journey-service.ts";

export const journeyMetricNames = [
  "turn_advanced",
  "draft_corrected",
  "journey_paused",
  "scoring_failed",
  "scoring_recovered",
  "illegal_snapshot",
] as const;

export type JourneyMetricName = (typeof journeyMetricNames)[number];

export const journeyMetricPhases = ["baseline", "adaptive", "result"] as const;
export type JourneyMetricPhase = (typeof journeyMetricPhases)[number];

export const journeyMetricConfidences = ["low", "medium", "high"] as const;
export type JourneyMetricConfidence = (typeof journeyMetricConfidences)[number];

export type JourneyMetricLabels = Readonly<{
  readonly phase: JourneyMetricPhase;
  readonly confidence?: JourneyMetricConfidence;
}>;

export type JourneyMetricPayload = Readonly<{
  readonly name: JourneyMetricName;
  readonly phase: JourneyMetricPhase;
  readonly confidence?: JourneyMetricConfidence;
}>;

export type JourneyMetricSink = (payload: JourneyMetricPayload) => void;
export type JourneyMetricRecorder = (
  name: JourneyMetricName,
  labels: JourneyMetricLabels,
) => void;

export type JourneyMetricEvent =
  | Readonly<{
    readonly kind: "transition";
    readonly name: Extract<JourneyMetricName, "turn_advanced" | "draft_corrected" | "journey_paused">;
    readonly phase: JourneyMetricPhase;
    readonly confidence?: JourneyMetricConfidence;
  }>
  | Readonly<{
    readonly kind: "scoring";
    readonly outcome: "failed";
    readonly phase: JourneyMetricPhase;
  }>
  | Readonly<{
    readonly kind: "scoring";
    readonly outcome: "succeeded";
    readonly priorFailure: boolean;
    readonly phase: JourneyMetricPhase;
    readonly confidence: JourneyMetricConfidence;
  }>
  | Readonly<{
    readonly kind: "error";
    readonly reason: "illegal_state" | "scoring_failure";
    readonly phase: JourneyMetricPhase;
  }>;

const metricPayloadSchema = z.object({
  name: z.enum(journeyMetricNames),
  phase: z.enum(journeyMetricPhases),
  confidence: z.enum(journeyMetricConfidences).optional(),
}).strict().readonly();

export const journeyMetricPayloadSchema = metricPayloadSchema;

function consoleSink(payload: JourneyMetricPayload): void {
  console.info("[birth-time-journey]", JSON.stringify(payload));
}

export function createJourneyTelemetry(
  sink: JourneyMetricSink = consoleSink,
): JourneyMetricRecorder {
  return (name, labels) => {
    const labelsValue = z.object({
      phase: z.enum(journeyMetricPhases),
      confidence: z.enum(journeyMetricConfidences).optional(),
    }).strict().parse(labels);
    const payload = metricPayloadSchema.parse({ name, ...labelsValue });
    try {
      sink(payload);
    } catch { // no-excuse-ok: catch
      return;
    }
  };
}

export const journeyMetric = createJourneyTelemetry();

function metricPayload(
  name: JourneyMetricName,
  phase: JourneyMetricPhase,
  confidence: JourneyMetricConfidence | undefined,
): JourneyMetricPayload {
  return confidence === undefined ? { name, phase } : { name, phase, confidence };
}

export function decideJourneyMetric(event: JourneyMetricEvent): JourneyMetricPayload | null {
  switch (event.kind) {
    case "transition":
      return metricPayload(event.name, event.phase, event.confidence);
    case "scoring":
      if (event.outcome === "failed") return metricPayload("scoring_failed", event.phase, undefined);
      if (event.outcome === "succeeded") return metricPayload(
        event.priorFailure ? "scoring_recovered" : "turn_advanced",
        event.phase,
        event.confidence,
      );
      return null;
    case "error":
      if (event.reason === "illegal_state") return metricPayload("illegal_snapshot", event.phase, undefined);
      if (event.reason === "scoring_failure") return metricPayload("scoring_failed", event.phase, undefined);
      return null;
    default: {
      const exhaustive: never = event;
      return exhaustive;
    }
  }
}

export function recordJourneyMetricEvent(
  event: JourneyMetricEvent,
  recorder: JourneyMetricRecorder = journeyMetric,
): void {
  const payload = decideJourneyMetric(event);
  if (payload === null) return;
  if (payload.confidence === undefined) {
    recorder(payload.name, { phase: payload.phase });
    return;
  }
  recorder(payload.name, { phase: payload.phase, confidence: payload.confidence });
}

export function journeyResponseMetricPhase(
  response: VersionedJourneyResponse,
): JourneyMetricPhase {
  switch (response.nextAction.kind) {
    case "ask_baseline_evidence":
      return "baseline";
    case "ask_adaptive_evidence":
      return "adaptive";
    case "review_evidence_draft":
    case "score_pending":
    case "retry_scoring":
      return response.progress.adaptiveRound > 0 ? "adaptive" : "baseline";
    case "paused":
      return response.candidateResult === null && response.progress.adaptiveRound === 0
        ? "baseline"
        : response.candidateResult === null
          ? "adaptive"
          : "result";
    case "present_low_result":
    case "present_medium_result":
    case "candidate_saved":
    case "request_candidate_confirmation":
    case "ready":
      return "result";
    default: {
      const exhaustive: never = response.nextAction;
      return exhaustive;
    }
  }
}

export function recordJourneyTransitionMetric(
  response: VersionedJourneyResponse,
  name: Extract<JourneyMetricName, "turn_advanced" | "draft_corrected" | "journey_paused">,
  recorder: JourneyMetricRecorder = journeyMetric,
): void {
  recordJourneyMetricEvent({
    kind: "transition",
    name,
    phase: journeyResponseMetricPhase(response),
    ...(response.candidateResult === null
      ? {}
      : { confidence: response.candidateResult.confidence }),
  }, recorder);
}

export function recordScoringJourneyMetric(
  before: VersionedJourneyResponse,
  after: VersionedJourneyResponse,
  recorder: JourneyMetricRecorder = journeyMetric,
): void {
  if (before.turnVersion === after.turnVersion) return;
  if (after.nextAction.kind === "retry_scoring") {
    recordJourneyMetricEvent({
      kind: "scoring",
      outcome: "failed",
      phase: journeyResponseMetricPhase(before),
    }, recorder);
    return;
  }
  if (
    before.nextAction.kind !== "score_pending"
    && before.nextAction.kind !== "retry_scoring"
  ) return;
  const confidence = after.candidateResult?.confidence;
  if (confidence === undefined) return;
  recordJourneyMetricEvent({
    kind: "scoring",
    outcome: "succeeded",
    priorFailure: before.nextAction.kind === "retry_scoring",
    phase: "result",
    confidence,
  }, recorder);
}
