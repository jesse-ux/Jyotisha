import { z } from "zod";
import {
  conversationalRectificationCommandSchema,
  conversationalRectificationResponseSchema,
  type ConversationalRectificationCommand,
  type ConversationalRectificationResponse,
} from "./contracts.ts";

export const CONVERSATIONAL_RECTIFICATION_UNAVAILABLE = "生时校正暂时无法继续，请稍后重试。";

const publicErrorSchema = z.object({
  code: z.string(),
  message: z.string(),
}).passthrough();

const streamEventSchema = z.discriminatedUnion("type", [
  z.object({ type: z.literal("delta"), text: z.string() }).strict(),
  z.object({
    type: z.literal("turn"),
    turn: conversationalRectificationResponseSchema,
  }).strict(),
]);

export type ConversationalRectificationStreamOptions = Readonly<{
  onNarrativeDelta?: (text: string) => void;
}>;

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

async function readJsonPayload(response: Response): Promise<unknown> {
  return response.json().catch(() => null);
}

async function readStreamedTurn(
  response: Response,
  options: ConversationalRectificationStreamOptions,
): Promise<ConversationalRectificationResponse> {
  if (!response.body) throw new SyntaxError("missing rectification response stream");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffered = "";
  let turn: ConversationalRectificationResponse | null = null;
  const consumeLine = (line: string) => {
    if (!line.trim()) return;
    const event = streamEventSchema.parse(JSON.parse(line));
    if (event.type === "delta") options.onNarrativeDelta?.(event.text);
    else turn = event.turn;
  };
  while (true) {
    const { done, value } = await reader.read();
    buffered += decoder.decode(value, { stream: !done });
    let newline = buffered.indexOf("\n");
    while (newline >= 0) {
      consumeLine(buffered.slice(0, newline));
      buffered = buffered.slice(newline + 1);
      newline = buffered.indexOf("\n");
    }
    if (done) break;
  }
  consumeLine(buffered);
  if (!turn) throw new SyntaxError("missing rectification turn event");
  return turn;
}

async function postCommandWithOneReplay(
  body: string,
  options: ConversationalRectificationStreamOptions,
) {
  for (let attempt = 0; attempt < 2; attempt += 1) {
    let emittedNarrative = false;
    try {
      const response = await fetch("/api/birth-time-conversation", {
        method: "POST",
        credentials: "same-origin",
        headers: {
          Accept: "application/x-ndjson, application/json",
          "Content-Type": "application/json",
        },
        body,
      });
      if (!response.ok) {
        const payload = await readJsonPayload(response);
        const nonJsonFailure = payload === null;
        if (attempt === 0 && (response.status === 502 || nonJsonFailure)) continue;
        return { response, payload, turn: null };
      }
      if (response.headers.get("content-type")?.includes("application/x-ndjson")) {
        const turn = await readStreamedTurn(response, {
          onNarrativeDelta(text) {
            emittedNarrative = true;
            options.onNarrativeDelta?.(text);
          },
        });
        return { response, payload: null, turn };
      }
      return { response, payload: await readJsonPayload(response), turn: null };
    } catch (error) {
      if (attempt === 0 && !emittedNarrative && isRetryableTransportError(error)) continue;
      throw error;
    }
  }
  throw new TypeError("unreachable conversational rectification replay state");
}

export async function sendConversationalRectificationCommand(
  command: ConversationalRectificationCommand,
  options: ConversationalRectificationStreamOptions = {},
): Promise<ConversationalRectificationResponse> {
  const request = conversationalRectificationCommandSchema.parse(command);
  const body = JSON.stringify(request);
  try {
    const { response, payload, turn } = await postCommandWithOneReplay(body, options);
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
    return turn ?? conversationalRectificationResponseSchema.parse(payload);
  } catch (error) {
    if (error instanceof ConversationalRectificationRequestError) throw error;
    throw new ConversationalRectificationRequestError(
      502,
      null,
      CONVERSATIONAL_RECTIFICATION_UNAVAILABLE,
    );
  }
}
