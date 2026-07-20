import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { candidateResultSchema } from "../src/lib/birth-time-evidence.ts";
import { birthTimeJourneyRequestSchema } from "../src/lib/birth-time-journey-request.ts";
import { createBirthTimeJourneyService } from "../src/lib/birth-time-journey-service.ts";
import { StaleJourneyTurnError } from "../src/lib/birth-time-journey-turn-persistence.ts";
import { actionId, dynamicCase, ownerId } from "./birth-time-dynamic-persistence-fixture.ts";
import { memoryStore } from "./birth-time-journey-memory-store.ts";

const highCandidate = candidateResultSchema.parse({
  resultId: "f8eb3bc5-80eb-40fc-b937-e62ea37c3236",
  confidence: "high",
  canApply: true,
  winningSegment: {
    startTime: "17:13",
    endTime: "17:17",
    representativeTime: "17:15",
    widthMinutes: 5,
  },
  eventCount: 4,
  domainCount: 3,
  topScore: 18,
  secondScore: 8,
  marginPercent: 55,
  reasons: ["One segment has consistent evidence."],
  evidence: [],
  algorithmVersion: "birth-time-event-scoring-v1",
});

const migration = readFileSync(new URL(
  "../supabase/migrations/20260720000000_chat_delete_and_dynamic_candidate_confirmation.sql",
  import.meta.url,
), "utf8");

function highConfidenceDynamicCase() {
  const current = dynamicCase();
  return {
    ...current,
    candidateResult: highCandidate,
    snapshot: {
      ...current.snapshot,
      state: "confirming" as const,
      assistantIntent: "confirm_candidate_time" as const,
      input: "candidate_confirmation" as const,
      confidence: "high" as const,
      canApply: true,
    },
    currentChoiceQuestion: null,
    dynamicTurnState: {
      ...current.dynamicTurnState,
      nextAction: {
        kind: "request_candidate_confirmation" as const,
        resultId: highCandidate.resultId,
      },
      progress: { ...current.dynamicTurnState.progress, phase: "result" as const },
      permissions: { canConfirmCandidate: true },
    },
  };
}

test("dynamic confirmation atomically reaches ready", async () => {
  const current = highConfidenceDynamicCase();
  const memory = memoryStore(current);
  const service = createBirthTimeJourneyService({
    store: memory.store,
    engine: {
      async scan() { throw new Error("unexpected scan"); },
      async score() { throw new Error("unexpected score"); },
      async scoreEvents() { throw new Error("unexpected event score"); },
      async buildDifferencePacket() { throw new Error("unexpected packet"); },
      async scoreChoices() { throw new Error("unexpected choice score"); },
    },
  });

  const result = await service.confirmDynamicCandidate({
    userId: ownerId,
    caseId: current.id,
    actionId,
    expectedVersion: current.dynamicTurnState.turnVersion,
    resultId: current.candidateResult.resultId,
    time: current.candidateResult.winningSegment?.representativeTime ?? "",
  });

  assert.equal(result.nextAction.kind, "ready");
  assert.equal(result.snapshot.activeTime, "17:15");
});

test("dynamic confirmation replays only its exact receipt and rejects stale versions", async () => {
  const current = highConfidenceDynamicCase();
  const memory = memoryStore(current);
  const service = createBirthTimeJourneyService({
    store: memory.store,
    engine: {
      async scan() { throw new Error("unexpected scan"); },
      async score() { throw new Error("unexpected score"); },
      async scoreEvents() { throw new Error("unexpected event score"); },
      async buildDifferencePacket() { throw new Error("unexpected packet"); },
      async scoreChoices() { throw new Error("unexpected choice score"); },
    },
  });
  const command = {
    userId: ownerId,
    caseId: current.id,
    actionId,
    expectedVersion: current.turnVersion,
    resultId: highCandidate.resultId,
    time: "17:15",
  };

  const first = await service.confirmDynamicCandidate(command);
  const replay = await service.confirmDynamicCandidate(command);

  assert.deepEqual(replay, first);
  assert.equal(memory.committedTurnWrites(), 1);
  await assert.rejects(service.confirmDynamicCandidate({
    ...command,
    actionId: "f3a64be6-65d3-498c-a86d-847cf104e594",
  }), StaleJourneyTurnError);
});

test("dynamic confirmation rejects a non-representative minute before writing", async () => {
  const current = highConfidenceDynamicCase();
  const memory = memoryStore(current);
  const service = createBirthTimeJourneyService({
    store: memory.store,
    engine: {
      async scan() { throw new Error("unexpected scan"); },
      async score() { throw new Error("unexpected score"); },
      async scoreEvents() { throw new Error("unexpected event score"); },
      async buildDifferencePacket() { throw new Error("unexpected packet"); },
      async scoreChoices() { throw new Error("unexpected choice score"); },
    },
  });

  await assert.rejects(service.confirmDynamicCandidate({
    userId: ownerId,
    caseId: current.id,
    actionId,
    expectedVersion: current.turnVersion,
    resultId: highCandidate.resultId,
    time: "17:14",
  }), StaleJourneyTurnError);
  assert.equal(memory.committedTurnWrites(), 0);
});

test("dynamic confirmation request accepts only its strict receipt, version, result, and time", () => {
  const valid = {
    type: "confirm_dynamic_candidate",
    caseId: dynamicCase().id,
    actionId,
    turnVersion: 7,
    resultId: highCandidate.resultId,
    time: "17:15",
  } as const;

  assert.equal(birthTimeJourneyRequestSchema.safeParse(valid).success, true);
  assert.equal(birthTimeJourneyRequestSchema.safeParse({ ...valid, time: "17:15:00" }).success, false);
  assert.equal(birthTimeJourneyRequestSchema.safeParse({ ...valid, turnVersion: -1 }).success, false);
  assert.equal(birthTimeJourneyRequestSchema.safeParse({ ...valid, candidateResult: highCandidate }).success, false);
});

test("dynamic confirmation RPC locks the v2 case and is service-role only", () => {
  assert.match(migration, /create function public\.confirm_birth_time_dynamic_candidate\([\s\S]*?returns bigint/i);
  assert.match(migration, /for update[\s\S]*journey_protocol is distinct from 'dynamic-choice-v2'/i);
  assert.match(migration, /p_action_id = any\(v_case\.processed_action_ids\)/i);
  assert.match(migration, /candidate_result_id is distinct from p_result_id[\s\S]*representativeTime/i);
  assert.match(migration, /turn_version = p_expected_version \+ 1[\s\S]*turn_state = p_turn_state/i);
  assert.match(migration, /set active_birth_time = p_time,[\s\S]*birth_time_status = 'confirmed',[\s\S]*rectification_case_id = p_case_id/i);
  assert.match(migration, /revoke all on function public\.confirm_birth_time_dynamic_candidate\([\s\S]*?from public, anon, authenticated;[\s\S]*?grant execute on function public\.confirm_birth_time_dynamic_candidate\([\s\S]*?to service_role;/i);
});
