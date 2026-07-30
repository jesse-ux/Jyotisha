import assert from "node:assert/strict";
import test from "node:test";

import { candidateSnapshotSchema, type EvidenceDomain, type Robustness } from "../src/lib/rectification-v4/contracts.ts";
import { evaluateDecisionGate } from "../src/lib/rectification-v4/decision-gate.ts";
import { classifyMissingTechniqueLayers } from "../src/lib/rectification-v4/technique-layer-policy.ts";

const cluster = {
  rank: 1,
  startTime: "05:13",
  endTime: "05:17",
  representativeTime: "05:15",
  widthMinutes: 5,
  peakScore: 10,
  scoreMass: 40,
} as const;
const robustness: Robustness = {
  neighborSupportMinutes: 4,
  leaveOneOutRetentionRate: 1,
  leaveOneDomainOutRetentionRate: 1,
  dateSensitivityRetentionRate: 1,
  calculationSpecHashMatched: true,
};
const domains = ["education", "relocation", "career"] as const satisfies readonly EvidenceDomain[];

function gate(overrides: Partial<Parameters<typeof evaluateDecisionGate>[0]> = {}) {
  return evaluateDecisionGate({
    clusters: [cluster],
    robustness,
    scoreableEventCount: 6,
    scoreableDomains: domains,
    missingTechniqueLayers: [],
    ...overrides,
  });
}

test("single-domain dependence blocks the public candidate range", () => {
  const result = gate({ robustness: { ...robustness, leaveOneDomainOutRetentionRate: 0.79 } });
  assert.equal(result.canAcceptRange, false);
  assert.ok(result.reasons.includes("leave_one_domain_out_not_stable"));
  assert.equal(result.canConfirmExactMinute, false);
});

test("KP cusps alone do not block the public candidate range", () => {
  const classified = classifyMissingTechniqueLayers(["KP_cusps"], domains);
  assert.deepEqual(classified.optional, ["KP_cusps"]);
  assert.equal(gate({ missingTechniqueLayers: ["KP_cusps"] }).canAcceptRange, true);
});

test("D60 remains reference-only and does not block the public candidate range", () => {
  const classified = classifyMissingTechniqueLayers(["D60"], domains);
  assert.deepEqual(classified.referenceOnly, ["D60"]);
  assert.equal(gate({ missingTechniqueLayers: ["D60"] }).canAcceptRange, true);
});

test("missing D10 blocks when career evidence is active", () => {
  const result = gate({ missingTechniqueLayers: ["D10"] });
  assert.equal(result.canAcceptRange, false);
  assert.ok(result.reasons.includes("missing_required_layer:D10"));
});

test("missing D10 does not block without career evidence", () => {
  const scoreableDomains = ["education", "relocation", "relationship"] as const;
  assert.equal(gate({ scoreableDomains, missingTechniqueLayers: ["D10"] }).canAcceptRange, true);
});

test("unclassified missing layers fail closed", () => {
  const result = gate({ missingTechniqueLayers: ["future_unknown_layer"] });
  assert.equal(result.canAcceptRange, false);
  assert.ok(result.reasons.includes("missing_unclassified_layer:future_unknown_layer"));
});

function snapshotInput(overrides: Record<string, unknown> = {}) {
  return {
    id: "00000000-0000-4000-8000-000000000001",
    caseId: "00000000-0000-4000-8000-000000000002",
    caseVersion: 1,
    evidenceSetHash: "e".repeat(64),
    calculationSpecHash: "c".repeat(64),
    algorithmVersion: "rectification-v5-matrix-scoring-1",
    candidates: [{ time: "05:15", score: 10, supportingEventIds: [], conflictingEventIds: [] }],
    clusters: [cluster],
    canConfirmExactMinute: false,
    canAcceptRange: true,
    gateReasons: [],
    createdAt: "2026-07-29T00:00:00.000Z",
    ...overrides,
  };
}

test("legacy snapshots without domain retention still parse without retroactive rejection", () => {
  const parsed = candidateSnapshotSchema.parse(snapshotInput({
    robustness: {
      neighborSupportMinutes: 4,
      leaveOneOutRetentionRate: 1,
      dateSensitivityRetentionRate: 1,
      calculationSpecHashMatched: true,
    },
  }));
  assert.equal(parsed.robustness.leaveOneDomainOutRetentionRate, 0.8);
  assert.equal(parsed.canAcceptRange, true);
  assert.ok(!parsed.gateReasons.includes("leave_one_domain_out_not_stable"));
});

test("snapshots with explicit low domain retention are normalized to rejected", () => {
  const parsed = candidateSnapshotSchema.parse(snapshotInput({
    robustness: { ...robustness, leaveOneDomainOutRetentionRate: 0.79 },
  }));
  assert.equal(parsed.robustness.leaveOneDomainOutRetentionRate, 0.79);
  assert.equal(parsed.canAcceptRange, false);
  assert.ok(parsed.gateReasons.includes("leave_one_domain_out_not_stable"));
});
