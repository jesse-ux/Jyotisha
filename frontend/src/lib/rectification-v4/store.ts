import type {
  CandidateSnapshot,
  LifeEventRevision,
  RectificationV4Case,
  RectificationV4Job,
  RectificationV4Phase,
  RectificationV4Question,
  RectificationV4Turn,
} from "./contracts.ts";
export type { RectificationV4Turn } from "./contracts.ts";

export type ClaimedRectificationV4Job = Readonly<{
  job: RectificationV4Job;
  case: RectificationV4Case;
  turn: RectificationV4Turn;
  turns: readonly RectificationV4Turn[];
  events: readonly LifeEventRevision[];
  attemptedRefinementEventIds: readonly string[];
}>;

export type CompleteRectificationV4JobInput = Readonly<{
  workerId: string;
  jobId: string;
  expectedCaseVersion: number;
  inputEvidenceSetHash: string;
  outputEvidenceSetHash: string;
  calculationSpecHash: string;
  newEventRevisions: readonly LifeEventRevision[];
  snapshot: CandidateSnapshot | null;
  nextQuestion: RectificationV4Question | null;
  status: RectificationV4Case["status"];
  phase: RectificationV4Phase;
}>;

export interface RectificationV4Store {
  findActiveCase(userId: string): Promise<RectificationV4Case | null>;
  loadCase(userId: string, caseId: string): Promise<RectificationV4Case | null>;
  loadEvents(userId: string, caseId: string): Promise<readonly LifeEventRevision[]>;
  loadTurns(userId: string, caseId: string): Promise<readonly RectificationV4Turn[]>;
  createCase(input: { readonly case: RectificationV4Case; readonly actionId: string }): Promise<RectificationV4Case>;
  submitAnswer(input: {
    readonly userId: string;
    readonly caseId: string;
    readonly actionId: string;
    readonly expectedCaseVersion: number;
    readonly answer: string;
    readonly modelId: string | null;
    readonly question: RectificationV4Question;
    readonly jobId: string;
    readonly turnId: string;
    readonly now: string;
  }): Promise<{ readonly case: RectificationV4Case; readonly job: RectificationV4Job }>;
  reviseEvent(input: {
    readonly userId: string;
    readonly caseId: string;
    readonly actionId: string;
    readonly expectedCaseVersion: number;
    readonly revision: LifeEventRevision;
    readonly jobId: string;
    readonly now: string;
  }): Promise<{ readonly case: RectificationV4Case; readonly job: RectificationV4Job }>;
  transitionCase(input: {
    readonly userId: string;
    readonly caseId: string;
    readonly actionId: string;
    readonly expectedCaseVersion: number;
    readonly status: RectificationV4Case["status"];
    readonly phase: RectificationV4Phase;
    readonly acceptedRange?: { readonly start: string; readonly end: string } | null;
    readonly now: string;
  }): Promise<RectificationV4Case>;
  loadJob(userId: string, jobId: string): Promise<RectificationV4Job | null>;
  updateJobPhase(input: { readonly workerId: string; readonly jobId: string; readonly phase: RectificationV4Phase; readonly now: string }): Promise<void>;
  claimNextJob(workerId: string, now: string): Promise<ClaimedRectificationV4Job | null>;
  completeJob(input: CompleteRectificationV4JobInput, now: string): Promise<RectificationV4Case>;
  failJob(input: {
    readonly workerId: string;
    readonly jobId: string;
    readonly expectedCaseVersion: number;
    readonly errorCode: string;
    readonly restoreQuestion: RectificationV4Question | null;
    readonly now: string;
  }): Promise<void>;
}

export class RectificationV4StoreError extends Error {
  readonly name = "RectificationV4StoreError";
  constructor(readonly code: "not_found" | "stale_version" | "invalid_state" | "stale_job" | "lease_lost") {
    super(code);
  }
}
