type CandidateCompletionRequest = {
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

  return assessment?.id === request.caseId
    && assessment.user_id
    && assessment.status === "candidate"
    && assessment.candidate_result_id === request.resultId
    && action?.resultId === request.resultId
    && terminal
    && winner?.representativeTime === request.time
    ? request.time
    : null;
}
