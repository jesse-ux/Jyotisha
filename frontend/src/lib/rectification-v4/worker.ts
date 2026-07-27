import { randomUUID } from "node:crypto";
import type {
  CandidateSnapshot,
  LifeEventRevision,
  RectificationV4Case,
  RectificationV4Question,
} from "./contracts.ts";
import { rectificationV4AlgorithmVersion } from "./contracts.ts";
import type { RectificationV4CandidateEngine } from "./candidate-engine.ts";
import { buildCandidateClusters } from "./candidate-clusters.ts";
import { evaluateDecisionGate } from "./decision-gate.ts";
import { evidenceSetHash } from "./fingerprints.ts";
import { extractV4EventRevisions } from "./extraction.ts";
import { latestEventRevisions, scoreableEvents } from "./evidence-ledger.ts";
import { planNextQuestion } from "./question-planner.ts";
import type { ClaimedRectificationV4Job, RectificationV4Store } from "./store.ts";

export function createRectificationV4Worker(input: {
  readonly store: RectificationV4Store;
  readonly engine: RectificationV4CandidateEngine;
  readonly workerId?: string;
  readonly now?: () => Date;
  readonly questionAuthor?: (context: Readonly<{
    modelId: string | null;
    candidateRange: RectificationV4Case["calculationSpec"]["candidateRange"];
    snapshot: CandidateSnapshot | null;
    turns: ClaimedRectificationV4Job["turns"];
    events: readonly LifeEventRevision[];
    attemptedRefinementEventIds: readonly string[];
  }>) => Promise<RectificationV4Question>;
}) {
  const workerId = input.workerId ?? randomUUID();
  const now = input.now ?? (() => new Date());

  return {
    async runOnce(): Promise<boolean> {
      const claimed = await input.store.claimNextJob(workerId, now().toISOString());
      if (!claimed) return false;
      try {
        const extracted = claimed.turn.answer
          ? extractV4EventRevisions({
              answer: claimed.turn.answer,
              sourceTurnId: claimed.turn.id,
              asOfDate: now().toISOString().slice(0, 10),
              existing: claimed.events,
              targetEventId: claimed.turn.questionTargetEventId,
              now: now(),
            })
          : [];
        const events = latestEventRevisions([...claimed.events, ...extracted]);
        await input.store.updateJobPhase({ workerId, jobId: claimed.job.id, phase: "scoring_candidates", now: now().toISOString() });
        const scoreable = scoreableEvents(events);
        const domains = new Set(scoreable.map((event) => event.domain));
        let snapshot: CandidateSnapshot | null = null;
        if (scoreable.length >= 3 && domains.size >= 2) {
          const scored = await input.engine.score({ calculationSpec: claimed.case.calculationSpec, events: scoreable });
          await input.store.updateJobPhase({ workerId, jobId: claimed.job.id, phase: "checking_robustness", now: now().toISOString() });
          const clusters = buildCandidateClusters(scored.candidates);
          const robustness = {
            ...scored.robustness,
            calculationSpecHashMatched: scored.calculationSpecHash === claimed.case.calculationSpecHash,
          };
          const gate = evaluateDecisionGate({
            clusters,
            robustness,
            scoreableEventCount: scoreable.length,
            scoreableDomainCount: domains.size,
          });
          snapshot = {
            id: scored.resultId,
            caseId: claimed.case.id,
            caseVersion: claimed.case.version,
            evidenceSetHash: evidenceSetHash(events),
            calculationSpecHash: claimed.case.calculationSpecHash,
            algorithmVersion: rectificationV4AlgorithmVersion,
            candidates: [...scored.candidates],
            clusters: [...clusters],
            robustness,
            canConfirmExactMinute: false,
            canAcceptRange: gate.canAcceptRange,
            gateReasons: [...gate.reasons, ...scored.missingLayers.map((layer) => `missing_layer:${layer}`)],
            createdAt: now().toISOString(),
          };
        }
        await input.store.updateJobPhase({ workerId, jobId: claimed.job.id, phase: "planning_question", now: now().toISOString() });
        let nextQuestion: RectificationV4Question | null = null;
        if (!snapshot?.canAcceptRange) {
          const plannedQuestion = planNextQuestion({
            events,
            attemptedRefinementEventIds: claimed.attemptedRefinementEventIds,
            latestAnswer: claimed.turn.answer,
          });
          const authoredQuestion = input.questionAuthor
            ? await input.questionAuthor({
              modelId: claimed.turn.modelId,
              candidateRange: claimed.case.calculationSpec.candidateRange,
              snapshot,
              turns: claimed.turns,
              events,
              attemptedRefinementEventIds: claimed.attemptedRefinementEventIds,
            })
            : plannedQuestion;
          nextQuestion = plannedQuestion.targetEventId !== null
            && (authoredQuestion.targetEventId !== plannedQuestion.targetEventId
              || authoredQuestion.domain !== plannedQuestion.domain)
            ? plannedQuestion
            : authoredQuestion;
        }
        await input.store.completeJob({
          workerId,
          jobId: claimed.job.id,
          expectedCaseVersion: claimed.case.version,
          inputEvidenceSetHash: claimed.case.evidenceSetHash,
          outputEvidenceSetHash: evidenceSetHash(events),
          calculationSpecHash: claimed.case.calculationSpecHash,
          newEventRevisions: extracted,
          snapshot,
          nextQuestion,
          status: snapshot?.canAcceptRange ? "range_ready" : "awaiting_answer",
          phase: snapshot?.canAcceptRange ? "complete" : "collecting_evidence",
        }, now().toISOString());
        return true;
      } catch (error) {
        await input.store.failJob({
          workerId,
          jobId: claimed.job.id,
          expectedCaseVersion: claimed.case.version,
          errorCode: error instanceof Error ? error.message.slice(0, 120) : "unknown_worker_error",
          restoreQuestion: claimed.turn.questionId && claimed.turn.questionDomain ? {
            id: claimed.turn.questionId,
            domain: claimed.turn.questionDomain,
            targetEventId: claimed.turn.questionTargetEventId,
            prompt: claimed.turn.question,
            recallCost: "low",
            reason: "上一轮处理没有完成，请重新提交这段经历。",
          } : null,
          now: now().toISOString(),
        });
        return true;
      }
    },
  };
}
