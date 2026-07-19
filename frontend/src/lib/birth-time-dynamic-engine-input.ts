import type {
  DifferencePacketInput,
  DynamicChoiceScoreInput,
  DynamicStoredRectificationCase,
} from "./birth-time-journey-service.ts";

export class BirthTimeDynamicEngineInputError extends Error {
  readonly name = "BirthTimeDynamicEngineInputError";
}

export function dynamicChoiceScoreInput(
  stored: DynamicStoredRectificationCase,
): DynamicChoiceScoreInput {
  const context = stored.eventContext;
  if (!context) throw new BirthTimeDynamicEngineInputError();
  const range = stored.dynamicTurnState.progress.currentRange;
  return {
    birthDate: context.birthDate,
    startTime: range.startTime,
    endTime: range.endTime,
    lat: context.lat,
    lon: context.lon,
    tz: context.tz,
    evidence: stored.choiceEvidence,
  };
}

export function dynamicDifferenceInput(
  stored: DynamicStoredRectificationCase,
): DifferencePacketInput {
  return {
    caseId: stored.id,
    asOfDate: stored.dynamicControl.asOfDate,
    ...dynamicChoiceScoreInput(stored),
    dismissedOpportunityIds: stored.dynamicControl.dismissedOpportunityIds,
    questionFingerprints: stored.dynamicControl.questionFingerprints,
    partitionFingerprints: stored.dynamicControl.partitionFingerprints,
    recentRanges: stored.dynamicControl.recentRanges,
    candidateModel: stored.candidateModel,
  };
}
