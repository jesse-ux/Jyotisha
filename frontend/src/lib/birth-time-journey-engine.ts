import "server-only";

import {
  parseCandidateDifferenceBuild,
  parseDynamicChoiceScoring,
  parseRectificationQuestionnaire,
  parseRectificationScoring,
  parseCandidateResult,
} from "./birth-time-journey-adapters.ts";
import {
  differencePacketPayload,
  dynamicChoiceScorePayload,
  eventScorePayload,
} from "./birth-time-journey-engine-model.ts";
import type { DynamicBirthTimeJourneyEngine } from "./birth-time-journey-service.ts";

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

async function postJson(
  apiBase: string,
  path: string,
  body: unknown,
  authorization?: string,
): Promise<unknown> {
  const response = await fetch(`${apiBase}${path}`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      ...(authorization ? { authorization } : {}),
    },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(45_000),
  });
  const payload: unknown = await response.json();
  if (!response.ok) throw new BirthTimeJourneyEngineError(response.status);
  return payload;
}

function dynamicAuthorization(): string {
  const token = process.env.JYOTISH_DYNAMIC_RECTIFICATION_TOKEN?.trim();
  if (!token) throw new BirthTimeJourneyEngineConfigurationError();
  return `Bearer ${token}`;
}

export function createJyotishBirthTimeJourneyEngine(
  apiBase = process.env.JYOTISH_API_BASE ?? "http://127.0.0.1:5200",
): DynamicBirthTimeJourneyEngine {
  return {
    async scan(input) {
      const payload = await postJson(apiBase, "/api/active_rectification_questions", {
        birth_time: input.birthTime,
        uncertainty_minutes: input.uncertaintyMinutes,
        step_minutes: 1,
        lat: input.lat,
        lon: input.lon,
        tz: input.tz,
        ayanamsa: input.ayanamsa,
      });
      return { questionnaire: parseRectificationQuestionnaire(payload) };
    },

    async score(input) {
      const payload = await postJson(apiBase, "/api/active_rectification_score", {
        questionnaire: input.questionnaire.raw,
        answers: input.answers,
      });
      return parseRectificationScoring(payload);
    },

    async scoreEvents(input) {
      const payload = await postJson(
        apiBase,
        "/api/active_rectification_events",
        eventScorePayload(input),
      );
      return parseCandidateResult(payload);
    },

    async buildDifferencePacket(input) {
      const payload = await postJson(
        apiBase,
        "/api/dynamic_rectification_opportunities",
        differencePacketPayload(input),
        dynamicAuthorization(),
      );
      return parseCandidateDifferenceBuild(payload);
    },

    async scoreChoices(input) {
      const payload = await postJson(
        apiBase,
        "/api/dynamic_rectification_score",
        dynamicChoiceScorePayload(input),
        dynamicAuthorization(),
      );
      return parseDynamicChoiceScoring(payload);
    },
  };
}
