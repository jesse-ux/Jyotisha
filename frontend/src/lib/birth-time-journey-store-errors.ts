export type JourneyStoreOperation =
  | "insert_case"
  | "update_profile"
  | "load_case"
  | "update_case";

export class BirthTimeJourneyStoreError extends Error {
  readonly name = "BirthTimeJourneyStoreError";
  readonly operation: JourneyStoreOperation;

  constructor(operation: JourneyStoreOperation) {
    super(`Birth-time journey persistence failed during ${operation}`);
    this.operation = operation;
  }
}

export class StaleJourneyTurnError extends Error {
  readonly name = "StaleJourneyTurnError";
  readonly caseId: string;
  readonly expectedVersion: number;
  readonly currentVersion: number;

  constructor(caseId: string, expectedVersion: number, currentVersion: number) {
    super(`Journey turn ${caseId} is stale at version ${expectedVersion}`);
    this.caseId = caseId;
    this.expectedVersion = expectedVersion;
    this.currentVersion = currentVersion;
  }
}
