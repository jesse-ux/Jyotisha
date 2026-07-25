import { RECTIFICATION_POLICY } from "../rectification-policy.ts";
import type {
  RectificationEvidenceDomain,
  RectificationTechnicalPacket,
} from "./technical-packet.ts";

const plateauNotePrefix = "range_plateau_count:";
const systemBlockers = new Set([
  "required_layers_incomplete",
  "three_engine_parity_not_passed",
  "vedastro_validation_required",
  "vedastro_validation_not_passed",
  "vedastro_official_response_missing",
  "vedastro_minute_snapshot_failed",
  "vedastro_minute_sensitive_layers_not_discriminated",
  "minute_holdout_not_ready",
]);

type CandidateProgress = Readonly<{
  rangeStart?: string | null;
  rangeEnd?: string | null;
  workingState?: Readonly<{
    notes: readonly string[];
  }>;
}>;

function priorPlateauCount(candidate: CandidateProgress): number {
  const note = candidate.workingState?.notes.find((item) => item.startsWith(plateauNotePrefix));
  const value = Number(note?.slice(plateauNotePrefix.length));
  return Number.isSafeInteger(value) && value >= 0 ? value : 0;
}

function sameRange(candidate: CandidateProgress, packet: RectificationTechnicalPacket): boolean {
  return candidate.rangeStart === packet.candidate.range.startTime
    && candidate.rangeEnd === packet.candidate.range.endTime;
}

export function nextPlateauCount(
  candidate: CandidateProgress,
  packet: RectificationTechnicalPacket,
): number {
  return sameRange(candidate, packet) ? priorPlateauCount(candidate) + 1 : 0;
}

export function convergenceNotes(candidate: CandidateProgress, plateauCount: number): string[] {
  return [
    ...(candidate.workingState?.notes ?? []).filter((item) => !item.startsWith(plateauNotePrefix)),
    `${plateauNotePrefix}${plateauCount}`,
  ];
}

export function shouldCompleteBoundedResult(input: Readonly<{
  packet: RectificationTechnicalPacket;
  scoreableEventCount: number;
  scoreableDomainCount: number;
  answeredDomains: ReadonlySet<RectificationEvidenceDomain>;
  plateauCount: number;
}>): boolean {
  if (input.packet.candidate.status === "ready_for_confirmation"
    || input.scoreableEventCount < RECTIFICATION_POLICY.minConfirmationEvents
    || input.scoreableDomainCount < RECTIFICATION_POLICY.minConfirmationDomains
    || input.packet.suggestedDomains.some((item) => !input.answeredDomains.has(item.domain))) {
    return false;
  }
  if (input.plateauCount >= RECTIFICATION_POLICY.maxPlateauRounds) return true;
  const blockers = input.packet.expertWorkflow?.hardBlockers ?? [];
  return blockers.length > 0 && blockers.every((blocker) => systemBlockers.has(blocker));
}
