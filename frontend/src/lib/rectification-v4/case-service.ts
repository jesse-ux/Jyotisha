import { randomUUID } from "node:crypto";
import type {
  CalculationSpec,
  LifeEventRevision,
  RectificationV4ApiResponse,
  RectificationV4Case,
} from "./contracts.ts";
import { rectificationAgentV5Protocol, rectificationV4AlgorithmVersion, rectificationV4Protocol } from "./contracts.ts";
import { selectRectificationDeploymentMode } from "../rectification-agent/feature-policy.ts";
import { CURRENT_RECTIFICATION_PROMPT_VERSION, CURRENT_RECTIFICATION_SKILL_VERSION } from "../rectification-agent/contracts.ts";
import { regenerateDirectorQuestion } from "../rectification-agent/director-agent.ts";
import { regenerateQuestionRealization } from "../rectification-agent/renderer-agent.ts";
import { calculationSpecHash, evidenceSetHash } from "./fingerprints.ts";
import { openingQuestion } from "./opening-question.ts";
import type { RectificationV4Store } from "./store.ts";

const regenerationInFlight = new Map<string, Promise<RectificationV4Case | null>>();

export function createRectificationV4CaseService(
  store: RectificationV4Store,
  options: {
    readonly now?: () => Date;
    readonly regenerateQuestion?: typeof regenerateQuestionRealization;
    readonly regenerateDirectorQuestion?: typeof regenerateDirectorQuestion;
  } = {},
) {
  const now = options.now ?? (() => new Date());
  const realizeQuestion = options.regenerateQuestion ?? regenerateQuestionRealization;
  const redirectQuestion = options.regenerateDirectorQuestion ?? regenerateDirectorQuestion;

  async function response(userId: string, caseValue: RectificationV4Case, jobId?: string): Promise<RectificationV4ApiResponse> {
    const [events, turns, analysis, job] = await Promise.all([
      store.loadEvents(userId, caseValue.id),
      store.loadTurns(userId, caseValue.id),
      caseValue.deploymentMode === "v5_agent"
        ? store.loadAnalysisMessages(userId, caseValue.id)
        : Promise.resolve([]),
      jobId
        ? store.loadJob(userId, jobId)
        : caseValue.status === "processing" ? store.loadActiveJob(userId, caseValue.id) : null,
    ]);
    return {
      case: caseValue,
      job,
      events: [...events],
      turns: [...turns],
      analysis: [...analysis],
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
        skillVersion: CURRENT_RECTIFICATION_SKILL_VERSION,
        promptVersion: CURRENT_RECTIFICATION_PROMPT_VERSION,
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

    async regenerateQuestion(input: {
      readonly userId: string;
      readonly caseId: string;
      readonly actionId: string;
      readonly expectedCaseVersion: number;
    }) {
      const replay = await store.loadActionCase(input.userId, input.actionId);
      if (replay) return response(input.userId, replay);

      const key = `${input.userId}:${input.actionId}`;
      let pending = regenerationInFlight.get(key);
      if (!pending) {
        pending = (async () => {
          const secondReplay = await store.loadActionCase(input.userId, input.actionId);
          if (secondReplay) return secondReplay;
          const current = await store.loadCase(input.userId, input.caseId);
          if (!current?.currentQuestion || current.deploymentMode !== "v5_agent") return null;
          const validated = await store.loadLatestValidatedDecision(input.userId, input.caseId);
          if (!validated || validated.decision.action !== "ask_question") return null;
          const [events, turns] = await Promise.all([
            store.loadEvents(input.userId, input.caseId),
            store.loadTurns(input.userId, input.caseId),
          ]);
          let prompt: string;
          if (validated.selectedOpportunity) {
            prompt = await realizeQuestion({
              caseValue: current,
              currentPrompt: current.currentQuestion.prompt,
              latestAnswer: turns.at(-1)?.answer ?? "",
              acceptedEvents: events,
              opportunity: validated.selectedOpportunity,
            });
          } else {
            if (!("focus" in validated.decision)) return null;
            prompt = await redirectQuestion({
              caseValue: current,
              currentQuestion: current.currentQuestion.prompt,
              latestAnswer: turns.at(-1)?.answer ?? "",
              acceptedEvents: events,
              focus: validated.decision.focus,
            });
          }
          return store.replaceCurrentQuestion({
            ...input,
            question: { ...current.currentQuestion, id: randomUUID(), prompt },
            now: now().toISOString(),
          });
        })();
        regenerationInFlight.set(key, pending);
      }
      try {
        const saved = await pending;
        return saved ? response(input.userId, saved) : null;
      } finally {
        if (regenerationInFlight.get(key) === pending) regenerationInFlight.delete(key);
      }
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
