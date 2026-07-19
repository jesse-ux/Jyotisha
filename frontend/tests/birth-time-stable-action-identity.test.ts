import assert from "node:assert/strict";
import test from "node:test";
import {
  createStableActionIdentityRegistry,
  runStableJourneyAction,
  stableActionIdentity,
} from "../src/lib/birth-time-guided-effect-coordinator.ts";
import {
  answerDynamicBirthTimeChoice,
  generateDynamicBirthTimeQuestion,
} from "../src/lib/birth-time-journey-client.ts";
import { storedDynamicJourneyResponse } from "../src/lib/birth-time-journey-response.ts";
import { dynamicCase, persistedQuestion } from "./birth-time-dynamic-persistence-fixture.ts";

const firstId = "45857b75-4718-4590-aaf5-7113a03ea765";
const secondId = "0790866c-ad5e-4a45-b2b4-a5c73f6be6ea";

test("stable action identities survive failures and clear only after success", async () => {
  const ids = [firstId, secondId];
  const registry = createStableActionIdentityRegistry(
    () => ids.shift() ?? assert.fail("unexpected id allocation"),
  );
  const seen: string[] = [];
  const identity = stableActionIdentity({
    caseId: "case-a", turnVersion: 7, operation: "answer_dynamic_choice",
    payload: ["question-a", "option-a"],
  });
  const fail = () => registry.run(identity, async (actionId) => {
    seen.push(actionId);
    throw new TypeError("offline");
  });

  await assert.rejects(fail());
  await assert.rejects(fail());
  await registry.run(identity, async (actionId) => { seen.push(actionId); });
  await registry.run(identity, async (actionId) => { seen.push(actionId); });

  assert.deepEqual(seen, [firstId, firstId, firstId, secondId]);
});

test("action identity separates options, notes, and new turns", () => {
  const base = {
    caseId: "case-a", turnVersion: 7, operation: "answer_dynamic_choice",
    payload: ["question-a", "option-a"],
  } as const;

  assert.equal(stableActionIdentity(base), stableActionIdentity(base));
  assert.notEqual(stableActionIdentity(base), stableActionIdentity({ ...base, payload: ["question-a", "option-b"] }));
  assert.notEqual(stableActionIdentity(base), stableActionIdentity({ ...base, turnVersion: 8 }));
  assert.notEqual(
    stableActionIdentity({ ...base, operation: "reframe_unmatched", payload: ["question-a", "较早"] }),
    stableActionIdentity({ ...base, operation: "reframe_unmatched", payload: ["question-a", "较晚"] }),
  );
});

async function lostResponseRetry(
  context: test.TestContext,
  operation: "answer_dynamic_choice" | "generate_dynamic_question",
  send: (actionId: string) => Promise<unknown>,
) {
  const bodies: string[] = [];
  let attempts = 0;
  context.mock.method(globalThis, "fetch", async (_input: string | URL | Request, init?: RequestInit) => {
    attempts += 1;
    bodies.push(String(init?.body));
    if (attempts <= 2) throw new TypeError("response lost");
    return new Response(JSON.stringify(storedDynamicJourneyResponse(dynamicCase())), { status: 200 });
  });
  const registry = createStableActionIdentityRegistry(() => firstId);
  const identity = { caseId: dynamicCase().id, turnVersion: 7, operation } as const;

  await assert.rejects(runStableJourneyAction(registry, identity, send));
  await runStableJourneyAction(registry, identity, send);

  assert.equal(attempts, 3);
  assert.equal(new Set(bodies).size, 1);
  assert.equal(JSON.parse(bodies[0]).actionId, firstId);
}

test("two lost choice responses and a manual retry send one exact receipt", async (context) => {
  await lostResponseRetry(context, "answer_dynamic_choice", (actionId) => answerDynamicBirthTimeChoice({
    caseId: dynamicCase().id,
    actionId,
    turnVersion: 7,
    questionId: persistedQuestion.questionId,
    optionId: persistedQuestion.options[0].optionId,
  }));
});

test("failed automatic generation reuses its action id on manual retry", async (context) => {
  await lostResponseRetry(context, "generate_dynamic_question", (actionId) => (
    generateDynamicBirthTimeQuestion(dynamicCase().id, actionId, 7)
  ));
});
