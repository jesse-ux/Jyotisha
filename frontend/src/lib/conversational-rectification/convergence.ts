import type { RectificationTechnicalPacket } from "./technical-packet.ts";

export const MINIMUM_SCOREABLE_EVENTS = 3;

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
