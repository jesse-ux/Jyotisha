import type {
  DifferencePacketInput,
  DynamicChoiceScoreInput,
  JourneyEventScoreInput,
} from "./birth-time-journey-service.ts";

export function eventScorePayload(input: JourneyEventScoreInput) {
  return {
    birth_date: input.birthDate,
    start_time: input.startTime,
    end_time: input.endTime,
    lat: input.lat,
    lon: input.lon,
    tz: input.tz,
    events: input.events.map((event) => ({
      id: event.id,
      domain: event.domain,
      date: event.date,
      precision: event.precision,
    })),
  } as const;
}

function choiceEvidencePayload(input: DifferencePacketInput["evidence"]) {
  return input.map((item) => ({
    question_id: item.questionId,
    opportunity_id: item.opportunityId,
    partition_id: item.partitionId,
    dimension_code: item.dimensionCode,
    candidate_scores: item.candidateScores,
    information_gain: item.informationGain,
  }));
}

export function differencePacketPayload(input: DifferencePacketInput) {
  return {
    case_id: input.caseId,
    as_of_date: input.asOfDate,
    birth_date: input.birthDate,
    start_time: input.startTime,
    end_time: input.endTime,
    lat: input.lat,
    lon: input.lon,
    tz: input.tz,
    evidence: choiceEvidencePayload(input.evidence),
    dismissed_opportunity_ids: input.dismissedOpportunityIds,
    question_fingerprints: input.questionFingerprints,
    partition_fingerprints: input.partitionFingerprints,
    recent_ranges: input.recentRanges.map((range) => ({
      start_time: range.startTime,
      end_time: range.endTime,
    })),
    candidate_model: input.candidateModel,
  } as const;
}

export function dynamicChoiceScorePayload(input: DynamicChoiceScoreInput) {
  return {
    birth_date: input.birthDate,
    start_time: input.startTime,
    end_time: input.endTime,
    lat: input.lat,
    lon: input.lon,
    tz: input.tz,
    choice_evidence: choiceEvidencePayload(input.evidence),
  } as const;
}
