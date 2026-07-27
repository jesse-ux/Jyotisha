import type { CandidateCluster, Robustness } from "./contracts.ts";

export type DecisionGateResult = Readonly<{
  canConfirmExactMinute: false;
  canAcceptRange: boolean;
  reasons: readonly string[];
}>;

export function evaluateDecisionGate(input: {
  readonly clusters: readonly CandidateCluster[];
  readonly robustness: Robustness;
  readonly scoreableEventCount: number;
  readonly scoreableDomainCount: number;
}): DecisionGateResult {
  const reasons: string[] = [];
  const primary = input.clusters[0];
  if (!primary) reasons.push("no_primary_candidate_cluster");
  if (input.scoreableEventCount < 5) reasons.push("insufficient_scoreable_events");
  if (input.scoreableDomainCount < 3) reasons.push("insufficient_scoreable_domains");
  if ((primary?.widthMinutes ?? 0) < 2) reasons.push("single_minute_cluster_not_acceptable");
  if ((primary?.widthMinutes ?? Number.POSITIVE_INFINITY) > 15) reasons.push("primary_cluster_too_wide");
  if (input.robustness.neighborSupportMinutes < 2) reasons.push("neighbor_support_not_passed");
  if (input.robustness.leaveOneOutRetentionRate < 0.8) reasons.push("leave_one_out_not_stable");
  if (input.robustness.dateSensitivityRetentionRate < 0.8) reasons.push("date_range_sensitivity_not_stable");
  if (!input.robustness.calculationSpecHashMatched) reasons.push("calculation_spec_changed");
  return { canConfirmExactMinute: false, canAcceptRange: reasons.length === 0, reasons };
}
