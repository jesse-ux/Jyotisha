import type { CandidateSnapshot } from "../rectification-v4/contracts.ts";
import type { DiagnosticsSummary, QuestionOpportunity, RectificationDecision } from "./contracts.ts";

export function deterministicDecision(input: Readonly<{
  snapshot: CandidateSnapshot | null;
  diagnostics: DiagnosticsSummary | null;
  opportunities: readonly QuestionOpportunity[];
}>): RectificationDecision {
  if (input.snapshot?.canAcceptRange) return { action: "offer_candidate_range", snapshotId: input.snapshot.id };
  const top = input.opportunities.find((item) => item.active);
  if (top) return { action: "ask_question", opportunityId: top.opportunityId, narrativeFocus: ["latest_event", ...(top.kind === "refine_event_date" ? ["date_precision" as const] : [])] };
  return { action: "stop_low_confidence", reasonCodes: input.diagnostics ? ["no_high_value_question", "diagnostics_not_stable"] : ["insufficient_scoreable_evidence"] };
}
