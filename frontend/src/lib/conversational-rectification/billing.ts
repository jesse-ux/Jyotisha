import { z } from "zod";
import { ConversationalRectificationError } from "./errors.ts";
import {
  conversationalRectificationCaseIdForStartAction,
  mapConversationalRectificationStoreError,
  type ConversationalRectificationRpcClient,
} from "./store.ts";
import { billingReceiptResponseSchema } from "./persistence-contracts.ts";

export type ConversationalRectificationBillingIdentity = Readonly<{
  userId: string;
  caseId: string;
  expectedVersion: number;
  actionId: string;
}>;

export type ConversationalRectificationFeeInput =
  ConversationalRectificationBillingIdentity & Readonly<{ price: number }>;

export type ConversationalRectificationBillingResult = Readonly<{
  success: true;
  credits: number;
  billingState: "reserved" | "charged" | "released" | "migration_waived";
}>;

const billingIdentitySchema = z.object({
  userId: z.string().uuid(),
  caseId: z.string().uuid(),
  expectedVersion: z.number().int().nonnegative(),
  actionId: z.string().uuid(),
}).strict();

function billingArgs(
  input: ConversationalRectificationBillingIdentity,
): Readonly<Record<string, unknown>> {
  const parsed = billingIdentitySchema.safeParse({
    userId: input.userId,
    caseId: input.caseId,
    expectedVersion: input.expectedVersion,
    actionId: input.actionId,
  });
  if (!parsed.success
    || parsed.data.caseId !== conversationalRectificationCaseIdForStartAction(parsed.data.actionId)) {
    throw new ConversationalRectificationError("action_conflict");
  }
  return {
    p_user_id: parsed.data.userId,
    p_case_id: parsed.data.caseId,
    p_expected_version: parsed.data.expectedVersion,
    p_action_id: parsed.data.actionId,
  };
}

function unwrapBillingRow(data: unknown): unknown {
  if (!Array.isArray(data)) return data;
  if (data.length !== 1) throw new ConversationalRectificationError("billing_failed");
  return data[0];
}

function billingRejection(errorCode: string | null): ConversationalRectificationError {
  if (errorCode === "insufficient_credits") {
    return new ConversationalRectificationError("insufficient_credits");
  }
  if (errorCode === "action_conflict") {
    return new ConversationalRectificationError("action_conflict");
  }
  return new ConversationalRectificationError("billing_failed");
}

export class ConversationalRectificationBilling {
  constructor(private readonly supabase: ConversationalRectificationRpcClient) {}

  private async call(
    functionName: string,
    args: Readonly<Record<string, unknown>>,
  ): Promise<ConversationalRectificationBillingResult> {
    try {
      const { data, error } = await this.supabase.rpc(functionName, args);
      if (error) {
        const mapped = mapConversationalRectificationStoreError(error);
        throw mapped.code === "store_unavailable"
          ? new ConversationalRectificationError("billing_failed")
          : mapped;
      }
      const parsed = billingReceiptResponseSchema.safeParse(unwrapBillingRow(data));
      if (!parsed.success) throw new ConversationalRectificationError("billing_failed");
      if (!parsed.data.success || !parsed.data.billing_state || parsed.data.credits === null) {
        throw billingRejection(parsed.data.error_code);
      }
      return Object.freeze({
        success: true,
        credits: parsed.data.credits,
        billingState: parsed.data.billing_state,
      });
    } catch (error) {
      if (error instanceof ConversationalRectificationError) throw error;
      throw new ConversationalRectificationError("billing_failed");
    }
  }

  async reserve(
    input: ConversationalRectificationFeeInput,
  ): Promise<ConversationalRectificationBillingResult> {
    if (!Number.isSafeInteger(input.price) || input.price < 1 || input.price > 1_000_000) {
      throw new ConversationalRectificationError("billing_failed");
    }
    return this.call("reserve_conversational_rectification_fee", {
      ...billingArgs(input),
      p_price: input.price,
    });
  }

  async complete(
    input: ConversationalRectificationBillingIdentity,
  ): Promise<ConversationalRectificationBillingResult> {
    return this.call("complete_conversational_rectification_fee", billingArgs(input));
  }

  async release(
    input: ConversationalRectificationFeeInput,
  ): Promise<ConversationalRectificationBillingResult> {
    if (!Number.isSafeInteger(input.price) || input.price < 1 || input.price > 1_000_000) {
      throw new ConversationalRectificationError("billing_failed");
    }
    return this.call("release_conversational_rectification_fee", {
      ...billingArgs(input),
      p_price: input.price,
    });
  }
}

export function createSupabaseConversationalRectificationBilling(
  supabase: ConversationalRectificationRpcClient,
): ConversationalRectificationBilling {
  return new ConversationalRectificationBilling(supabase);
}
