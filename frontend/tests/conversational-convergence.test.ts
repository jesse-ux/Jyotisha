import assert from "node:assert/strict";
import test from "node:test";
import {
  convergenceNotes,
  nextPlateauCount,
  shouldCompleteBoundedResult,
} from "../src/lib/conversational-rectification/convergence.ts";
import type { RectificationTechnicalPacket } from "../src/lib/conversational-rectification/technical-packet.ts";

const pendingPacket = {
  candidate: { status: "pending_validation" },
  suggestedDomains: [
    { domain: "relationship", layer: "D9", reason: "relationship evidence" },
    { domain: "finance", layer: "D11", reason: "finance evidence" },
  ],
} as unknown as RectificationTechnicalPacket;

test("an unchanged range only advances background plateau state", () => {
  const candidate = {
    rangeStart: "04:30",
    rangeEnd: "06:30",
    workingState: { notes: ["range_plateau_count:50", "keep-me"] },
  };
  const packet = {
    ...pendingPacket,
    candidate: {
      ...pendingPacket.candidate,
      range: { startTime: "04:30", endTime: "06:30" },
    },
  } as RectificationTechnicalPacket;

  const plateauCount = nextPlateauCount(candidate, packet);
  assert.equal(plateauCount, 51);
  assert.deepEqual(convergenceNotes(candidate, plateauCount), ["keep-me", "range_plateau_count:51"]);
});

test("a changed range resets background plateau state without completing the session", () => {
  const candidate = {
    rangeStart: "04:30",
    rangeEnd: "06:30",
    workingState: { notes: ["range_plateau_count:8"] },
  };
  const packet = {
    ...pendingPacket,
    candidate: {
      ...pendingPacket.candidate,
      range: { startTime: "05:10", endTime: "05:40" },
    },
  } as RectificationTechnicalPacket;

  assert.equal(nextPlateauCount(candidate, packet), 0);
});

test("a covered 4-event 3-domain plateau completes as a bounded result", () => {
  assert.equal(shouldCompleteBoundedResult({
    packet: pendingPacket,
    scoreableEventCount: 4,
    scoreableDomainCount: 3,
    answeredDomains: new Set(["relationship", "finance", "career"]),
    plateauCount: 2,
  }), true);
});

test("an unanswered discriminating domain keeps the conversation active", () => {
  assert.equal(shouldCompleteBoundedResult({
    packet: pendingPacket,
    scoreableEventCount: 4,
    scoreableDomainCount: 3,
    answeredDomains: new Set(["relationship", "career", "education"]),
    plateauCount: 2,
  }), false);
});

test("system-only blockers complete a covered range without waiting for another plateau", () => {
  const packet = {
    ...pendingPacket,
    suggestedDomains: [],
    expertWorkflow: { hardBlockers: ["required_layers_incomplete", "minute_holdout_not_ready"] },
  } as unknown as RectificationTechnicalPacket;
  assert.equal(shouldCompleteBoundedResult({
    packet,
    scoreableEventCount: 4,
    scoreableDomainCount: 3,
    answeredDomains: new Set(["relationship", "career", "education"]),
    plateauCount: 0,
  }), true);
});

test("user-resolvable blockers do not complete a bounded result", () => {
  const packet = {
    ...pendingPacket,
    suggestedDomains: [],
    expertWorkflow: { hardBlockers: ["insufficient_events"] },
  } as unknown as RectificationTechnicalPacket;
  assert.equal(shouldCompleteBoundedResult({
    packet,
    scoreableEventCount: 4,
    scoreableDomainCount: 3,
    answeredDomains: new Set(["relationship", "career", "education"]),
    plateauCount: 2,
  }), true, "the completed evidence plateau, not a stale blocker, is decisive");
  assert.equal(shouldCompleteBoundedResult({
    packet,
    scoreableEventCount: 4,
    scoreableDomainCount: 3,
    answeredDomains: new Set(["relationship", "career", "education"]),
    plateauCount: 1,
  }), false);
});
