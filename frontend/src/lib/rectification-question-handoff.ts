import { z } from "zod";
import {
  conversationalRectificationTurnSchema,
  type ConversationalRectificationTurn,
} from "./conversational-rectification/contracts.ts";

export type RectificationQuestionHandoff<Theme extends string> = Readonly<{
  question: string;
  sessionId: string;
  theme: Theme;
}>;

type HandoffFallback<Theme extends string> = Readonly<{
  sessionId: string;
  theme: Theme;
}>;

type ContinueOriginalQuestion<Theme extends string> = (
  handoff: RectificationQuestionHandoff<Theme>,
) => Promise<boolean>;

function normalizedQuestion(value: string | null | undefined): string | null {
  if (typeof value !== "string") return null;
  const question = value.trim();
  return question.length > 0 && question.length <= 500 ? question : null;
}

function sameHandoff<Theme extends string>(
  left: RectificationQuestionHandoff<Theme> | null,
  right: RectificationQuestionHandoff<Theme>,
) {
  return left?.question === right.question
    && left.sessionId === right.sessionId
    && left.theme === right.theme;
}

/**
 * Keeps the presentation-only session/theme context beside the question that
 * the v3 case persists. The durable question always wins after refresh; local
 * context is retained only while it still belongs to that same question.
 */
export function createRectificationQuestionHandoffCoordinator<Theme extends string>() {
  let current: RectificationQuestionHandoff<Theme> | null = null;
  let activeContinuation: Promise<boolean> | null = null;
  let activeContinuationToken: symbol | null = null;
  let consumedQuestion: string | null = null;

  const fromDurableQuestion = (
    questionValue: string | null | undefined,
    fallback: HandoffFallback<Theme>,
  ): RectificationQuestionHandoff<Theme> | null => {
    const question = normalizedQuestion(questionValue);
    if (!question) return current;
    if (current?.question === question) return current;
    if (consumedQuestion === question) return null;
    if (!fallback.sessionId) return null;
    current = Object.freeze({ question, ...fallback });
    return current;
  };

  return Object.freeze({
    capture(input: RectificationQuestionHandoff<Theme>) {
      const question = normalizedQuestion(input.question);
      if (!question || !input.sessionId) {
        throw new TypeError("A visible question and session are required for rectification handoff");
      }
      consumedQuestion = null;
      current = Object.freeze({ ...input, question });
      return current;
    },
    synchronizeDurableQuestion: fromDurableQuestion,
    peek() {
      return current;
    },
    clear() {
      current = null;
    },
    continueOriginalQuestion(
      questionValue: string,
      fallback: HandoffFallback<Theme>,
      send: ContinueOriginalQuestion<Theme>,
    ) {
      if (activeContinuation) return activeContinuation;
      const handoff = fromDurableQuestion(questionValue, fallback);
      if (!handoff) return Promise.resolve(false);

      const token = Symbol("rectification-question-continuation");
      const operation = Promise.resolve()
        .then(() => send(handoff))
        .then((completed) => {
          if (completed && sameHandoff(current, handoff)) {
            current = null;
            consumedQuestion = handoff.question;
          }
          return completed;
        })
        .finally(() => {
          if (activeContinuationToken === token) {
            activeContinuation = null;
            activeContinuationToken = null;
          }
        });
      activeContinuation = operation;
      activeContinuationToken = token;
      return operation;
    },
  });
}

export type RectificationQuestionHandoffCoordinator<Theme extends string> = ReturnType<
  typeof createRectificationQuestionHandoffCoordinator<Theme>
>;

const durableHandoffSchema = z.object({
  caseId: z.string().uuid(),
  turnVersion: z.number().int().nonnegative(),
  question: z.string().trim().min(1).max(500),
  questionFingerprint: z.string().regex(/^[0-9a-f]{64}$/),
  requestId: z.string().uuid(),
  status: z.enum(["pending", "claimed", "in_progress", "consumed"]),
  turn: conversationalRectificationTurnSchema,
}).strict();

export type DurableRectificationQuestionHandoff = z.infer<typeof durableHandoffSchema>;
export type ClaimedRectificationQuestionHandoff = DurableRectificationQuestionHandoff & Readonly<{
  claimActionId: string;
}>;

export class DurableRectificationHandoffError extends Error {
  readonly name = "DurableRectificationHandoffError";

  constructor(
    readonly status: number,
    readonly code: string | null,
    message: string,
  ) {
    super(message);
  }
}

type HandoffFetch = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;

async function handoffPayload(response: Response): Promise<unknown> {
  if (response.status === 204) return null;
  const contentType = response.headers.get("content-type") ?? "";
  return contentType.includes("application/json")
    ? response.json().catch(() => null)
    : null;
}

function errorFields(value: unknown): { code: string | null; message: string } {
  if (!value || typeof value !== "object") {
    return { code: null, message: "暂时无法保存或继续原问题，请稍后重试。" };
  }
  const record = value as { code?: unknown; message?: unknown };
  return {
    code: typeof record.code === "string" ? record.code : null,
    message: typeof record.message === "string"
      ? record.message
      : "暂时无法保存或继续原问题，请稍后重试。",
  };
}

/**
 * Browser transport for the account-level handoff. A claim keeps one action id
 * until the server returns a terminal response, so a lost HTTP response replays
 * the same durable identity rather than creating another consultation attempt.
 */
export function createDurableRectificationQuestionHandoffClient(input: Readonly<{
  fetch?: HandoffFetch;
  createActionId?: () => string;
}> = {}) {
  const fetcher = input.fetch ?? globalThis.fetch.bind(globalThis);
  const createActionId = input.createActionId ?? (() => globalThis.crypto.randomUUID());
  const claimActions = new Map<string, string>();

  async function post(command: Readonly<Record<string, unknown>>): Promise<unknown> {
    const body = JSON.stringify(command);
    let lastError: unknown = null;
    for (let attempt = 0; attempt < 2; attempt += 1) {
      try {
        const response = await fetcher("/api/birth-time-conversation/handoff", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body,
        });
        const payload = await handoffPayload(response);
        if (!response.ok) {
          const fields = errorFields(payload);
          throw new DurableRectificationHandoffError(
            response.status,
            fields.code,
            fields.message,
          );
        }
        return payload;
      } catch (error) {
        lastError = error;
        if (error instanceof DurableRectificationHandoffError || attempt > 0) throw error;
      }
    }
    throw lastError;
  }

  return Object.freeze({
    async load(): Promise<DurableRectificationQuestionHandoff | null> {
      const response = await fetcher("/api/birth-time-conversation/handoff", {
        method: "GET",
        headers: { accept: "application/json" },
      });
      const payload = await handoffPayload(response);
      if (response.status === 204) return null;
      if (!response.ok) {
        const fields = errorFields(payload);
        throw new DurableRectificationHandoffError(response.status, fields.code, fields.message);
      }
      return durableHandoffSchema.parse(payload);
    },

    async attach(request: Readonly<{
      caseId: string;
      turnVersion: number;
      question: string;
      actionId?: string;
    }>): Promise<ConversationalRectificationTurn> {
      const payload = await post({
        type: "attach",
        caseId: request.caseId,
        turnVersion: request.turnVersion,
        actionId: request.actionId ?? createActionId(),
        question: request.question.trim(),
      });
      return conversationalRectificationTurnSchema.parse(payload);
    },

    async claim(request: Readonly<{
      caseId: string;
      turnVersion: number;
      question: string;
    }>): Promise<ClaimedRectificationQuestionHandoff> {
      const identity = JSON.stringify([
        request.caseId,
        request.turnVersion,
        request.question.trim(),
      ]);
      const actionId = claimActions.get(identity) ?? createActionId();
      claimActions.set(identity, actionId);
      const payload = durableHandoffSchema.parse(await post({
        type: "claim",
        caseId: request.caseId,
        turnVersion: request.turnVersion,
        actionId,
        question: request.question.trim(),
      }));
      if (payload.status !== "claimed") claimActions.delete(identity);
      return Object.freeze({ ...payload, claimActionId: actionId });
    },
  });
}

export type DurableRectificationQuestionHandoffClient = ReturnType<
  typeof createDurableRectificationQuestionHandoffClient
>;
