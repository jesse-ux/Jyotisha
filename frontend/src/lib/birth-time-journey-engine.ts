import "server-only";

import {
  createJourneyEngineMethods,
  createJourneyEngineWire,
} from "./birth-time-journey-engine-model.ts";
import type { BirthTimeJourneyEngine } from "./birth-time-journey-service.ts";
import { resolveDynamicRectificationToken } from "./birth-time-dynamic-token.ts";

export {
  BirthTimeJourneyEngineConfigurationError,
  BirthTimeJourneyEngineError,
} from "./birth-time-journey-engine-model.ts";

export function createJyotishBirthTimeJourneyEngine(
  apiBase = process.env.JYOTISH_API_BASE ?? "http://127.0.0.1:5200",
): BirthTimeJourneyEngine {
  return createJourneyEngineMethods(createJourneyEngineWire({
    apiBase,
    dynamicToken: resolveDynamicRectificationToken(
      process.env.JYOTISH_DYNAMIC_RECTIFICATION_TOKEN,
      process.env.SUPABASE_SERVICE_ROLE_KEY,
    ),
    fetchImpl: fetch,
  }));
}
