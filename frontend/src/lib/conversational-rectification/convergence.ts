import type { RectificationTechnicalPacket } from "./technical-packet.ts";

export const MINIMUM_SCOREABLE_EVENTS = 3;
export const MAXIMUM_SCOREABLE_EVENTS = 8;
export const MAXIMUM_PLATEAU_ROUNDS = 2;

export type RangeCompletionReason =
  | "evidence_limit"
  | "no_discriminating_question"
  | "range_plateau";

const plateauNotePrefix = "range_plateau_count:";

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

export function rangeCompletionReason(input: Readonly<{
  packet: RectificationTechnicalPacket;
  scoreableEventCount: number;
  plateauCount: number;
}>): RangeCompletionReason | null {
  if (input.packet.candidate.status === "ready_for_confirmation") return null;
  if (input.scoreableEventCount < MINIMUM_SCOREABLE_EVENTS) return null;
  if (input.scoreableEventCount >= MAXIMUM_SCOREABLE_EVENTS) return "evidence_limit";
  if (input.packet.suggestedDomains.length === 0) return "no_discriminating_question";
  if (input.plateauCount >= MAXIMUM_PLATEAU_ROUNDS) return "range_plateau";
  return null;
}

export function rangeCompletionCopy(reason: RangeCompletionReason): string {
  switch (reason) {
    case "evidence_limit":
      return "已核对足够数量的真实经历，但现有证据仍不足以可靠确认某一分钟。";
    case "no_discriminating_question":
      return "当前候选之间已经没有可由真实经历继续区分的问题。";
    case "range_plateau":
      return "连续两轮补充经历后，候选范围没有继续稳定缩小。";
  }
}
