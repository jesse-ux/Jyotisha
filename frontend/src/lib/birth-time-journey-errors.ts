export class RectificationCaseNotFoundError extends Error {
  readonly name = "RectificationCaseNotFoundError";
  readonly caseId: string;

  constructor(caseId: string) {
    super(`Rectification case ${caseId} was not found`);
    this.caseId = caseId;
  }
}

export class RectificationQuestionsUnavailableError extends Error {
  readonly name = "RectificationQuestionsUnavailableError";
}
