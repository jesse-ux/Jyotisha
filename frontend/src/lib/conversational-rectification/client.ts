import { z } from "zod";
import { postJson } from "../birth-time-client-transport.ts";
import {
  conversationalRectificationCommandSchema,
  conversationalRectificationTurnSchema,
  type ConversationalRectificationCommand,
  type ConversationalRectificationTurn,
} from "./contracts.ts";

export const CONVERSATIONAL_RECTIFICATION_UNAVAILABLE = "生时校正暂时无法继续，请稍后重试。";

export type ConversationalRectificationHistoryMessage = Readonly<{
  role: "assistant" | "user";
  text: string;
}>;

const conversationHistoryMessageSchema = z.object({
  role: z.enum(["assistant", "user"]),
  text: z.string().trim().min(1).max(12_000),
}).strict();

const conversationHistorySchema = z.array(conversationHistoryMessageSchema).max(500);
const conversationHistoryByTurn = new WeakMap<object, readonly ConversationalRectificationHistoryMessage[]>();

export function conversationalRectificationHistoryForTurn(
  turn: ConversationalRectificationTurn,
): readonly ConversationalRectificationHistoryMessage[] {
  return conversationHistoryByTurn.get(turn) ?? [];
}

const publicErrorSchema = z.object({
  code: z.string(),
  message: z.string(),
}).passthrough();

export class ConversationalRectificationRequestError extends Error {
  readonly name = "ConversationalRectificationRequestError";
  readonly status: number;
  readonly code: string | null;

  constructor(status: number, code: string | null, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

function canonicalValue(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(canonicalValue);
  if (value !== null && typeof value === "object") {
    const record = value as Readonly<Record<string, unknown>>;
    return Object.fromEntries(
      Object.keys(record)
        .filter((key) => record[key] !== undefined)
        .sort()
        .map((key) => [key, canonicalValue(record[key])]),
    );
  }
  return value;
}

export function canonicalConversationalRectificationPayload(value: unknown): string {
  return JSON.stringify(canonicalValue(value));
}

export type ConversationalRectificationActionIdentity = Readonly<{
  caseId: string;
  turnVersion: number;
  operation: ConversationalRectificationCommand["type"];
  payload: unknown;
}>;

function actionIdentity(input: ConversationalRectificationActionIdentity): string {
  return canonicalConversationalRectificationPayload({
    caseId: input.caseId,
    operation: input.operation,
    payload: input.payload,
    turnVersion: input.turnVersion,
  });
}

export function createConversationalRectificationActionRegistry(
  createId: () => string = () => globalThis.crypto.randomUUID(),
) {
  const actionIds = new Map<string, string>();
  return {
    async run<T>(
      input: ConversationalRectificationActionIdentity,
      operation: (actionId: string) => Promise<T>,
    ): Promise<T> {
      const identity = actionIdentity(input);
      const actionId = actionIds.get(identity) ?? createId();
      actionIds.set(identity, actionId);
      const result = await operation(actionId);
      if (actionIds.get(identity) === actionId) actionIds.delete(identity);
      return result;
    },
  };
}

export type ConversationalRectificationActionRegistry = ReturnType<
  typeof createConversationalRectificationActionRegistry
>;

function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}

function isRetryableTransportError(error: unknown): boolean {
  return !isAbortError(error) && (
    error instanceof TypeError
    || error instanceof SyntaxError
    || (error instanceof DOMException && error.name === "SyntaxError")
  );
}

async function postCommandWithOneReplay(body: string) {
  for (let attempt = 0; attempt < 2; attempt += 1) {
    try {
      const result = await postJson({
        url: "/api/birth-time-conversation",
        body,
        retryLostResponse: false,
      });
      // postJson deliberately projects an unparseable non-ok body to null. Treating all null
      // error payloads as replayable also covers proxies that mislabel HTML as application/json.
      const nonJsonFailure = !result.response.ok && result.payload === null;
      if (attempt === 0 && (result.response.status === 502 || nonJsonFailure)) continue;
      return result;
    } catch (error) {
      if (attempt === 0 && isRetryableTransportError(error)) continue;
      throw error;
    }
  }
  throw new TypeError("unreachable conversational rectification replay state");
}

export async function sendConversationalRectificationCommand(
  command: ConversationalRectificationCommand,
): Promise<ConversationalRectificationTurn> {
  const request = conversationalRectificationCommandSchema.parse(command);
  const body = JSON.stringify(request);
  try {
    const { response, payload } = await postCommandWithOneReplay(body);
    if (!response.ok) {
      const parsed = publicErrorSchema.safeParse(payload);
      const safeServerMessage = response.status < 500 && parsed.success
        ? parsed.data.message
        : CONVERSATIONAL_RECTIFICATION_UNAVAILABLE;
      throw new ConversationalRectificationRequestError(
        response.status,
        parsed.success ? parsed.data.code : null,
        safeServerMessage,
      );
    }
    const payloadRecord = payload !== null && typeof payload === "object" && !Array.isArray(payload)
      ? payload as Readonly<Record<string, unknown>>
      : null;
    const history = conversationHistorySchema.safeParse(payloadRecord?.conversationMessages);
    const turnPayload = payloadRecord && "conversationMessages" in payloadRecord
      ? Object.fromEntries(
          Object.entries(payloadRecord).filter(([key]) => key !== "conversationMessages"),
        )
      : payload;
    const turn = conversationalRectificationTurnSchema.parse(turnPayload);
    if (history.success && history.data.length > 0) {
      conversationHistoryByTurn.set(turn, history.data);
    }
    return turn;
  } catch (error) {
    if (error instanceof ConversationalRectificationRequestError) throw error;
    throw new ConversationalRectificationRequestError(
      502,
      null,
      CONVERSATIONAL_RECTIFICATION_UNAVAILABLE,
    );
  }
}
