import assert from "node:assert/strict";
import test from "node:test";
import {
  BirthTimeJourneyStoreError,
  createJourneyTurnPersistence,
  loadStoredRectificationCase,
  StaleJourneyTurnError,
} from "../src/lib/birth-time-journey-turn-persistence.ts";

const actionId = "45857b75-4718-4590-aaf5-7113a03ea765";
const storedCase = {
  id: "case-1",
  userId: "user-1",
  snapshot: { state: "rectifying" },
  answers: {},
  turnState: { nextAction: { kind: "paused" } },
  evidenceDraft: null,
  processedActionIds: [],
  persistedProgress: { adaptiveRound: 0, askedDomains: [] },
};

function updateClient(result) {
  const calls = [];
  const filter = {
    eq(column, value) {
      calls.push([column, value]);
      return filter;
    },
    not(column, operator, value) {
      calls.push(["not", column, operator, value]);
      return filter;
    },
    select(columns) {
      calls.push(["select", columns]);
      return filter;
    },
    async maybeSingle() {
      return result;
    },
  };
  return {
    calls,
    client: {
      from(table) {
        assert.equal(table, "birth_time_rectification_cases");
        return {
          update(values) {
            calls.push(["update", values]);
            return filter;
          },
        };
      },
    },
  };
}

test("saveTurn uses one owner-and-version-constrained update", async () => {
  const fake = updateClient({ data: { id: "case-1" }, error: null });
  const persistence = createJourneyTurnPersistence(fake.client, async () => null);

  const saved = await persistence.saveTurn(storedCase, 4, actionId);

  assert.equal(saved.turnVersion, 5);
  assert.deepEqual(saved.processedActionIds, [actionId]);
  assert.deepEqual(fake.calls, [
    ["update", {
      status: "rectifying",
      journey_snapshot: storedCase.snapshot,
      answers: {},
      life_events: [],
      candidate_result: {},
      turn_version: 5,
      turn_state: storedCase.turnState,
      evidence_draft: null,
      processed_action_ids: [actionId],
      adaptive_round: 0,
      asked_domains: [],
      updated_at: fake.calls[0][1].updated_at,
    }],
    ["id", "case-1"],
    ["user_id", "user-1"],
    ["turn_version", 4],
    ["not", "processed_action_ids", "cs", `{${actionId}}`],
    ["select", "id"],
  ]);
});

test("saveTurn reloads only a conflicting write and returns duplicate receipt", async () => {
  const fake = updateClient({ data: null, error: null });
  const current = { ...storedCase, turnVersion: 5, processedActionIds: [actionId] };
  const persistence = createJourneyTurnPersistence(fake.client, async () => current);

  const saved = await persistence.saveTurn(storedCase, 4, actionId);

  assert.equal(saved, current);
});

test("saveTurn throws a typed stale error after a conflicting unprocessed action", async () => {
  const fake = updateClient({ data: null, error: null });
  const current = { ...storedCase, turnVersion: 5 };
  const persistence = createJourneyTurnPersistence(fake.client, async () => current);

  await assert.rejects(
    persistence.saveTurn(storedCase, 4, actionId),
    StaleJourneyTurnError,
  );
});

test("saveTurn returns a same-version replay without a second receipt", async () => {
  const fake = updateClient({ data: null, error: null });
  const current = { ...storedCase, turnVersion: 4, processedActionIds: [actionId] };
  const persistence = createJourneyTurnPersistence(fake.client, async () => current);

  const saved = await persistence.saveTurn(storedCase, 4, actionId);

  assert.equal(saved, current);
  assert.equal(saved.turnVersion, 4);
  assert.deepEqual(saved.processedActionIds, [actionId]);
});

test("saveTurn treats an uppercase UUID replay as the stored lowercase receipt", async () => {
  const fake = updateClient({ data: null, error: null });
  const current = { ...storedCase, turnVersion: 4, processedActionIds: [actionId] };
  const persistence = createJourneyTurnPersistence(fake.client, async () => current);

  const saved = await persistence.saveTurn(storedCase, 4, actionId.toUpperCase());

  assert.equal(saved, current);
  assert.equal(fake.calls[0][1].processed_action_ids[0], actionId);
  assert.deepEqual(fake.calls[4], ["not", "processed_action_ids", "cs", `{${actionId}}`]);
});

test("saveTurn rejects a non-UUID action receipt before writing", async () => {
  const fake = updateClient({ data: { id: "case-1" }, error: null });
  const persistence = createJourneyTurnPersistence(fake.client, async () => null);

  await assert.rejects(persistence.saveTurn(storedCase, 4, "not-a-uuid"));

  assert.deepEqual(fake.calls, []);
});

test("saveTurn writes asked domains in canonical unique order", async () => {
  const fake = updateClient({ data: { id: "case-1" }, error: null });
  const persistence = createJourneyTurnPersistence(fake.client, async () => null);
  const value = {
    ...storedCase,
    persistedProgress: { adaptiveRound: 0, askedDomains: ["career", "education", "career"] },
  };

  const saved = await persistence.saveTurn(value, 4, actionId);

  assert.deepEqual(fake.calls[0][1].asked_domains, ["education", "career"]);
  assert.deepEqual(saved.persistedProgress.askedDomains, ["education", "career"]);
});

function storedRow(overrides = {}) {
  return {
    id: "45857b75-4718-4590-aaf5-7113a03ea765",
    user_id: "12dc56f0-1f17-4a2f-86bf-1056ab78def9",
    journey_snapshot: {
      state: "rectifying", assistantIntent: "continue_rectification_questions", input: "rectification_questions",
      route: "rectification", confidence: null, canApply: false, activeTime: null,
      reportedRange: { label: "14:00—15:00", startTime: "14:00", endTime: "15:00" },
    },
    questionnaire: {}, answers: {}, scoring_result: {}, reported_date: "1993-04-17",
    life_events: [], candidate_result: {}, turn_version: 4, turn_state: {}, evidence_draft: null,
    processed_action_ids: [], adaptive_round: 0, asked_domains: [],
    ...overrides,
  };
}

function loadClient(row) {
  const filter = { eq() { return filter; }, async maybeSingle() { return { data: row, error: null }; } };
  const profile = { eq() { return profile; }, async maybeSingle() {
    return { data: { latitude: 31.2304, longitude: 121.4737, timezone_offset: 8 }, error: null };
  } };
  return { from(table) { return { select() { return table === "profiles" ? profile : filter; } }; } };
}

test("load accepts only the exact empty legacy turn state", async () => {
  const value = await loadStoredRectificationCase(loadClient(storedRow()), "12dc56f0-1f17-4a2f-86bf-1056ab78def9", "45857b75-4718-4590-aaf5-7113a03ea765");

  assert.equal(value?.turnState, null);
});

test("load rejects a malformed nonempty persisted turn state", async () => {
  await assert.rejects(
    loadStoredRectificationCase(loadClient(storedRow({ turn_state: { turnVersion: 1 } })), "12dc56f0-1f17-4a2f-86bf-1056ab78def9", "45857b75-4718-4590-aaf5-7113a03ea765"),
    BirthTimeJourneyStoreError,
  );
});

test("load rejects a malformed non-null persisted evidence draft", async () => {
  await assert.rejects(
    loadStoredRectificationCase(loadClient(storedRow({ evidence_draft: {} })), "12dc56f0-1f17-4a2f-86bf-1056ab78def9", "45857b75-4718-4590-aaf5-7113a03ea765"),
    BirthTimeJourneyStoreError,
  );
});
