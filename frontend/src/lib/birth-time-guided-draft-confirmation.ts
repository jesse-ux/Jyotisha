import { lifeEventSchema } from "./birth-time-evidence.ts";
import type { JourneyClientResponse } from "./birth-time-journey-response-schema.ts";
import type { EvidenceDatePrecision } from "./birth-time-question-planner.ts";

type ConfirmDraftInput = {
  readonly turn: JourneyClientResponse;
  readonly precision: EvidenceDatePrecision;
  readonly date: string;
};

type RevisionCommand = {
  readonly caseId: string;
  readonly turnVersion: number;
  readonly precision: EvidenceDatePrecision;
  readonly date: string;
};

type ConfirmationCommand = {
  readonly caseId: string;
  readonly turnVersion: number;
  readonly draftId: string;
};

type ConfirmDraftPorts = {
  readonly revise: (command: RevisionCommand) => Promise<JourneyClientResponse>;
  readonly publish: (turn: JourneyClientResponse) => void;
  readonly confirm: (command: ConfirmationCommand) => Promise<JourneyClientResponse>;
};

export class GuidedDraftConfirmationError extends Error {
  readonly name = "GuidedDraftConfirmationError";
}

export async function confirmReviewedBirthTimeDraft(
  input: ConfirmDraftInput,
  ports: ConfirmDraftPorts,
): Promise<JourneyClientResponse> {
  const draft = input.turn.evidenceDraft;
  if (!draft) throw new GuidedDraftConfirmationError("当前没有可确认的经历草稿。");
  const parsed = lifeEventSchema.parse({
    id: draft.draftId,
    domain: draft.domain,
    precision: input.precision,
    date: input.date,
  });
  const revised = draft.precision === parsed.precision && draft.date === parsed.date
    ? input.turn
    : await ports.revise({
        caseId: input.turn.caseId,
        turnVersion: input.turn.turnVersion,
        precision: parsed.precision,
        date: parsed.date,
      });
  if (revised !== input.turn) ports.publish(revised);
  const currentDraft = revised.evidenceDraft;
  if (!currentDraft) throw new GuidedDraftConfirmationError("经历草稿已经变化，请使用最新内容。");
  return ports.confirm({
    caseId: revised.caseId,
    turnVersion: revised.turnVersion,
    draftId: currentDraft.draftId,
  });
}
