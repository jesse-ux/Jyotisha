import {
  evidenceDraftProposalSchema,
  lifeEventSchema,
  type EvidenceDraftProposal,
} from "./birth-time-evidence.ts";
import {
  currentJourneyTurn,
  persistedJourneyResponse,
  storedJourneyResponse,
} from "./birth-time-journey-response.ts";
import {
  confirmDraftTransition,
  draftMatchesQuestion,
  finishTransition,
  pauseTransition,
  questionFromTurn,
  reviewDraftTransition,
  skipQuestionTransition,
  type EvidenceQuestionIdentity,
} from "./birth-time-journey-transitions.ts";
import type { EvidenceDraft } from "./birth-time-journey-turn.ts";
import { persistGuidedJourneyTurn } from "./birth-time-scoring-job-persistence.ts";
import type { JourneyTurnPersistencePorts } from "./birth-time-scoring-job-persistence.ts";
import type {
  StoredRectificationCase,
  VersionedJourneyResponse,
} from "./birth-time-journey-service.ts";

type ActionFailure = "case_not_found" | "invalid_turn" | "invalid_draft";

export class BirthTimeJourneyActionError extends Error {
  readonly name = "BirthTimeJourneyActionError";
  readonly reason: ActionFailure;
  readonly caseId: string;

  constructor(reason: ActionFailure, caseId: string) {
    super(`Birth-time journey action ${reason} for ${caseId}`);
    this.reason = reason;
    this.caseId = caseId;
  }
}

type MutationContext = {
  readonly ports: JourneyTurnPersistencePorts;
  readonly stored: StoredRectificationCase;
  readonly expectedVersion: number;
  readonly actionId: string;
};

async function actionContext(input: {
  readonly ports: JourneyTurnPersistencePorts;
  readonly userId: string;
  readonly caseId: string;
  readonly expectedVersion: number;
  readonly actionId: string;
}): Promise<MutationContext> {
  const stored = await input.ports.store.loadCase(input.userId, input.caseId);
  if (!stored) throw new BirthTimeJourneyActionError("case_not_found", input.caseId);
  return {
    ports: input.ports,
    stored,
    expectedVersion: input.expectedVersion,
    actionId: input.actionId,
  };
}

async function replayed(context: MutationContext): Promise<boolean> {
  const receipt = context.actionId.toLowerCase();
  if (!context.stored.processedActionIds?.includes(receipt)) return false;
  await context.ports.store.saveTurn(
    context.stored,
    context.expectedVersion,
    context.actionId,
  );
  return true;
}

function requireQuestionContext(stored: StoredRectificationCase): {
  readonly current: ReturnType<typeof currentJourneyTurn>;
  readonly question: EvidenceQuestionIdentity;
  readonly draft: EvidenceDraft | null;
} {
  const current = currentJourneyTurn(stored);
  const question = questionFromTurn(current);
  if (question) return { current, question, draft: null };
  const draft = stored.evidenceDraft ?? current.evidenceDraft;
  if (
    current.nextAction.kind !== "review_evidence_draft"
    || current.nextAction.draftId !== draft?.draftId
  ) {
    throw new BirthTimeJourneyActionError("invalid_turn", stored.id);
  }
  return {
    current,
    question: {
      questionId: draft.questionId,
      phase: current.progress.adaptiveRound > 0 ? "adaptive" : "baseline",
      domain: draft.domain,
    },
    draft,
  };
}

function requireDraft(
  stored: StoredRectificationCase,
  draftId: string,
): { readonly current: ReturnType<typeof currentJourneyTurn>; readonly draft: EvidenceDraft } {
  const current = currentJourneyTurn(stored);
  const draft = stored.evidenceDraft ?? current.evidenceDraft;
  if (
    current.nextAction.kind !== "review_evidence_draft"
    || current.nextAction.draftId !== draftId
    || draft?.draftId !== draftId
    || draft.needsReview
    || !draftMatchesQuestion(draft, current.progress.adaptiveRound)
  ) {
    throw new BirthTimeJourneyActionError("invalid_draft", stored.id);
  }
  return { current, draft };
}

export function createJourneyTurnActions(ports: JourneyTurnPersistencePorts) {
  async function context(
    userId: string,
    caseId: string,
    actionId: string,
    expectedVersion: number,
  ) {
    return actionContext({ ports, userId, caseId, actionId, expectedVersion });
  }

  async function mutate(
    userId: string,
    caseId: string,
    actionId: string,
    expectedVersion: number,
    transition: (stored: StoredRectificationCase) => StoredRectificationCase,
    response: (stored: StoredRectificationCase) => VersionedJourneyResponse = storedJourneyResponse,
  ) {
    const mutation = await context(userId, caseId, actionId, expectedVersion);
    const duplicate = await replayed(mutation);
    if (duplicate) return response(mutation.stored);
    const saved = await persistGuidedJourneyTurn(
      mutation.ports,
      transition(mutation.stored),
      mutation.expectedVersion,
      mutation.actionId,
    );
    return response(saved);
  }

  return {
    async proposeEvidenceDraft(
      userId: string,
      caseId: string,
      actionId: string,
      expectedVersion: number,
      proposalInput: EvidenceDraftProposal,
    ) {
      return mutate(userId, caseId, actionId, expectedVersion, (stored) => {
        const { current, question, draft: currentDraft } = requireQuestionContext(stored);
        if (currentDraft && !currentDraft.needsReview) {
          throw new BirthTimeJourneyActionError("invalid_turn", caseId);
        }
        const proposal = evidenceDraftProposalSchema.parse(proposalInput);
        if (proposal.domain !== question.domain) {
          throw new BirthTimeJourneyActionError("invalid_draft", caseId);
        }
        const draftId = globalThis.crypto.randomUUID();
        const candidate = {
          id: draftId,
          domain: question.domain,
          precision: proposal.precision,
          date: proposal.date,
        };
        const draft: EvidenceDraft = {
          draftId,
          questionId: question.questionId,
          domain: question.domain,
          precision: proposal.precision,
          date: proposal.date,
          status: "draft",
          needsReview: !lifeEventSchema.safeParse(candidate).success,
        };
        return reviewDraftTransition({
          stored,
          current,
          question,
          draft,
          nextVersion: expectedVersion + 1,
        });
      });
    },

    async confirmEvidenceDraft(
      userId: string,
      caseId: string,
      actionId: string,
      expectedVersion: number,
      draftId: string,
    ) {
      return mutate(userId, caseId, actionId, expectedVersion, (stored) => {
        const { current, draft } = requireDraft(stored, draftId);
        const event = lifeEventSchema.parse({
          id: draft.draftId,
          domain: draft.domain,
          precision: draft.precision,
          date: draft.date,
        });
        return confirmDraftTransition({
          stored,
          current,
          event,
          scoreJobId: globalThis.crypto.randomUUID(),
          nextVersion: expectedVersion + 1,
        });
      });
    },

    async skipEvidenceQuestion(
      userId: string,
      caseId: string,
      actionId: string,
      expectedVersion: number,
    ) {
      return mutate(userId, caseId, actionId, expectedVersion, (stored) => {
        const { question } = requireQuestionContext(stored);
        return skipQuestionTransition({ stored, question, nextVersion: expectedVersion + 1 });
      });
    },

    async pause(
      userId: string,
      caseId: string,
      actionId: string,
      expectedVersion: number,
    ) {
      return mutate(userId, caseId, actionId, expectedVersion, (stored) => {
        const { current } = requireQuestionContext(stored);
        return pauseTransition(stored, current, expectedVersion + 1);
      }, persistedJourneyResponse);
    },

    async finishWithCurrentRange(
      userId: string,
      caseId: string,
      actionId: string,
      expectedVersion: number,
    ) {
      return mutate(userId, caseId, actionId, expectedVersion, (stored) => {
        const current = currentJourneyTurn(stored);
        return finishTransition(stored, current.progress.adaptiveRound, expectedVersion + 1);
      });
    },
  };
}
