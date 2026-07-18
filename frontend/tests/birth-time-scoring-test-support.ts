import type { CandidateResult } from "../src/lib/birth-time-evidence.ts";
import { createBirthTimeJourneyService } from "../src/lib/birth-time-journey-service.ts";
import type { BirthTimeJourneyStore } from "../src/lib/birth-time-journey-service.ts";
import {
  confirmActionId,
  draftActionId,
  existingCareerEvent,
  existingEducationEvent,
  guidedCase,
  journeyCaseId,
  memoryStore,
  unusedJourneyEngine,
} from "./birth-time-journey-test-support.ts";

export const scoringTestUserId = "user-1";

export async function pendingScoringFlow(input: {
  readonly score: () => Promise<CandidateResult>;
  readonly now?: () => Date;
  readonly transformStore?: (store: BirthTimeJourneyStore) => BirthTimeJourneyStore;
}) {
  const memory = memoryStore(guidedCase({
    version: 4,
    domain: "relationship",
    askedDomains: ["education", "career"],
    lifeEvents: [existingEducationEvent, existingCareerEvent],
  }));
  let calls = 0;
  const service = createBirthTimeJourneyService({
    store: input.transformStore?.(memory.store) ?? memory.store,
    engine: {
      ...unusedJourneyEngine,
      async scoreEvents() {
        calls += 1;
        return input.score();
      },
    },
    ...(input.now ? { now: input.now } : {}),
  });
  const proposed = await service.proposeEvidenceDraft(
    scoringTestUserId,
    journeyCaseId,
    draftActionId,
    4,
    { domain: "relationship", precision: "year", date: "2021" },
  );
  const pending = await service.confirmEvidenceDraft(
    scoringTestUserId,
    journeyCaseId,
    confirmActionId,
    proposed.turnVersion,
    proposed.evidenceDraft?.draftId ?? "",
  );
  if (pending.nextAction.kind !== "score_pending") {
    throw new TypeError("test setup did not create score_pending");
  }
  return {
    memory,
    service,
    pending,
    jobId: pending.nextAction.jobId,
    calls: () => calls,
  };
}
