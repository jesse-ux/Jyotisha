import { randomUUID } from "node:crypto";
import { processRectificationAgentTurn } from "../rectification-agent/orchestrator.ts";
import type { RectificationV4CandidateEngine } from "./candidate-engine.ts";
import type { RectificationV4Question } from "./contracts.ts";
import { evidenceSetHash } from "./fingerprints.ts";
import type { RectificationV4Store } from "./store.ts";

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
      await input.store.completeJob({
        workerId, jobId: claimed.job.id, expectedCaseVersion: claimed.case.version,
        inputEvidenceSetHash: claimed.case.evidenceSetHash,
        outputEvidenceSetHash: evidenceSetHash([...claimed.events, ...result.newEventRevisions]),
        calculationSpecHash: claimed.case.calculationSpecHash,
        newEventRevisions: result.newEventRevisions,
        pendingEvidence: result.pendingEvidence,
        snapshot: result.snapshot,
        diagnostics: result.diagnostics,
        featureSnapshot: result.featureSnapshot,
        validatedDecision: result.validatedDecision,
        publicMessage: result.publicMessage,
        agentRun: result.agentRun,
        nextQuestion: result.nextQuestion,
        status: result.status,
        phase: result.phase,
      }, now().toISOString());
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
