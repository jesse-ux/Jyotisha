import { randomUUID } from "node:crypto";
import type {
  CalculationSpec,
  LifeEventRevision,
  RectificationV4ApiResponse,
  RectificationV4Case,
} from "./contracts.ts";
import { rectificationAgentV5Protocol, rectificationV4AlgorithmVersion, rectificationV4Protocol } from "./contracts.ts";
import { selectRectificationDeploymentMode } from "../rectification-agent/feature-policy.ts";
import { calculationSpecHash, evidenceSetHash } from "./fingerprints.ts";
import { openingQuestion } from "./opening-question.ts";
import type { RectificationV4Store } from "./store.ts";

export function createRectificationV4CaseService(store: RectificationV4Store, options: { readonly now?: () => Date } = {}) {
  const now = options.now ?? (() => new Date());

  async function response(userId: string, caseValue: RectificationV4Case, jobId?: string): Promise<RectificationV4ApiResponse> {
    const [events, turns] = await Promise.all([
      store.loadEvents(userId, caseValue.id),
      store.loadTurns(userId, caseValue.id),
    ]);
    return {
      case: caseValue,
      job: jobId ? await store.loadJob(userId, jobId) : null,
      events: [...events],
      turns: [...turns],
    };
  }

  return {
    async createCase(input: { readonly userId: string; readonly actionId: string; readonly calculationSpec: CalculationSpec }) {
      const timestamp = now().toISOString();
      const deploymentMode = selectRectificationDeploymentMode(input.userId);
      const caseValue: RectificationV4Case = {
        id: randomUUID(),
        userId: input.userId,
        protocol: deploymentMode === "v4_legacy" ? rectificationV4Protocol : rectificationAgentV5Protocol,
        version: 0,
        status: "awaiting_answer",
        phase: "collecting_evidence",
        calculationSpec: input.calculationSpec,
        calculationSpecHash: calculationSpecHash(input.calculationSpec),
        evidenceSetHash: evidenceSetHash([]),
        currentQuestion: openingQuestion(input.calculationSpec.candidateRange),
        latestSnapshot: null,
        orchestrationModelId: process.env.RECTIFICATION_ORCHESTRATION_MODEL_ID?.trim() || null,
        narrationModelId: process.env.RECTIFICATION_NARRATION_MODEL_ID?.trim() || null,
        skillVersion: "birth-time-rectification-v5",
        promptVersion: "rectification-agent-v5-1",
        algorithmVersion: rectificationV4AlgorithmVersion,
        deploymentMode,
        agentMode: "deterministic_fallback",
        featureSnapshotId: null,
        latestDiagnosticsId: null,
        acceptedRange: null,
        createdAt: timestamp,
        updatedAt: timestamp,
      };
      return response(input.userId, await store.createCase({ case: caseValue, actionId: input.actionId }));
    },

    async loadCase(userId: string, caseId: string) {
      const found = await store.loadCase(userId, caseId);
      return found ? response(userId, found) : null;
    },

    async loadActive(userId: string) {
      const found = await store.findActiveCase(userId);
      return found ? response(userId, found) : null;
    },

    async loadJob(userId: string, jobId: string) {
      return store.loadJob(userId, jobId);
    },

    async answer(input: { readonly userId: string; readonly caseId: string; readonly actionId: string; readonly expectedCaseVersion: number; readonly answer: string; readonly modelId?: string | null }) {
      const current = await store.loadCase(input.userId, input.caseId);
      if (!current?.currentQuestion) return null;
      const saved = await store.submitAnswer({
        ...input,
        modelId: input.modelId ?? null,
        question: current.currentQuestion,
        jobId: randomUUID(),
        turnId: randomUUID(),
        now: now().toISOString(),
      });
      return response(input.userId, saved.case, saved.job.id);
    },

    async reviseEvent(input: {
      readonly userId: string;
      readonly caseId: string;
      readonly actionId: string;
      readonly expectedCaseVersion: number;
      readonly revision: LifeEventRevision;
    }) {
      const saved = await store.reviseEvent({ ...input, jobId: randomUUID(), now: now().toISOString() });
      return response(input.userId, saved.case, saved.job.id);
    },

    async transition(input: {
      readonly userId: string;
      readonly caseId: string;
      readonly actionId: string;
      readonly expectedCaseVersion: number;
      readonly kind: "pause" | "resume" | "abandon";
    }) {
      const status = input.kind === "pause" ? "paused" : input.kind === "abandon" ? "abandoned" : "awaiting_answer";
      const phase = input.kind === "abandon" ? "complete" : "collecting_evidence";
      return response(input.userId, await store.transitionCase({ ...input, status, phase, now: now().toISOString() }));
    },

    async acceptRange(input: {
      readonly userId: string;
      readonly caseId: string;
      readonly actionId: string;
      readonly expectedCaseVersion: number;
      readonly startTime: string;
      readonly endTime: string;
    }) {
      const current = await store.loadCase(input.userId, input.caseId);
      const primary = current?.latestSnapshot?.clusters[0];
      if (!current || !current.latestSnapshot?.canAcceptRange || !primary
        || primary.startTime !== input.startTime || primary.endTime !== input.endTime) return null;
      return response(input.userId, await store.transitionCase({
        ...input,
        status: "range_ready",
        phase: "complete",
        acceptedRange: { start: input.startTime, end: input.endTime },
        now: now().toISOString(),
      }));
    },
  };
}
