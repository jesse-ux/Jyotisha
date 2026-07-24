import assert from "node:assert/strict";
import test from "node:test";
import {
  convergenceNotes,
  nextPlateauCount,
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
