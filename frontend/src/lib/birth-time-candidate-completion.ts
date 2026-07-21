type CandidateCompletionRequest = {
  readonly userId: string;
  readonly caseId: string;
  readonly resultId: string;
  readonly time: string;
};

/** Direct adoption was superseded by versioned high-confidence confirmation. */
export function candidateWorkingTime(
  _stored: unknown,
  _request: CandidateCompletionRequest,
): string | null {
  return null;
}
