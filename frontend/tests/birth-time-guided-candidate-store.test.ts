import assert from "node:assert/strict";
import test from "node:test";
import {
  createSupabaseGuidedCandidateStore,
  type GuidedCandidateRpcClient,
} from "../src/lib/birth-time-guided-candidate-store.ts";
import { BirthTimeJourneyStoreError } from "../src/lib/birth-time-journey-turn-persistence.ts";
import {
  draftActionId,
  guidedCase,
  journeyCaseId,
  lowCandidate,
} from "./birth-time-journey-test-support.ts";

function failingRpc(message: string, code = "08006"): GuidedCandidateRpcClient {
  return {
    rpc() {
      return Promise.resolve({ error: { code, message } });
    },
  };
}

test("an RPC error reloads the owner-scoped case and replays a committed receipt", async () => {
  const value = guidedCase({ candidateResult: lowCandidate });
  const committed = {
    ...value,
    processedActionIds: [draftActionId],
  };
  let reloaded = 0;
  const store = createSupabaseGuidedCandidateStore(
    failingRpc("connection reset after commit"),
    async (userId, caseId) => {
      reloaded += 1;
      assert.equal(userId, value.userId);
      assert.equal(caseId, journeyCaseId);
      return committed;
    },
  );

  const result = await store.commitGuidedCandidate(value, {
    kind: "save",
    actionId: draftActionId,
    expectedVersion: value.turnVersion ?? 0,
  });

  assert.equal(result, committed);
  assert.equal(reloaded, 1);
});

test("an RPC infrastructure error without a receipt stays unavailable", async () => {
  const value = guidedCase({ candidateResult: lowCandidate });
  const store = createSupabaseGuidedCandidateStore(
    failingRpc("connection reset"),
    async () => value,
  );

  await assert.rejects(
    store.commitGuidedCandidate(value, {
      kind: "save",
      actionId: draftActionId,
      expectedVersion: value.turnVersion ?? 0,
    }),
    BirthTimeJourneyStoreError,
  );
});
