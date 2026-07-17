import { z } from "zod";

const creditResultSchema = z.object({
  success: z.boolean(),
  credits: z.number().int().nullable(),
  error_code: z.string().nullable().optional(),
});

type CreditRpcName = "begin_consultation_credit" | "complete_consultation_credit" | "cancel_consultation_credit";
type AccountingClient = {
  rpc(
    rpcName: CreditRpcName,
    args: { p_user_id: string; p_request_id: string },
  ): PromiseLike<{ data: unknown; error: { message: string } | null }>;
};

export type CreditResult = z.infer<typeof creditResultSchema>;

export class CreditRpcError extends Error {
  readonly code: string;

  constructor(code: string) {
    super(`Credit operation failed: ${code}`);
    this.name = "CreditRpcError";
    this.code = code;
  }
}

export async function runCreditRpc(
  accounting: AccountingClient,
  rpcName: CreditRpcName,
  userId: string,
  requestId: string,
): Promise<CreditResult> {
  let lastError = "unknown_credit_error";

  for (let attempt = 1; attempt <= 3; attempt += 1) {
    try {
      const { data, error } = await accounting.rpc(rpcName, {
        p_user_id: userId,
        p_request_id: requestId,
      });
      const candidate = Array.isArray(data) ? data[0] : data;
      const parsed = creditResultSchema.safeParse(candidate);
      if (!error && parsed.success) return parsed.data;
      lastError = error?.message || "invalid_credit_response";
    } catch (error) {
      lastError = error instanceof Error ? error.message : "credit_request_failed";
    }

    if (attempt < 3) {
      await new Promise((resolve) => setTimeout(resolve, attempt * 150));
    }
  }

  throw new CreditRpcError(lastError);
}
