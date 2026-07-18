import { createHash } from "node:crypto";
import type { CandidateDifferencePacket } from "./birth-time-dynamic-choice-internal.ts";

const clockTimePattern = /(?:^|[^\d])(?:[01]?\d|2[0-3])\s*[:：]\s*[0-5]\d(?:$|[^\d])/;

export function dynamicServerCopyIsSafe(value: string, question: boolean): boolean {
  const normalized = value.normalize("NFKC").trim();
  if (normalized.length > (question ? 240 : 80)) return false;
  if (!/[\u3400-\u9fff]/u.test(normalized) || /[A-Za-z]/.test(normalized)) return false;
  if (clockTimePattern.test(normalized)) return false;
  return !question || (normalized.match(/[？?]/g) ?? []).length === 1;
}

export function normalizeDynamicLabel(value: string): string {
  return value.normalize("NFKC").trim().replace(/\s+/g, "");
}

export function modelSafeDynamicQuestionPrompt(
  packet: CandidateDifferencePacket,
): string {
  return JSON.stringify({
    task: "select_dynamic_choice_opportunity",
    opportunities: packet.opportunities.map((opportunity) => ({
      opportunityId: opportunity.opportunityId,
      dimensionCode: opportunity.dimensionCode,
      neutralContext: opportunity.neutralContext,
    })),
  });
}

export function dynamicQuestionSemanticFingerprint(output: {
  readonly prompt: string;
  readonly options: readonly { readonly label: string }[];
}): string {
  const semantics = {
    prompt: normalizeDynamicLabel(output.prompt),
    options: output.options.map((option) => normalizeDynamicLabel(option.label)),
  };
  return createHash("sha256")
    .update(`birth-time-dynamic-question-v1\n${JSON.stringify(semantics)}`, "utf8")
    .digest("hex");
}
