import {
  parseCandidateResult,
  parseRectificationQuestionnaire,
  parseRectificationScoring,
} from "./birth-time-journey-adapters.ts";
import {
  parseCandidateDifferenceBuild,
  parseDynamicChoiceScoring,
} from "./birth-time-journey-dynamic-adapters.ts";
import type {
  BirthTimeJourneyEngine,
  DifferencePacketInput,
  DynamicChoiceScoreInput,
  JourneyEventScoreInput,
} from "./birth-time-journey-service.ts";

export class BirthTimeJourneyEngineError extends Error {
  readonly name = "BirthTimeJourneyEngineError";
  readonly status: number;

  constructor(status: number) {
    super(`Jyotish birth-time engine returned ${status}`);
    this.status = status;
  }
}

export class BirthTimeJourneyEngineConfigurationError extends Error {
  readonly name = "BirthTimeJourneyEngineConfigurationError";

  constructor() {
    super("Dynamic Jyotish rectification is not configured");
  }
}

export type JourneyEngineFetch = (
  url: string,
  init: RequestInit,
) => Promise<{
  readonly ok: boolean;
  readonly status: number;
  json(): Promise<unknown>;
}>;

export type JourneyEngineWire = {
  post(input: {
    readonly path: string;
    readonly body: unknown;
    readonly authentication: "legacy" | "dynamic";
  }): Promise<unknown>;
};

export function createJourneyEngineWire(options: {
  readonly apiBase: string;
  readonly dynamicToken: string | null;
  readonly fetchImpl: JourneyEngineFetch;
  readonly signalFactory?: (timeoutMs: number) => AbortSignal;
}): JourneyEngineWire {
  const signalFactory = options.signalFactory
    ?? ((timeoutMs: number) => AbortSignal.timeout(timeoutMs));
  return {
    async post(input) {
      const token = options.dynamicToken?.trim();
      if (input.authentication === "dynamic" && !token) {
        throw new BirthTimeJourneyEngineConfigurationError();
      }
      const response = await options.fetchImpl(`${options.apiBase}${input.path}`, {
        method: "POST",
        headers: {
          "content-type": "application/json",
          ...(input.authentication === "dynamic" ? { authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(input.body),
        signal: signalFactory(45_000),
      });
      const payload = await response.json();
      if (!response.ok) throw new BirthTimeJourneyEngineError(response.status);
      return payload;
    },
  };
}

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

export function createJourneyEngineMethods(wire: JourneyEngineWire): BirthTimeJourneyEngine {
  return {
    async scan(input) {
      const payload = await wire.post({
        path: "/api/active_rectification_questions",
        authentication: "legacy",
        body: {
          birth_time: input.birthTime,
          uncertainty_minutes: input.uncertaintyMinutes,
          step_minutes: 1,
          lat: input.lat,
          lon: input.lon,
          tz: input.tz,
          ayanamsa: input.ayanamsa,
        },
      });
      return { questionnaire: parseRectificationQuestionnaire(payload) };
    },
    async score(input) {
      const payload = await wire.post({
        path: "/api/active_rectification_score",
        authentication: "legacy",
        body: { questionnaire: input.questionnaire.raw, answers: input.answers },
      });
      return parseRectificationScoring(payload);
    },
    async scoreEvents(input) {
      const payload = await wire.post({
        path: "/api/active_rectification_events",
        authentication: "legacy",
        body: eventScorePayload(input),
      });
      return parseCandidateResult(payload);
    },
    async buildDifferencePacket(input) {
      const payload = await wire.post({
        path: "/api/dynamic_rectification_opportunities",
        authentication: "dynamic",
        body: differencePacketPayload(input),
      });
      return parseCandidateDifferenceBuild(payload);
    },
    async scoreChoices(input) {
      const payload = await wire.post({
        path: "/api/dynamic_rectification_score",
        authentication: "dynamic",
        body: dynamicChoiceScorePayload(input),
      });
      return parseDynamicChoiceScoring(payload);
    },
  };
}
