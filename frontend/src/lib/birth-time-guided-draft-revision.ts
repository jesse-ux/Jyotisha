import { lifeEventSchema } from "./birth-time-evidence.ts";
import { currentJourneyTurn, storedJourneyResponse } from "./birth-time-journey-response.ts";
import type { VersionedJourneyResponse } from "./birth-time-journey-service.ts";
import type { JourneyTurnPersistencePorts } from "./birth-time-scoring-job-persistence.ts";
import { BirthTimeJourneyActionError } from "./birth-time-journey-actions.ts";
import { StaleJourneyTurnError } from "./birth-time-journey-turn-persistence.ts";
import type { EvidenceDatePrecision } from "./birth-time-question-planner.ts";

type ProposeDraft = (
  userId: string,
  caseId: string,
  actionId: string,
  expectedVersion: number,
  proposal: { readonly domain: "education" | "relocation" | "relationship" | "career" | "health_pressure"; readonly precision: EvidenceDatePrecision; readonly date: string },
) => Promise<VersionedJourneyResponse>;
type DraftRevision = {
  readonly userId: string;
  readonly caseId: string;
  readonly actionId: string;
  readonly expectedVersion: number;
  readonly precision: EvidenceDatePrecision;
  readonly date: string;
};

export function createGuidedDraftRevisionActions(
  ports: JourneyTurnPersistencePorts,
  proposeDraft: ProposeDraft,
) {
  return {
    async revise(input: DraftRevision) {
      const stored = await ports.store.loadCase(input.userId, input.caseId);
      if (!stored) throw new BirthTimeJourneyActionError("case_not_found", input.caseId);
      if (stored.processedActionIds?.includes(input.actionId.toLowerCase())) {
        return storedJourneyResponse(stored);
      }
      const currentVersion = stored.turnVersion ?? 0;
      if (currentVersion !== input.expectedVersion) {
        throw new StaleJourneyTurnError(stored.id, input.expectedVersion, currentVersion);
      }
      const current = currentJourneyTurn(stored);
      const draft = stored.evidenceDraft ?? current.evidenceDraft;
      if (
        current.nextAction.kind !== "review_evidence_draft"
        || current.nextAction.draftId !== draft?.draftId
      ) throw new BirthTimeJourneyActionError("invalid_turn", input.caseId);
      lifeEventSchema.parse({ id: draft.draftId, domain: draft.domain, precision: input.precision, date: input.date });
      return proposeDraft(input.userId, input.caseId, input.actionId, input.expectedVersion, {
        domain: draft.domain,
        precision: input.precision,
        date: input.date,
      });
    },
  };
}
