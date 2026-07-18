import { z } from "zod";
import { birthTimeJourneyRequestSchema } from "./birth-time-journey-request.ts";
import { parseJourneyResponse } from "./birth-time-journey-client.ts";
import type { JourneyClientResponse } from "./birth-time-journey-response-schema.ts";
import type { EvidenceDatePrecision } from "./birth-time-question-planner.ts";
import { postJson } from "./birth-time-client-transport.ts";

type GuidedMutation = {
  readonly caseId: string;
  readonly actionId: string;
  readonly turnVersion: number;
};
type DraftRevision = GuidedMutation & {
  readonly precision: EvidenceDatePrecision;
  readonly date: string;
};
type CandidateSave = GuidedMutation & { readonly resultId: string };
type CandidateConfirmation = CandidateSave & { readonly time: string };

const errorPayloadSchema = z.object({
  message: z.string().optional(),
  error: z.string().optional(),
}).readonly();

export class GuidedBirthTimeRequestError extends Error {
  readonly name = "GuidedBirthTimeRequestError";
  readonly status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function send(event: Readonly<Record<string, unknown>>): Promise<JourneyClientResponse> {
  const request = birthTimeJourneyRequestSchema.parse(event);
  const { response, payload: body } = await postJson({
    url: "/api/birth-time-journey",
    body: JSON.stringify(request),
    retryLostResponse: true,
  });
  if (!response.ok) {
    const parsed = errorPayloadSchema.safeParse(body);
    const message = parsed.success
      ? parsed.data.message ?? parsed.data.error ?? "生时校正暂时不可用"
      : "生时校正暂时不可用";
    throw new GuidedBirthTimeRequestError(response.status, message);
  }
  return parseJourneyResponse(body);
}

export function reviseBirthTimeEvidenceDraft(
  input: DraftRevision,
) {
  return send({
    type: "revise_evidence_draft",
    ...input,
  });
}

export function saveGuidedBirthTimeCandidate(
  input: CandidateSave,
) {
  return send({ type: "save_guided_candidate", ...input });
}

export function confirmGuidedBirthTimeCandidate(
  input: CandidateConfirmation,
) {
  return send({ type: "confirm_guided_candidate", ...input });
}
