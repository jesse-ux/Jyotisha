import { randomUUID } from "node:crypto";
import path from "node:path";
import { Agent } from "@mastra/core/agent";
import { z } from "zod";
import { defaultLanguageModel, resolveLanguageModel } from "@/mastra/model";
import {
  evidenceDomainSchema,
  type CandidateSnapshot,
  type LifeEventRevision,
  type RectificationV4Question,
  type RectificationV4Turn,
} from "./contracts.ts";
import { planNextQuestion } from "./question-planner.ts";

const outputSchema = z.object({
  domain: evidenceDomainSchema,
  targetEventId: z.string().uuid().nullable(),
  prompt: z.string().trim().min(1).max(1_000),
  recallCost: z.enum(["low", "medium", "high"]),
  reason: z.string().trim().min(1).max(240),
}).strict();

const jyotishSkillPath = process.env.JYOTISH_SKILL_PATH?.trim()
  || path.resolve(process.cwd(), "..", "skills", "jyotish-vedic-astrology");
const agents = new Map<string, Agent>();
const internalCopyPattern = /(?:候选分数|内部(?:领域|路由|状态)|评分权重|\b(?:education|relocation|relationship|career|finance|health_pressure|family|other)\b)/iu;

function agentFor(modelId: string | null) {
  const model = modelId ? resolveLanguageModel(modelId) : defaultLanguageModel();
  const selected = model ?? defaultLanguageModel();
  if (!selected) return null;
  const cached = agents.get(selected.id);
  if (cached) return cached;
  const agent = new Agent({
    id: `rectification-v4-question-${selected.id}`,
    name: "Rectification V4 Conversational Question Author",
    model: selected.model,
    skills: [jyotishSkillPath],
    instructions: "Return only the requested JSON. Act as a birth-time rectification conversation partner, not a questionnaire. Respond to the user's latest concrete experience, then ask at most one natural open question that can materially improve evidence quality or distinguish the remaining candidate range. Choose the next evidence domain from context; never follow a fixed domain order. Never expose domain labels, event ids, scores, routing metadata, gate reasons, or implementation status in the visible prompt.",
  });
  agents.set(selected.id, agent);
  return agent;
}

function latestByEvent(events: readonly LifeEventRevision[]) {
  const latest = new Map<string, LifeEventRevision>();
  for (const event of events) {
    const current = latest.get(event.eventId);
    if (!current || current.revision < event.revision) latest.set(event.eventId, event);
  }
  return [...latest.values()];
}

export async function authorRectificationV4Question(input: Readonly<{
  modelId: string | null;
  candidateRange: Readonly<{ start: string; end: string }>;
  snapshot: CandidateSnapshot | null;
  turns: readonly RectificationV4Turn[];
  events: readonly LifeEventRevision[];
  attemptedRefinementEventIds: readonly string[];
}>): Promise<RectificationV4Question> {
  const plannedQuestion = planNextQuestion({
    events: input.events,
    attemptedRefinementEventIds: input.attemptedRefinementEventIds,
    latestAnswer: input.turns.at(-1)?.answer,
  });
  const fallback = () => plannedQuestion;
  const agent = agentFor(input.modelId);
  if (!agent) return fallback();

  const events = latestByEvent(input.events);
  const allowedTargets = new Map(events.map((event) => [event.eventId, event]));
  const requiredContinuation = plannedQuestion.targetEventId
    ? allowedTargets.get(plannedQuestion.targetEventId) ?? null
    : null;
  const recentTurns = input.turns.slice(-6).flatMap((turn) => [
    { role: "assistant", text: turn.question },
    ...(turn.answer ? [{ role: "user", text: turn.answer }] : []),
  ]);
  const prompt = JSON.stringify({
    task: "Write the next assistant message for an open-ended birth-time rectification conversation.",
    constraints: [
      "First acknowledge or connect to the latest user experience; do not say merely that an answer is complete or recorded.",
      "Ask zero or one question, never a checklist, form, domain menu, or fixed sequence.",
      "When requiredContinuation is present, continue that exact event and ask naturally for a more precise month or date; do not switch to another event or domain.",
      "When requiredContinuation is absent, choose the highest-information next question from context rather than following a domain order.",
      "The visible prompt must not mention internal domains, ids, scores, weights, gates, processing phases, or that a model selected a route.",
      "targetEventId must be null or one of allowedTargetEventIds.",
    ],
    candidateRange: input.candidateRange,
    currentCandidateRange: input.snapshot?.clusters[0]
      ? { start: input.snapshot.clusters[0].startTime, end: input.snapshot.clusters[0].endTime }
      : null,
    recentConversation: recentTurns,
    existingEvidence: events.map((event) => ({
      eventId: event.eventId,
      domain: event.domain,
      summary: event.summary,
      date: event.dateRange.label,
      precision: event.dateRange.precision,
      scoreability: event.scoreability,
    })),
    attemptedRefinementEventIds: input.attemptedRefinementEventIds,
    requiredContinuation: requiredContinuation
      ? {
          eventId: requiredContinuation.eventId,
          summary: requiredContinuation.summary,
          currentDate: requiredContinuation.dateRange.label,
          precision: requiredContinuation.dateRange.precision,
        }
      : null,
    allowedTargetEventIds: [...allowedTargets.keys()],
    allowedDomains: evidenceDomainSchema.options,
  });

  try {
    const result = await agent.generate(
      [{ role: "user", content: prompt }],
      {
        abortSignal: AbortSignal.timeout(35_000),
        structuredOutput: { schema: outputSchema, jsonPromptInjection: "inline" },
      },
    );
    const parsed = outputSchema.safeParse(result.object ?? (result.text ? JSON.parse(result.text) : null));
    if (!parsed.success || internalCopyPattern.test(parsed.data.prompt)) return fallback();
    const target = parsed.data.targetEventId ? allowedTargets.get(parsed.data.targetEventId) : null;
    return {
      id: randomUUID(),
      domain: target?.domain ?? parsed.data.domain,
      targetEventId: target?.eventId ?? null,
      prompt: parsed.data.prompt,
      recallCost: parsed.data.recallCost,
      reason: parsed.data.reason,
    };
  } catch (error) {
    console.warn("rectification_v4_question_author_failed", {
      modelId: input.modelId,
      errorName: error instanceof Error ? error.name : "UnknownError",
    });
    return fallback();
  }
}
