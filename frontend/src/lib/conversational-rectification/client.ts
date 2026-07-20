import { z } from "zod";
import { postJson } from "../birth-time-client-transport.ts";
import {
  conversationalRectificationCommandSchema,
  conversationalRectificationTurnSchema,
  type ConversationalRectificationCommand,
  type ConversationalRectificationTurn,
} from "./contracts.ts";

export const CONVERSATIONAL_RECTIFICATION_UNAVAILABLE = "生时校正暂时无法继续，请稍后重试。";

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

export async function sendConversationalRectificationCommand(
  command: ConversationalRectificationCommand,
): Promise<ConversationalRectificationTurn> {
  const request = conversationalRectificationCommandSchema.parse(command);
  try {
    const { response, payload } = await postJson({
      url: "/api/birth-time-conversation",
      body: JSON.stringify(request),
      retryLostResponse: true,
    });
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
    return conversationalRectificationTurnSchema.parse(payload);
  } catch (error) {
    if (error instanceof ConversationalRectificationRequestError) throw error;
    throw new ConversationalRectificationRequestError(
      502,
      null,
      CONVERSATIONAL_RECTIFICATION_UNAVAILABLE,
    );
  }
}
