import type { JourneyClientResponse } from "./birth-time-journey-response-schema.ts";

export type GuidedTerminalPath = {
  readonly kind: "edit_birth_time_details";
  readonly preservesCase: true;
  readonly appliesCandidateTime: false;
};

export function guidedTerminalPath(journey: JourneyClientResponse): GuidedTerminalPath | null {
  const kind = journey.nextAction.kind;
  return kind === "present_low_result" || kind === "candidate_saved"
    ? { kind: "edit_birth_time_details", preservesCase: true, appliesCandidateTime: false }
    : null;
}
