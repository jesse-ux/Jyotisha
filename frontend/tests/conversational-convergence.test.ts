import assert from "node:assert/strict";
import test from "node:test";
import {
  MAXIMUM_SCOREABLE_EVENTS,
  rangeCompletionReason,
} from "../src/lib/conversational-rectification/convergence.ts";
import type { RectificationTechnicalPacket } from "../src/lib/conversational-rectification/technical-packet.ts";

const pendingPacket = {
  candidate: { status: "pending_validation" },
  suggestedDomains: [
    { domain: "relationship", layer: "D9", reason: "relationship evidence" },
    { domain: "finance", layer: "D11", reason: "finance evidence" },
  ],
} as RectificationTechnicalPacket;

test("does not stop at the evidence count limit while discriminating domains remain unanswered", () => {
  assert.equal(rangeCompletionReason({
    packet: pendingPacket,
    scoreableEventCount: MAXIMUM_SCOREABLE_EVENTS,
    plateauCount: 1,
    unansweredSuggestedDomainCount: 2,
  }), null);
});

test("stops at the evidence count limit after the suggested domains are covered", () => {
  assert.equal(rangeCompletionReason({
    packet: pendingPacket,
    scoreableEventCount: MAXIMUM_SCOREABLE_EVENTS,
    plateauCount: 1,
    unansweredSuggestedDomainCount: 0,
  }), "evidence_limit");
});
