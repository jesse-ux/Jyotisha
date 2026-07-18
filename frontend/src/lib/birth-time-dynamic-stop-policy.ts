import type { CandidateResult } from "./birth-time-evidence.ts";

export type DynamicStopInput = {
  readonly result: CandidateResult;
  readonly effectiveAnswer: boolean;
  readonly previousResult: CandidateResult | null;
  readonly priorPlateauCount: number;
  readonly usefulOpportunityCount: number;
  readonly repeatedOnly: boolean;
  readonly effectiveAnswerCount: number;
};

export type DynamicStopDecision =
  | {
    readonly kind: "finish";
    readonly reason: "high_confidence" | "safety_cap" | "plateau" | "no_information_gain" | "repeated_partition";
    readonly plateauCount: number;
  }
  | { readonly kind: "continue"; readonly plateauCount: number };

export function materiallyChanged(
  previousResult: CandidateResult | null,
  result: CandidateResult,
): boolean {
  if (previousResult === null) return true;
  const previousRange = previousResult.winningSegment;
  const nextRange = result.winningSegment;
  const rangeChanged = previousRange === null || nextRange === null
    ? previousRange !== nextRange
    : previousRange.startTime !== nextRange.startTime
      || previousRange.endTime !== nextRange.endTime
      || previousRange.representativeTime !== nextRange.representativeTime;
  return rangeChanged || Math.abs(previousResult.marginPercent - result.marginPercent) >= 2;
}

export function decideDynamicStop(input: DynamicStopInput): DynamicStopDecision {
  const plateauCount = input.effectiveAnswer
    ? materiallyChanged(input.previousResult, input.result) ? 0 : input.priorPlateauCount + 1
    : input.priorPlateauCount;
  if (input.result.confidence === "high") return { kind: "finish", reason: "high_confidence", plateauCount };
  if (input.effectiveAnswerCount >= 10) return { kind: "finish", reason: "safety_cap", plateauCount };
  if (plateauCount >= 2) return { kind: "finish", reason: "plateau", plateauCount };
  if (input.usefulOpportunityCount === 0) return { kind: "finish", reason: "no_information_gain", plateauCount };
  if (input.repeatedOnly) return { kind: "finish", reason: "repeated_partition", plateauCount };
  return { kind: "continue", plateauCount };
}
