import { createHash } from "node:crypto";
import { z } from "zod";
import { conversationalRectificationTurnSchema } from "./conversational-rectification/contracts.ts";
import { storedCaseRowSchema } from "./conversational-rectification/persistence-contracts.ts";

const uuidSchema = z.string().uuid();
const fingerprintSchema = z.string().regex(/^[0-9a-f]{64}$/);
const acceptedRangeSchema = z.object({
  start: z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/),
  end: z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/),
}).strict();

const handoffProjectionSchema = z.object({
  caseId: uuidSchema,
  turnVersion: z.number().int().nonnegative(),
  question: z.string().trim().min(1).max(500),
  questionFingerprint: fingerprintSchema,
  requestId: uuidSchema,
  status: z.enum(["pending", "claimed", "in_progress", "consumed"]),
  turn: conversationalRectificationTurnSchema,
}).strict();

const executionProjectionSchema = z.object({
  status: z.enum(["ready", "in_progress", "consumed", "released"]),
  requestId: uuidSchema,
  billingReused: z.boolean().optional().default(false),
  credits: z.number().int().nonnegative().nullable().optional(),
}).strict();

const settlementProjectionSchema = z.object({
  status: z.enum(["pending", "consumed"]),
  requestId: uuidSchema,
  credits: z.number().int().nonnegative().nullable(),
}).strict();

const rectificationV4ExecutionProjectionSchema = executionProjectionSchema.extend({
  acceptedRange: acceptedRangeSchema,
}).strict();

export type RectificationHandoffProjection = z.infer<typeof handoffProjectionSchema>;
export type RectificationHandoffExecution = z.infer<typeof executionProjectionSchema>;
export type RectificationHandoffSettlement = z.infer<typeof settlementProjectionSchema>;
export type RectificationV4HandoffExecution = z.infer<typeof rectificationV4ExecutionProjectionSchema>;

export type RectificationHandoffRpcClient = Readonly<{
  rpc(
    name: string,
    args: Readonly<Record<string, unknown>>,
  ): PromiseLike<Readonly<{ data: unknown; error: unknown }>>;
}>;

export class RectificationHandoffServiceError extends Error {
  readonly name = "RectificationHandoffServiceError";

  constructor(readonly code: "not_found" | "stale" | "conflict" | "unavailable") {
    super(`Rectification handoff failed: ${code}`);
  }
}

function rpcMessage(error: unknown): string {
  if (!error || typeof error !== "object") return "";
  try {
    const message = (error as { message?: unknown }).message;
    return typeof message === "string" ? message : "";
  } catch {
    return "";
  }
}

function mappedError(error: unknown): RectificationHandoffServiceError {
  const message = rpcMessage(error);
  if (["conversational_case_not_found", "rectification_v4_case_not_found"].includes(message)) {
    return new RectificationHandoffServiceError("not_found");
  }
  if (["conversational_stale_turn", "stale_rectification_v4_case"].includes(message)) {
    return new RectificationHandoffServiceError("stale");
  }
  if (["conversational_action_conflict", "rectification_v4_handoff_conflict"].includes(message)) {
    return new RectificationHandoffServiceError("conflict");
  }
  return new RectificationHandoffServiceError("unavailable");
}

function single(value: unknown): unknown {
  if (!Array.isArray(value)) return value;
  if (value.length !== 1) throw new RectificationHandoffServiceError("unavailable");
  return value[0];
}

async function rpc(
  client: RectificationHandoffRpcClient,
  name: string,
  args: Readonly<Record<string, unknown>>,
): Promise<unknown> {
  try {
    const result = await client.rpc(name, args);
    if (result.error) throw mappedError(result.error);
    return single(result.data);
  } catch (error) {
    if (error instanceof RectificationHandoffServiceError) throw error;
    throw new RectificationHandoffServiceError("unavailable");
  }
}

export function rectificationQuestionFingerprint(question: string): string {
  return createHash("sha256").update(question, "utf8").digest("hex");
}

export function createRectificationHandoffService(client: RectificationHandoffRpcClient) {
  return Object.freeze({
    async attach(input: Readonly<{
      userId: string;
      caseId: string;
      turnVersion: number;
      actionId: string;
      question: string;
    }>) {
      const question = input.question.trim();
      const parsed = storedCaseRowSchema.safeParse(await rpc(
        client,
        "attach_conversational_rectification_question",
        {
          p_user_id: input.userId,
          p_case_id: input.caseId,
          p_expected_version: input.turnVersion,
          p_action_id: input.actionId,
          p_question: question,
          p_question_fingerprint: rectificationQuestionFingerprint(question),
        },
      ));
      if (!parsed.success) throw new RectificationHandoffServiceError("unavailable");
      return parsed.data.latest_turn;
    },

    async load(input: Readonly<{ userId: string; caseId?: string }>) {
      const value = await rpc(client, "load_conversational_rectification_handoff", {
        p_user_id: input.userId,
        p_case_id: input.caseId ?? null,
      });
      if (value === null) return null;
      const parsed = handoffProjectionSchema.safeParse(value);
      if (!parsed.success) throw new RectificationHandoffServiceError("unavailable");
      return parsed.data;
    },

    async claim(input: Readonly<{
      userId: string;
      caseId: string;
      turnVersion: number;
      actionId: string;
      question: string;
    }>) {
      const question = input.question.trim();
      const parsed = handoffProjectionSchema.safeParse(await rpc(
        client,
        "claim_conversational_rectification_handoff",
        {
          p_user_id: input.userId,
          p_case_id: input.caseId,
          p_expected_version: input.turnVersion,
          p_action_id: input.actionId,
          p_question_fingerprint: rectificationQuestionFingerprint(question),
        },
      ));
      if (!parsed.success) throw new RectificationHandoffServiceError("unavailable");
      return parsed.data;
    },

    async beginExecution(input: Readonly<{
      userId: string;
      caseId: string;
      turnVersion: number;
      claimActionId: string;
      requestId: string;
      question: string;
    }>): Promise<RectificationHandoffExecution> {
      const question = input.question.trim();
      const parsed = executionProjectionSchema.safeParse(await rpc(
        client,
        "begin_conversational_rectification_handoff_execution",
        {
          p_user_id: input.userId,
          p_case_id: input.caseId,
          p_expected_version: input.turnVersion,
          p_claim_action_id: input.claimActionId,
          p_request_id: input.requestId,
          p_question_fingerprint: rectificationQuestionFingerprint(question),
        },
      ));
      if (!parsed.success) throw new RectificationHandoffServiceError("unavailable");
      return parsed.data;
    },

    async settle(input: Readonly<{
      userId: string;
      caseId: string;
      claimActionId: string;
      requestId: string;
      emitted: boolean;
    }>): Promise<RectificationHandoffSettlement> {
      const parsed = settlementProjectionSchema.safeParse(await rpc(
        client,
        "settle_conversational_rectification_handoff",
        {
          p_user_id: input.userId,
          p_case_id: input.caseId,
          p_claim_action_id: input.claimActionId,
          p_request_id: input.requestId,
          p_emitted: input.emitted,
        },
      ));
      if (!parsed.success) throw new RectificationHandoffServiceError("unavailable");
      return parsed.data;
    },
  });
}

export type RectificationHandoffService = ReturnType<typeof createRectificationHandoffService>;

const rectificationV4HandoffProjectionSchema = z.object({
  protocol: z.literal("rectification-evidence-v4"),
  caseId: uuidSchema,
  caseVersion: z.number().int().nonnegative(),
  question: z.string().trim().min(1).max(500),
  questionFingerprint: fingerprintSchema,
  requestId: uuidSchema,
  status: z.enum(["pending", "claimed", "in_progress", "consumed"]),
  acceptedRange: acceptedRangeSchema.nullable(),
}).strict();

export type RectificationV4HandoffProjection = z.infer<typeof rectificationV4HandoffProjectionSchema>;

export function createRectificationV4HandoffService(client: RectificationHandoffRpcClient) {
  return Object.freeze({
    async attach(input: Readonly<{
      userId: string;
      caseId: string;
      caseVersion: number;
      actionId: string;
      question: string;
    }>): Promise<RectificationV4HandoffProjection> {
      const question = input.question.trim();
      const parsed = rectificationV4HandoffProjectionSchema.safeParse(await rpc(
        client,
        "attach_birth_time_rectification_v4_question",
        {
          p_user_id: input.userId,
          p_case_id: input.caseId,
          p_expected_version: input.caseVersion,
          p_action_id: input.actionId,
          p_question: question,
          p_question_fingerprint: rectificationQuestionFingerprint(question),
        },
      ));
      if (!parsed.success) throw new RectificationHandoffServiceError("unavailable");
      return parsed.data;
    },

    async load(input: Readonly<{ userId: string; caseId?: string }>) {
      const value = await rpc(client, "load_birth_time_rectification_v4_handoff", {
        p_user_id: input.userId,
        p_case_id: input.caseId ?? null,
      });
      if (value === null) return null;
      const parsed = rectificationV4HandoffProjectionSchema.safeParse(value);
      if (!parsed.success) throw new RectificationHandoffServiceError("unavailable");
      return parsed.data;
    },

    async claim(input: Readonly<{
      userId: string;
      caseId: string;
      caseVersion: number;
      actionId: string;
      question: string;
    }>): Promise<RectificationV4HandoffProjection> {
      const question = input.question.trim();
      const parsed = rectificationV4HandoffProjectionSchema.safeParse(await rpc(
        client,
        "claim_birth_time_rectification_v4_handoff",
        {
          p_user_id: input.userId,
          p_case_id: input.caseId,
          p_expected_version: input.caseVersion,
          p_action_id: input.actionId,
          p_question_fingerprint: rectificationQuestionFingerprint(question),
        },
      ));
      if (!parsed.success) throw new RectificationHandoffServiceError("unavailable");
      return parsed.data;
    },

    async beginExecution(input: Readonly<{
      userId: string;
      caseId: string;
      caseVersion: number;
      claimActionId: string;
      requestId: string;
      question: string;
    }>): Promise<RectificationV4HandoffExecution> {
      const question = input.question.trim();
      const parsed = rectificationV4ExecutionProjectionSchema.safeParse(await rpc(
        client,
        "begin_birth_time_rectification_v4_handoff_execution",
        {
          p_user_id: input.userId,
          p_case_id: input.caseId,
          p_expected_version: input.caseVersion,
          p_claim_action_id: input.claimActionId,
          p_request_id: input.requestId,
          p_question_fingerprint: rectificationQuestionFingerprint(question),
        },
      ));
      if (!parsed.success) throw new RectificationHandoffServiceError("unavailable");
      return parsed.data;
    },

    async settle(input: Readonly<{
      userId: string;
      caseId: string;
      claimActionId: string;
      requestId: string;
      emitted: boolean;
    }>): Promise<RectificationHandoffSettlement> {
      const parsed = settlementProjectionSchema.safeParse(await rpc(
        client,
        "settle_birth_time_rectification_v4_handoff",
        {
          p_user_id: input.userId,
          p_case_id: input.caseId,
          p_claim_action_id: input.claimActionId,
          p_request_id: input.requestId,
          p_emitted: input.emitted,
        },
      ));
      if (!parsed.success) throw new RectificationHandoffServiceError("unavailable");
      return parsed.data;
    },
  });
}

export type RectificationV4HandoffService = ReturnType<typeof createRectificationV4HandoffService>;
