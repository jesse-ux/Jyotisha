import { createDynamicJourneyActions } from "./birth-time-dynamic-actions.ts";
import { createDynamicScoringService } from "./birth-time-dynamic-scoring-service.ts";
import type {
  BirthTimeJourneyPorts,
} from "./birth-time-journey-service.ts";

export function createDynamicJourneyMethods(ports: BirthTimeJourneyPorts) {
  const actions = createDynamicJourneyActions(ports);
  const scoring = createDynamicScoringService(ports);
  return {
    ...actions,
    generateDynamicQuestion: actions.loadDynamicQuestionBuild,
    pollDynamicScoringJob: scoring.poll,
  };
}
