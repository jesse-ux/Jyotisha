import { z } from "zod";
import type {
  DifferencePacketInput,
  DynamicChoiceScoreInput,
  DynamicStoredRectificationCase,
} from "./birth-time-journey-service.ts";
import type { ServerChoiceEvidence } from "./birth-time-dynamic-choice-internal.ts";
import type { TimeRange } from "./birth-time-dynamic-choice.ts";

const reusableCandidateModelSchema = z.object({
  opportunity_model_version: z.literal("birth-time-opportunity-model-v4"),
  historical_event_fingerprint: z.string().trim().min(1),
  range: z.object({ start_time: z.string(), end_time: z.string() }),
  windows: z.array(z.object({
    activations: z.record(z.string(), z.number().finite().nonnegative()),
    fact_selection_priority: z.number().finite().min(0).max(1),
    fact_priority_version: z.literal("birth-time-question-fact-priority-v1"),
    event_fact_selection_priority: z.number().finite().min(0).max(1),
    event_fact_priority_version: z.literal("birth-time-question-event-fact-priority-v1"),
  }).passthrough()),
}).passthrough();

export class BirthTimeDynamicEngineInputError extends Error {
  readonly name = "BirthTimeDynamicEngineInputError";
}

function rangeCandidateTimes(range: TimeRange): readonly string[] {
  const minute = (value: string) => {
    const [hour, part] = value.split(":").map(Number);
    return hour * 60 + part;
  };
  const time = (value: number) => (
    `${String(Math.floor(value / 60)).padStart(2, "0")}:${String(value % 60).padStart(2, "0")}`
  );
  const end = minute(range.endTime);
  let current = minute(range.startTime);
  const candidates = [time(current)];
  while (current !== end) {
    current = (current + 1) % 1_440;
    candidates.push(time(current));
  }
  return candidates;
}

function evidenceForRange(
  evidence: readonly ServerChoiceEvidence[],
  range: TimeRange,
): readonly ServerChoiceEvidence[] {
  const candidates = rangeCandidateTimes(range);
  return evidence.map((item) => {
    if (candidates.some((candidate) => !Object.hasOwn(item.candidateScores, candidate))) {
      return item;
    }
    return {
      ...item,
      candidateScores: Object.fromEntries(
        candidates.map((candidate) => [candidate, item.candidateScores[candidate]]),
      ),
    };
  });
}

function candidateModelForRange(
  model: Readonly<Record<string, unknown>> | null,
  range: TimeRange,
): Readonly<Record<string, unknown>> | null {
  if (model === null) return null;
  const parsed = reusableCandidateModelSchema.safeParse(model);
  if (!parsed.success) return null;
  return parsed.data.range.start_time === range.startTime
    && parsed.data.range.end_time === range.endTime
    ? model
    : null;
}

export function dynamicChoiceScoreInput(
  stored: DynamicStoredRectificationCase,
): DynamicChoiceScoreInput {
  return dynamicChoiceScoreInputForRange(
    stored,
    stored.dynamicTurnState.progress.currentRange,
  );
}

function dynamicChoiceScoreInputForRange(
  stored: DynamicStoredRectificationCase,
  range: TimeRange,
): DynamicChoiceScoreInput {
  const context = stored.eventContext;
  if (!context) throw new BirthTimeDynamicEngineInputError();
  return {
    birthDate: context.birthDate,
    startTime: range.startTime,
    endTime: range.endTime,
    lat: context.lat,
    lon: context.lon,
    tz: context.tz,
    evidence: evidenceForRange(stored.choiceEvidence, range),
  };
}

export function dynamicDifferenceInput(
  stored: DynamicStoredRectificationCase,
  range: TimeRange = stored.dynamicTurnState.progress.currentRange,
): DifferencePacketInput {
  return {
    caseId: stored.id,
    asOfDate: stored.dynamicControl.asOfDate,
    ...dynamicChoiceScoreInputForRange(stored, range),
    events: stored.lifeEvents ?? [],
    dismissedOpportunityIds: stored.dynamicControl.dismissedOpportunityIds,
    questionFingerprints: stored.dynamicControl.questionFingerprints,
    partitionFingerprints: stored.dynamicControl.partitionFingerprints,
    recentRanges: stored.dynamicControl.recentRanges,
    candidateModel: candidateModelForRange(stored.candidateModel, range),
  };
}
