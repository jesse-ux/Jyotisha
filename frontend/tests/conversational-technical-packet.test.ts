import assert from "node:assert/strict";
import test from "node:test";
import {
  buildRectificationTechnicalPacket,
  projectRectificationTechnicalPacket,
} from "../src/lib/conversational-rectification/technical-packet.ts";
import type { CandidateResult } from "../src/lib/birth-time-evidence.ts";
import type { CandidateDifferenceBuild } from "../src/lib/birth-time-dynamic-choice-internal.ts";
import type { RectificationQuestionnaire } from "../src/lib/birth-time-journey-service.ts";

const scan = {
  questions: [],
  samples: [
    { ascendantSign: "Cancer", d4Sign: "Aries", d9Sign: "Aries", d10Sign: "Taurus", d24Sign: "Gemini", d30Sign: "Pisces" },
    { ascendantSign: "Cancer", d4Sign: "Aries", d9Sign: "Leo", d10Sign: "Libra", d24Sign: "Gemini", d30Sign: "Pisces" },
    { ascendantSign: "Cancer", d4Sign: "Aries", d9Sign: "Virgo", d10Sign: "Scorpio", d24Sign: "Gemini", d30Sign: "Pisces" },
    { ascendantSign: "Cancer", d4Sign: "Aries", d9Sign: "Sagittarius", d10Sign: "Capricorn", d24Sign: "Gemini", d30Sign: "Pisces" },
  ],
  raw: {
    schema_version: 3,
    candidate_scan: {
      samples: [
        { time: "2000-01-01 05:10", ascendant: { sign: "Cancer" } },
        { time: "2000-01-01 05:16", ascendant: { sign: "Cancer" } },
        { time: "2000-01-01 05:24", ascendant: { sign: "Cancer" } },
        { time: "2000-01-01 05:30", ascendant: { sign: "Cancer" } },
      ],
    },
  },
} satisfies RectificationQuestionnaire;

const candidateDifferences = {
  packet: {
    caseId: "synthetic-case",
    scoringVersion: "birth-time-choice-scoring-v2",
    currentRange: { startTime: "05:10", endTime: "05:30" },
    opportunities: [{
      opportunityId: "difference-d9-relationship",
      dimensionCode: "relationship",
      neutralContext: "D9 changes across the candidate range",
      estimatedInformationGain: 0.8,
      candidatePartitionFingerprint: "private-fingerprint",
      fallbackPrompt: "relationship event",
      partitions: [
        { partitionId: "private-partition-early", descriptor: "early", fallbackLabel: "early" },
        { partitionId: "private-partition-late", descriptor: "late", fallbackLabel: "late" },
      ],
    }, {
      opportunityId: "difference-d10-career",
      dimensionCode: "career",
      neutralContext: "D10 changes across the candidate range",
      estimatedInformationGain: 0.7,
      candidatePartitionFingerprint: "private-career-fingerprint",
      fallbackPrompt: "career event",
      partitions: [
        { partitionId: "private-career-early", descriptor: "early", fallbackLabel: "early" },
        { partitionId: "private-career-late", descriptor: "late", fallbackLabel: "late" },
      ],
    }],
    askedQuestionFingerprints: [],
    candidatePartitionFingerprints: ["private-fingerprint", "private-career-fingerprint"],
    recentRangeHistory: [],
  },
  candidateModel: {
    version: "synthetic-candidate-model-v1",
    candidateWeights: { "05:10": 0.4, "05:30": 0.6 },
  },
  scoringPartitions: {
    "difference-d9-relationship": [
      { partitionId: "private-partition-early", descriptor: "early", fallbackLabel: "early", candidateScores: { "05:10": 1, "05:30": 0 } },
      { partitionId: "private-partition-late", descriptor: "late", fallbackLabel: "late", candidateScores: { "05:10": 0, "05:30": 1 } },
    ],
  },
} satisfies CandidateDifferenceBuild;

const eventScore = {
  resultId: "00000000-0000-4000-8000-000000000601",
  confidence: "medium",
  canApply: false,
  winningSegment: {
    startTime: "05:16",
    endTime: "05:24",
    representativeTime: "05:20",
    widthMinutes: 9,
  },
  eventCount: 1,
  domainCount: 1,
  topScore: 8,
  secondScore: 7,
  marginPercent: 12.5,
  reasons: ["historical evidence narrows the middle segment"],
  evidence: [{
    eventId: "00000000-0000-4000-8000-000000000602",
    domain: "career",
    candidateTime: "05:20",
    ruleIds: ["vim-md-career"],
    points: 3,
  }],
  algorithmVersion: "birth-time-event-scoring-v1",
} satisfies CandidateResult;

export function syntheticTechnicalPacket() {
  return buildRectificationTechnicalPacket({
    scan,
    candidateDifferences,
    eventScore,
    consultation: {
      source: "server_consultation_workflow",
      calculationVersion: "rectification-technical-v1",
      availableLayers: ["D1", "D9", "D10"],
      layerReferences: {
        D1: ["consult-d1-ascendant"],
        D9: ["consult-d9-candidate-difference"],
        D10: ["consult-d10-candidate-difference"],
      },
      timeLinkedScanSamples: [
        { sampleIndex: 0, time: "05:10" },
        { sampleIndex: 1, time: "05:16" },
        { sampleIndex: 2, time: "05:24" },
        { sampleIndex: 3, time: "05:30" },
      ],
      boundaryDistanceMinutes: 4,
      futureWindows: [{
        label: "2028 career context window",
        startDate: "2028-03-01",
        endDate: "2028-05-31",
      }],
    },
  });
}

test("builds a deterministic private packet from server-computed engine receipts", () => {
  const first = syntheticTechnicalPacket();
  const second = syntheticTechnicalPacket();

  assert.deepEqual(first, second);
  assert.equal(first.candidate.status, "pending_validation");
  assert.equal(first.candidate.representativeTime, "05:20");
  assert.deepEqual(first.candidate.range, { startTime: "05:16", endTime: "05:24" });
  assert.equal(first.d1Stability, "stable");
  assert.deepEqual(first.stableLayers.map((item) => item.layer), ["D1"]);
  assert.deepEqual(first.supportedSensitiveLayers, ["D9", "D10"]);
  assert.deepEqual(first.sensitiveLayers.map((item) => item.values), [["Leo", "Virgo"], ["Libra", "Scorpio"]]);
  assert.deepEqual(first.sensitivityScope, {
    source: "time_linked_candidate_scan_samples",
    rangeStart: "05:16",
    rangeEnd: "05:24",
    sampleTimes: ["05:16", "05:24"],
  });
  assert.equal(first.candidateDifferenceRefs.includes("difference-d9-relationship"), false);
  assert.ok(first.candidateDifferenceRefs.includes("consult-d9-candidate-difference"));
  assert.equal(first.boundaryDistanceMinutes, 4);
  assert.deepEqual(first.candidateWeights, { "05:10": 0.4, "05:30": 0.6 });
  assert.ok(first.partitionIds.includes("private-partition-early"));
  assert.deepEqual(first.scoredHistoricalEvidence[0], {
    evidenceId: "00000000-0000-4000-8000-000000000602",
    domain: "career",
    candidateTime: "05:20",
    score: 3,
    ruleRefs: ["vim-md-career"],
  });
  assert.ok(first.suggestedDomains.length >= 2);
  assert.deepEqual(first.suggestedDomains.map((item) => item.domain), ["relationship", "career"]);
  assert.match(first.suggestedDomains[0]?.reason ?? "", /D9/);
  assert.match(first.suggestedDomains[0]?.reason ?? "", /关系/);
  assert.doesNotMatch(first.suggestedDomains[0]?.reason ?? "", /relationship/);
  assert.match(first.suggestedDomains[1]?.reason ?? "", /事业/);
  assert.doesNotMatch(first.suggestedDomains[1]?.reason ?? "", /career/);
  assert.deepEqual(first.futureWindows, [{
    label: "2028 career context window",
    startDate: "2028-03-01",
    endDate: "2028-05-31",
    scoreable: false,
  }]);
});

test("does not claim scan-wide 05:10-05:30 differences inside a 05:16-05:24 candidate", () => {
  const scanWideOnly = {
    ...scan,
    samples: [scan.samples[0], scan.samples[3]],
    raw: {
      schema_version: 3,
      candidate_scan: {
        samples: [
          { time: "2000-01-01 05:10", ascendant: { sign: "Cancer" } },
          { time: "2000-01-01 05:30", ascendant: { sign: "Cancer" } },
        ],
      },
    },
  } satisfies RectificationQuestionnaire;

  assert.throws(() => buildRectificationTechnicalPacket({
    scan: scanWideOnly,
    candidateDifferences,
    eventScore,
    consultation: {
      source: "server_consultation_workflow",
      calculationVersion: "rectification-technical-v1",
      availableLayers: ["D1", "D9", "D10"],
      layerReferences: {
        D1: ["consult-d1-ascendant"],
        D9: ["consult-d9-candidate-difference"],
        D10: ["consult-d10-candidate-difference"],
      },
      timeLinkedScanSamples: [
        { sampleIndex: 0, time: "05:10" },
        { sampleIndex: 1, time: "05:30" },
      ],
      boundaryDistanceMinutes: 4,
      futureWindows: [],
    },
  }), /two time-linked scan samples inside the selected candidate range/);
});

test("uses typed server time links when normalized scan raw metadata omits sample times", () => {
  const normalizedScan = {
    ...scan,
    raw: {
      questions: [],
      candidate_scan: { samples: scan.samples.map(() => ({})) },
    },
  } satisfies RectificationQuestionnaire;
  const packet = buildRectificationTechnicalPacket({
    scan: normalizedScan,
    candidateDifferences,
    eventScore,
    consultation: {
      source: "server_consultation_workflow",
      calculationVersion: "rectification-technical-v1",
      availableLayers: ["D1", "D9", "D10"],
      layerReferences: {
        D1: ["consult-d1-ascendant"],
        D9: ["consult-d9-candidate-difference"],
        D10: ["consult-d10-candidate-difference"],
      },
      timeLinkedScanSamples: [
        { sampleIndex: 0, time: "05:10" },
        { sampleIndex: 1, time: "05:16" },
        { sampleIndex: 2, time: "05:24" },
        { sampleIndex: 3, time: "05:30" },
      ],
      boundaryDistanceMinutes: 4,
      futureWindows: [],
    },
  });

  assert.deepEqual(packet.sensitivityScope.sampleTimes, ["05:16", "05:24"]);
  assert.deepEqual(packet.sensitiveLayers.map((item) => item.values), [
    ["Leo", "Virgo"],
    ["Libra", "Scorpio"],
  ]);
});

test("public projection strips weights, partition identifiers, and private fingerprints", () => {
  const projected = projectRectificationTechnicalPacket(syntheticTechnicalPacket());
  const serialized = JSON.stringify(projected);

  assert.equal(serialized.includes("candidateWeights"), false);
  assert.equal(serialized.includes("partitionIds"), false);
  assert.equal(serialized.includes("private-partition"), false);
  assert.equal(serialized.includes("private-fingerprint"), false);
  assert.deepEqual(projected.technicalReceipt.stableLayers, ["D1"]);
  assert.deepEqual(projected.technicalReceipt.sensitiveLayers, ["D9", "D10"]);
  assert.deepEqual(projected.technicalReceipt.sensitivityScope, {
    source: "time_linked_candidate_scan_samples",
    rangeStart: "05:16",
    rangeEnd: "05:24",
    sampleTimes: ["05:16", "05:24"],
  });
  assert.deepEqual(projected.evidenceRequest.domains, ["relationship", "career"]);
  assert.equal(projected.futureWindows[0]?.scoreable, false);
});

test("public projection respects the existing bounded technical receipt", () => {
  const packet = syntheticTechnicalPacket();
  const projected = projectRectificationTechnicalPacket({
    ...packet,
    candidateDifferenceRefs: Array.from({ length: 50 }, (_, index) => `difference-${index}`),
  });

  assert.equal(projected.technicalReceipt.candidateDifferenceRefs.length, 40);
  assert.deepEqual(projected.technicalReceipt.candidateDifferenceRefs.slice(0, 2), [
    "difference-0",
    "difference-1",
  ]);
});
