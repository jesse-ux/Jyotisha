import type { AgentRun, CandidateFeatureSnapshot, DiagnosticsSummary, StoredPublicMessage, ValidatedDecision } from "../rectification-agent/contracts.ts";
import type {
  LifeEventRevision,
  PendingEvidence,
  RectificationV4Case,
  RectificationV4Job,
} from "./contracts.ts";
import type {
  ClaimedRectificationV4Job,
  CompleteRectificationV4JobInput,
  RectificationV4Store,
  RectificationV4Turn,
} from "./store.ts";
import { RectificationV4StoreError } from "./store.ts";
import { evidenceSetHash } from "./fingerprints.ts";

export function createRectificationV4MemoryStore(): RectificationV4Store & {
  readonly cases: Map<string, RectificationV4Case>;
  readonly jobs: Map<string, RectificationV4Job & { workerId: string | null; turnId: string }>;
  readonly diagnostics: Map<string, DiagnosticsSummary>;
  readonly featureSnapshots: Map<string, CandidateFeatureSnapshot>;
  readonly agentRuns: Map<string, AgentRun>;
  readonly publicMessages: Map<string, StoredPublicMessage>;
  readonly validatedDecisions: Map<string, ValidatedDecision>;
  readonly pendingEvidence: Map<string, PendingEvidence>;
} {
  const cases = new Map<string, RectificationV4Case>();
  const events = new Map<string, LifeEventRevision[]>();
  const turns = new Map<string, RectificationV4Turn>();
  const jobs = new Map<string, RectificationV4Job & { workerId: string | null; turnId: string }>();
  const actionResults = new Map<string, { caseId: string; jobId: string | null }>();
  const diagnostics = new Map<string, DiagnosticsSummary>();
  const featureSnapshots = new Map<string, CandidateFeatureSnapshot>();
  const agentRuns = new Map<string, AgentRun>();
  const publicMessages = new Map<string, StoredPublicMessage>();
  const validatedDecisions = new Map<string, ValidatedDecision>();
  const pendingEvidence = new Map<string, PendingEvidence>();

  function owned(userId: string, caseId: string): RectificationV4Case {
    const value = cases.get(caseId);
    if (!value || value.userId !== userId) throw new RectificationV4StoreError("not_found");
    return value;
  }

  return {
    cases,
    jobs,
    diagnostics,
    featureSnapshots,
    agentRuns,
    publicMessages,
    validatedDecisions,
    pendingEvidence,
    async findActiveCase(userId) {
      return [...cases.values()].find((value) => value.userId === userId
        && value.status !== "abandoned" && value.acceptedRange === null) ?? null;
    },
    async loadCase(userId, caseId) {
      const value = cases.get(caseId);
      return value?.userId === userId ? value : null;
    },
    async loadEvents(userId, caseId) {
      owned(userId, caseId);
      return events.get(caseId) ?? [];
    },
    async loadTurns(userId, caseId) {
      owned(userId, caseId);
      return [...turns.values()]
        .filter((turn) => turn.caseId === caseId)
        .sort((left, right) => left.caseVersion - right.caseVersion || left.createdAt.localeCompare(right.createdAt));
    },
    async loadAnalysisMessages(userId, caseId) {
      owned(userId, caseId);
      return [...jobs.values()]
        .filter((job) => job.caseId === caseId && publicMessages.get(job.id)?.analysisTrace)
        .sort((left, right) => turns.get(left.turnId)!.caseVersion - turns.get(right.turnId)!.caseVersion)
        .map((job) => ({ sourceTurnId: job.turnId, trace: publicMessages.get(job.id)!.analysisTrace! }));
    },
    async loadLatestValidatedDecision(userId, caseId) {
      const caseValue = cases.get(caseId);
      if (!caseValue || caseValue.userId !== userId) return null;
      const latest = [...agentRuns.values()]
        .filter((run) => run.caseId === caseId)
        .sort((left, right) => right.caseVersion - left.caseVersion || right.createdAt.localeCompare(left.createdAt))[0];
      return latest ? validatedDecisions.get(latest.jobId) ?? latest.validatedDecision : null;
    },
    async loadActionCase(userId, actionId) {
      const replay = actionResults.get(`${userId}:${actionId}`);
      return replay ? owned(userId, replay.caseId) : null;
    },
    async createCase(input) {
      const replay = actionResults.get(`${input.case.userId}:${input.actionId}`);
      if (replay) return owned(input.case.userId, replay.caseId);
      const active = [...cases.values()].find((value) => value.userId === input.case.userId
        && value.status !== "abandoned" && value.acceptedRange === null);
      if (active?.calculationSpecHash === input.case.calculationSpecHash) {
        actionResults.set(`${input.case.userId}:${input.actionId}`, { caseId: active.id, jobId: null });
        return active;
      }
      if (active) {
        cases.set(active.id, { ...active, status: "abandoned", phase: "complete", currentQuestion: null, updatedAt: input.case.createdAt });
        for (const [jobId, job] of jobs) {
          if (job.caseId === active.id && ["pending", "processing"].includes(job.status)) {
            jobs.set(jobId, { ...job, status: "stale", updatedAt: input.case.createdAt });
          }
        }
      }
      cases.set(input.case.id, input.case);
      events.set(input.case.id, []);
      actionResults.set(`${input.case.userId}:${input.actionId}`, { caseId: input.case.id, jobId: null });
      return input.case;
    },
    async replaceCurrentQuestion(input) {
      const key = `${input.userId}:${input.actionId}`;
      const replay = actionResults.get(key);
      if (replay) return owned(input.userId, replay.caseId);
      const current = owned(input.userId, input.caseId);
      if (current.version !== input.expectedCaseVersion) throw new RectificationV4StoreError("stale_version");
      if (current.deploymentMode !== "v5_agent"
        || !["awaiting_answer", "range_ready"].includes(current.status)
        || !current.currentQuestion) throw new RectificationV4StoreError("invalid_state");
      const updated: RectificationV4Case = {
        ...current,
        version: current.version + 1,
        currentQuestion: {
          ...input.question,
          domain: current.currentQuestion.domain,
          targetEventId: current.currentQuestion.targetEventId,
        },
        updatedAt: input.now,
      };
      cases.set(current.id, updated);
      actionResults.set(key, { caseId: current.id, jobId: null });
      return updated;
    },
    async submitAnswer(input) {
      const key = `${input.userId}:${input.actionId}`;
      const replay = actionResults.get(key);
      if (replay?.jobId) return { case: owned(input.userId, replay.caseId), job: jobs.get(replay.jobId)! };
      const current = owned(input.userId, input.caseId);
      if (current.version !== input.expectedCaseVersion) throw new RectificationV4StoreError("stale_version");
      if (!["awaiting_answer", "range_ready"].includes(current.status)) throw new RectificationV4StoreError("invalid_state");
      const version = current.version + 1;
      const updated: RectificationV4Case = {
        ...current, version, status: "processing", phase: "extracting_evidence", currentQuestion: null, updatedAt: input.now,
      };
      const turn: RectificationV4Turn = {
        id: input.turnId,
        caseId: input.caseId,
        caseVersion: version,
        questionId: input.question.id,
        questionDomain: input.question.domain,
        questionTargetEventId: input.question.targetEventId,
        question: input.question.prompt,
        answer: input.answer,
        modelId: input.modelId,
        actionId: input.actionId,
        createdAt: input.now,
      };
      const job: RectificationV4Job & { workerId: string | null; turnId: string } = {
        id: input.jobId,
        caseId: input.caseId,
        status: "pending",
        phase: "extracting_evidence",
        expectedCaseVersion: version,
        evidenceSetHash: current.evidenceSetHash,
        calculationSpecHash: current.calculationSpecHash,
        errorCode: null,
        createdAt: input.now,
        updatedAt: input.now,
        workerId: null,
        turnId: turn.id,
      };
      cases.set(current.id, updated);
      turns.set(turn.id, turn);
      jobs.set(job.id, job);
      actionResults.set(key, { caseId: current.id, jobId: job.id });
      return { case: updated, job };
    },
    async reviseEvent(input) {
      const key = `${input.userId}:${input.actionId}`;
      const replay = actionResults.get(key);
      if (replay?.jobId) return { case: owned(input.userId, replay.caseId), job: jobs.get(replay.jobId)! };
      const current = owned(input.userId, input.caseId);
      if (current.version !== input.expectedCaseVersion) throw new RectificationV4StoreError("stale_version");
      const nextEvents = [...(events.get(current.id) ?? []), input.revision];
      events.set(current.id, nextEvents);
      const version = current.version + 1;
      const updated = {
        ...current, version, status: "processing" as const, phase: "scoring_candidates" as const,
        evidenceSetHash: evidenceSetHash(nextEvents), currentQuestion: null, updatedAt: input.now,
      };
      const turn: RectificationV4Turn = {
        id: input.revision.id, caseId: current.id, caseVersion: version, questionId: null, questionDomain: null,
        questionTargetEventId: null, question: "修订事件", answer: "", modelId: null, actionId: input.actionId, createdAt: input.now,
      };
      const job = {
        id: input.jobId, caseId: current.id, status: "pending" as const, phase: "scoring_candidates" as const,
        expectedCaseVersion: version, evidenceSetHash: updated.evidenceSetHash,
        calculationSpecHash: current.calculationSpecHash, errorCode: null, createdAt: input.now, updatedAt: input.now,
        workerId: null, turnId: turn.id,
      };
      cases.set(current.id, updated);
      turns.set(turn.id, turn);
      jobs.set(job.id, job);
      actionResults.set(key, { caseId: current.id, jobId: job.id });
      return { case: updated, job };
    },
    async transitionCase(input) {
      const key = `${input.userId}:${input.actionId}`;
      const replay = actionResults.get(key);
      if (replay) return owned(input.userId, replay.caseId);
      const current = owned(input.userId, input.caseId);
      if (current.version !== input.expectedCaseVersion) throw new RectificationV4StoreError("stale_version");
      const updated = {
        ...current,
        version: current.version + 1,
        status: input.status,
        phase: input.phase,
        acceptedRange: input.acceptedRange === undefined ? current.acceptedRange : input.acceptedRange,
        updatedAt: input.now,
      };
      cases.set(current.id, updated);
      actionResults.set(key, { caseId: current.id, jobId: null });
      return updated;
    },
    async loadJob(userId, jobId) {
      const job = jobs.get(jobId);
      if (!job) return null;
      owned(userId, job.caseId);
      return job;
    },
    async loadActiveJob(userId, caseId) {
      owned(userId, caseId);
      return [...jobs.values()]
        .filter((job) => job.caseId === caseId && ["pending", "processing"].includes(job.status))
        .sort((left, right) => right.createdAt.localeCompare(left.createdAt))[0] ?? null;
    },
    async updateJobPhase(input) {
      const job = jobs.get(input.jobId);
      if (!job || job.workerId !== input.workerId || job.status !== "processing") throw new RectificationV4StoreError("lease_lost");
      jobs.set(job.id, { ...job, phase: input.phase, updatedAt: input.now });
      const current = cases.get(job.caseId)!;
      cases.set(current.id, { ...current, phase: input.phase, updatedAt: input.now });
    },
    async claimNextJob(workerId, now): Promise<ClaimedRectificationV4Job | null> {
      const job = [...jobs.values()].find((value) => value.status === "pending");
      if (!job) return null;
      const claimed = { ...job, status: "processing" as const, workerId, updatedAt: now };
      jobs.set(job.id, claimed);
      const caseValue = cases.get(job.caseId)!;
      const caseTurns = [...turns.values()]
        .filter((turn) => turn.caseId === job.caseId)
        .sort((left, right) => left.caseVersion - right.caseVersion || left.createdAt.localeCompare(right.createdAt));
      return {
        job: claimed,
        case: caseValue,
        turn: turns.get(job.turnId)!,
        turns: caseTurns,
        events: events.get(job.caseId) ?? [],
        attemptedRefinementEventIds: [...new Set(
          [...turns.values()]
            .filter((turn) => turn.caseId === job.caseId && turn.questionTargetEventId)
            .map((turn) => turn.questionTargetEventId!),
        )],
      };
    },
    async completeJob(input: CompleteRectificationV4JobInput, now) {
      const job = jobs.get(input.jobId);
      if (!job || job.workerId !== input.workerId || job.status !== "processing") throw new RectificationV4StoreError("lease_lost");
      const current = cases.get(job.caseId)!;
      if (current.version !== input.expectedCaseVersion
        || current.evidenceSetHash !== input.inputEvidenceSetHash
        || current.calculationSpecHash !== input.calculationSpecHash) throw new RectificationV4StoreError("stale_job");
      const nextEvents = [...(events.get(current.id) ?? []), ...input.newEventRevisions];
      events.set(current.id, nextEvents);
      if (input.diagnostics) diagnostics.set(input.diagnostics.id, input.diagnostics);
      if (input.featureSnapshot) featureSnapshots.set(input.featureSnapshot.id, input.featureSnapshot);
      agentRuns.set(input.agentRun.id, input.agentRun);
      publicMessages.set(input.jobId, input.publicMessage);
      validatedDecisions.set(input.jobId, input.validatedDecision);
      for (const item of input.pendingEvidence) pendingEvidence.set(item.id, item);
      const updated: RectificationV4Case = {
        ...current,
        version: current.version + 1,
        evidenceSetHash: input.outputEvidenceSetHash,
        latestSnapshot: input.snapshot,
        agentMode: input.validatedDecision.mode,
        featureSnapshotId: input.featureSnapshot?.id ?? current.featureSnapshotId,
        latestDiagnosticsId: input.diagnostics?.id ?? current.latestDiagnosticsId,
        currentQuestion: input.nextQuestion,
        status: input.status,
        phase: input.phase,
        updatedAt: now,
      };
      cases.set(current.id, updated);
      jobs.set(job.id, { ...job, status: "completed", phase: input.phase, updatedAt: now });
      return updated;
    },
    async failJob(input) {
      const job = jobs.get(input.jobId);
      if (!job || job.workerId !== input.workerId) throw new RectificationV4StoreError("lease_lost");
      jobs.set(job.id, { ...job, status: "failed", errorCode: input.errorCode, updatedAt: input.now });
      const current = cases.get(job.caseId);
      if (current?.version === input.expectedCaseVersion) {
        cases.set(current.id, {
          ...current, status: "awaiting_answer", phase: "collecting_evidence",
          currentQuestion: input.restoreQuestion, updatedAt: input.now,
        });
      }
    },
  };
}
