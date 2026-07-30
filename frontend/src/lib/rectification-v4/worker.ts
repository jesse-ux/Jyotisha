import { randomUUID } from "node:crypto";
import { extractLifeEventEvidence } from "../conversational-rectification/evidence-extractor.ts";
import { processRectificationAgentTurn } from "../rectification-agent/orchestrator.ts";
import type { RectificationV4CandidateEngine } from "./candidate-engine.ts";
import type { LifeEventRevision, PendingEvidence, RectificationV4Question } from "./contracts.ts";
import { latestEventRevisions } from "./evidence-ledger.ts";
import { evidenceSetHash } from "./fingerprints.ts";
import type { RectificationV4Store, ResolvedPendingEvidence } from "./store.ts";

function sameDate(left: LifeEventRevision, right: LifeEventRevision): boolean {
  return left.dateRange.start === right.dateRange.start
    && left.dateRange.end === right.dateRange.end
    && left.dateRange.precision === right.dateRange.precision;
}

export function resolvedPendingEvidence(
  pendingEvidence: readonly PendingEvidence[],
  revisions: readonly LifeEventRevision[],
  existingRevisions: readonly LifeEventRevision[],
  asOfDate: string,
): readonly ResolvedPendingEvidence[] {
  const latestRevisionByEvent = new Map(latestEventRevisions(revisions).map((revision) => [revision.eventId, revision]));
  const existingByEvent = new Map(latestEventRevisions(existingRevisions).map((revision) => [revision.eventId, revision]));
  const resolves = (pending: PendingEvidence, revision: LifeEventRevision) => pending.reasonCode !== "date_unresolved"
    || !existingByEvent.get(revision.eventId)
    || !sameDate(existingByEvent.get(revision.eventId)!, revision);
  const resolved: ResolvedPendingEvidence[] = pendingEvidence.flatMap((pending) => {
    const revision = pending.targetEventId ? latestRevisionByEvent.get(pending.targetEventId) : null;
    return revision && resolves(pending, revision)
      ? [{ pendingEvidenceId: pending.id, resolvedEventId: revision.eventId }]
      : [];
  });
  const untargeted = pendingEvidence.filter((pending) => !pending.targetEventId && pending.reasonCode === "date_unresolved");
  const candidates = new Map(untargeted.map((pending) => {
    const semantics = extractLifeEventEvidence({
      rawText: pending.rawText,
      sourceTurnId: pending.turnId,
      asOfDate,
    });
    return [pending.id, [...latestRevisionByEvent.values()].filter((revision) => semantics.some((event) =>
      event.domain === revision.domain
      && event.eventKind === revision.eventKind
      && event.subject === revision.subject
      && event.relatedPerson === revision.relatedPerson,
    ))] as const;
  }));
  for (const pending of untargeted) {
    const matches = candidates.get(pending.id) ?? [];
    if (matches.length !== 1) continue;
    const revision = matches[0]!;
    if (!resolves(pending, revision)) continue;
    const competingPending = untargeted.filter((other) => candidates.get(other.id)?.some((match) => match.eventId === revision.eventId));
    if (competingPending.length === 1) resolved.push({ pendingEvidenceId: pending.id, resolvedEventId: revision.eventId });
  }
  return resolved;
}

export function createRectificationV4Worker(input: {
  readonly store: RectificationV4Store;
  readonly engine: RectificationV4CandidateEngine;
  readonly workerId?: string;
  readonly now?: () => Date;
}) {
  const workerId = input.workerId ?? randomUUID();
  const now = input.now ?? (() => new Date());
  return { async runOnce(): Promise<boolean> {
    const claimed = await input.store.claimNextJob(workerId, now().toISOString());
    if (!claimed) return false;
    try {
      const result = await processRectificationAgentTurn({
        claimed, engine: input.engine, now: now(),
        onPhase: (phase) => input.store.updateJobPhase({ workerId, jobId: claimed.job.id, phase, now: now().toISOString() }),
      });
      const completedAt = now().toISOString();
      await input.store.completeJob({
        workerId, jobId: claimed.job.id, expectedCaseVersion: claimed.case.version,
        inputEvidenceSetHash: claimed.case.evidenceSetHash,
        outputEvidenceSetHash: evidenceSetHash([...claimed.events, ...result.newEventRevisions]),
        calculationSpecHash: claimed.case.calculationSpecHash,
        newEventRevisions: result.newEventRevisions,
        pendingEvidence: result.pendingEvidence,
        resolvedPendingEvidence: resolvedPendingEvidence(
          claimed.pendingEvidence,
          result.newEventRevisions,
          claimed.events,
          completedAt.slice(0, 10),
        ),
        snapshot: result.snapshot,
        diagnostics: result.diagnostics,
        featureSnapshot: result.featureSnapshot,
        validatedDecision: result.validatedDecision,
        publicMessage: result.publicMessage,
        agentRun: result.agentRun,
        nextQuestion: result.nextQuestion,
        status: result.status,
        phase: result.phase,
      }, completedAt);
      return true;
    } catch (error) {
      const restoreQuestion: RectificationV4Question | null = claimed.turn.questionId && claimed.turn.questionDomain ? {
        id: claimed.turn.questionId, domain: claimed.turn.questionDomain, targetEventId: claimed.turn.questionTargetEventId,
        prompt: claimed.turn.question, recallCost: "low", reason: "上一轮处理没有完成，请重新提交这段经历。",
      } : null;
      await input.store.failJob({
        workerId, jobId: claimed.job.id, expectedCaseVersion: claimed.case.version,
        errorCode: error instanceof Error ? error.message.slice(0, 120) : "unknown_worker_error",
        restoreQuestion, now: now().toISOString(),
      });
      return true;
    }
  }};
}
