import { createScoringJobSpec } from "./birth-time-scoring-job.ts";
import type {
  BirthTimeJourneyStore,
  LegacyStoredRectificationCase,
  StoredRectificationCase,
} from "./birth-time-journey-service.ts";

export type JourneyTurnPersistencePorts = {
  readonly store: BirthTimeJourneyStore;
  readonly now?: () => Date;
};

export async function persistGuidedJourneyTurn(
  ports: JourneyTurnPersistencePorts,
  value: LegacyStoredRectificationCase,
  expectedVersion: number,
  actionId: string,
): Promise<StoredRectificationCase> {
  const nextAction = value.turnState?.nextAction;
  if (nextAction?.kind !== "score_pending") {
    return ports.store.saveTurn(value, expectedVersion, actionId);
  }
  return ports.store.createScoringJob(
    value,
    expectedVersion,
    actionId,
    createScoringJobSpec(
      nextAction.jobId,
      value.lifeEvents ?? [],
      ports.now?.() ?? new Date(),
    ),
  );
}
