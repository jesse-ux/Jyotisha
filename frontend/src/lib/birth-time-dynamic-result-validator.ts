import type { DynamicChoiceScoringResult } from "./birth-time-dynamic-choice-internal.ts";
import type { TimeRange } from "./birth-time-dynamic-choice.ts";
import { BirthTimeScoringJobError } from "./birth-time-scoring-job.ts";

function minute(value: string): number {
  const [hour, part] = value.split(":").map(Number);
  return hour * 60 + part;
}

function rangeMinutes(range: TimeRange): readonly number[] {
  const start = minute(range.startTime);
  const end = minute(range.endTime);
  const values = [start];
  let current = start;
  while (current !== end) {
    current = (current + 1) % 1_440;
    values.push(current);
  }
  return values;
}

function segmentIsCoherent(
  result: DynamicChoiceScoringResult,
  currentRange: TimeRange,
): boolean {
  const segment = result.candidate.winningSegment;
  if (segment === null) return true;
  const candidates = rangeMinutes(currentRange);
  const start = candidates.indexOf(minute(segment.startTime));
  const end = candidates.indexOf(minute(segment.endTime));
  if (start < 0 || end < start) return false;
  const width = end - start + 1;
  const representative = candidates[start + Math.floor((width - 1) / 2)];
  return segment.widthMinutes === width
    && minute(segment.representativeTime) === representative;
}

export function assertDynamicScoringResult(
  result: DynamicChoiceScoringResult,
  currentRange: TimeRange,
): void {
  const candidate = result.candidate;
  const segment = candidate.winningSegment;
  const blocked = candidate.reasons.includes("missing_mandatory_layers");
  const high = !blocked
    && result.effectiveAnswerCount >= 4
    && result.dimensionCount >= 3
    && segment !== null
    && segment.widthMinutes <= 5
    && candidate.marginPercent >= 20;
  const medium = !blocked
    && result.effectiveAnswerCount >= 3
    && result.dimensionCount >= 2
    && segment !== null
    && segment.widthMinutes <= 15
    && candidate.marginPercent >= 10;
  const expected = high ? "high" : medium ? "medium" : "low";
  if (!segmentIsCoherent(result, currentRange)
    || candidate.confidence !== expected
    || candidate.canApply !== high
    || candidate.evidence.length !== 0) {
    throw new BirthTimeScoringJobError("invalid_result");
  }
}
