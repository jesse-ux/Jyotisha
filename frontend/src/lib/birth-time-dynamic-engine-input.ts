import type {
  DifferencePacketInput,
  DynamicChoiceScoreInput,
  DynamicStoredRectificationCase,
} from "./birth-time-journey-service.ts";
import type { ServerChoiceEvidence } from "./birth-time-dynamic-choice-internal.ts";
import type { TimeRange } from "./birth-time-dynamic-choice.ts";

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
  if (model.opportunity_model_version !== "birth-time-opportunity-model-v2") return null;
  const persistedRange = model.range;
  if (typeof persistedRange !== "object" || persistedRange === null) return model;
  const value = persistedRange as Readonly<Record<string, unknown>>;
  return value.start_time === range.startTime && value.end_time === range.endTime
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
    dismissedOpportunityIds: stored.dynamicControl.dismissedOpportunityIds,
    questionFingerprints: stored.dynamicControl.questionFingerprints,
    partitionFingerprints: stored.dynamicControl.partitionFingerprints,
    recentRanges: stored.dynamicControl.recentRanges,
    candidateModel: candidateModelForRange(stored.candidateModel, range),
  };
}
