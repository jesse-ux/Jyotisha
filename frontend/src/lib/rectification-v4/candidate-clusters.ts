import type { CandidateCluster, CandidateMinute } from "./contracts.ts";

function minuteValue(value: string): number {
  const [hour, minute] = value.split(":").map(Number);
  return hour! * 60 + minute!;
}

function nextMinute(previous: string, current: string): boolean {
  return (minuteValue(current) - minuteValue(previous) + 1_440) % 1_440 === 1;
}

export function buildCandidateClusters(
  candidates: readonly CandidateMinute[],
  relativeFloor = 0.97,
): readonly CandidateCluster[] {
  if (candidates.length === 0) return [];
  const sorted = [...candidates].sort((left, right) => minuteValue(left.time) - minuteValue(right.time));
  const peak = Math.max(...sorted.map((candidate) => candidate.score));
  const floor = peak >= 0 ? peak * relativeFloor : peak / relativeFloor;
  const viable = sorted.filter((candidate) => candidate.score >= floor);
  const groups: CandidateMinute[][] = [];
  for (const candidate of viable) {
    const group = groups.at(-1);
    if (group && nextMinute(group.at(-1)!.time, candidate.time)) group.push(candidate);
    else groups.push([candidate]);
  }
  return groups.map((group) => {
    const peakScore = Math.max(...group.map((candidate) => candidate.score));
    const peakCandidate = group.find((candidate) => candidate.score === peakScore)!;
    return {
      rank: 0,
      startTime: group[0]!.time,
      endTime: group.at(-1)!.time,
      representativeTime: peakCandidate.time,
      widthMinutes: group.length,
      peakScore,
      scoreMass: group.reduce((total, candidate) => total + Math.max(candidate.score, 0), 0),
    };
  }).sort((left, right) => right.peakScore - left.peakScore || right.scoreMass - left.scoreMass)
    .map((cluster, index) => ({ ...cluster, rank: index + 1 }));
}
