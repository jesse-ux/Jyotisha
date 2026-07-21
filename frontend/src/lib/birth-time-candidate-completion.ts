type CandidateCompletionRequest = {
  readonly userId: string;
  readonly caseId: string;
  readonly resultId: string;
  readonly time: string;
};

function record(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === "object"
    ? value as Record<string, unknown>
    : null;
}

export function candidateWorkingTime(
  stored: unknown,
  request: CandidateCompletionRequest,
): string | null {
  const assessment = record(stored);
  const candidate = record(assessment?.candidate_result);
  const winner = record(candidate?.winningSegment);
  const turn = record(assessment?.turn_state);
  const action = record(turn?.nextAction);
  const actionKind = action?.kind;
  const terminal = actionKind === "present_low_result"
    || actionKind === "present_medium_result"
    || actionKind === "candidate_saved";
  const terminalStatusMatches = actionKind === "present_low_result"
    ? assessment?.status === "rectifying"
    : (actionKind === "present_medium_result" || actionKind === "candidate_saved")
      && assessment?.status === "candidate";

  return assessment?.id === request.caseId
    && assessment?.user_id === request.userId
    && assessment?.journey_protocol === "legacy-guided-v1"
    && terminalStatusMatches
    && assessment.candidate_result_id === request.resultId
    && action?.resultId === request.resultId
    && terminal
    && winner?.representativeTime === request.time
    ? request.time
    : null;
}
