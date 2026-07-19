import type { JourneyClientResponse } from "./birth-time-journey-response-schema.ts";

export type GuidedTerminalPath =
  | {
    readonly kind: "edit_birth_time_details";
    readonly preservesCase: true;
    readonly appliesCandidateTime: false;
  }
  | {
    readonly kind: "complete_with_candidate";
    readonly time: string;
    readonly preservesCase: true;
    readonly appliesCandidateTime: true;
  };

export function guidedTerminalPath(journey: JourneyClientResponse): GuidedTerminalPath | null {
  const kind = journey.nextAction.kind;
  const winner = journey.candidateResult?.winningSegment;
  if (journey.journeyProtocol === "dynamic-choice-v2"
    && winner
    && (kind === "present_low_result" || kind === "present_medium_result" || kind === "candidate_saved")) {
    return {
      kind: "complete_with_candidate",
      time: winner.representativeTime,
      preservesCase: true,
      appliesCandidateTime: true,
    };
  }
  return kind === "present_low_result" || kind === "candidate_saved"
    ? { kind: "edit_birth_time_details", preservesCase: true, appliesCandidateTime: false }
    : null;
}
