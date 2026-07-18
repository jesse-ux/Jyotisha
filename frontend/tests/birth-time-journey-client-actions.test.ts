import assert from "node:assert/strict";
import test from "node:test";
import {
  birthTimeJourneyRequestSchema,
  confirmBirthTimeEvidenceDraft,
  finishBirthTimeRectification,
  pauseBirthTimeRectification,
  pollBirthTimeScoring,
  skipBirthTimeEvidenceQuestion,
} from "../src/lib/birth-time-journey-client.ts";
import {
  highConfirmationTurn,
} from "./birth-time-journey-client-test-support.ts";

test("structured mutations require UUID actions and nonnegative versions", () => {
  const base = {
    type: "confirm_evidence_draft",
    caseId: highConfirmationTurn.caseId,
    actionId: "45857b75-4718-4590-aaf5-7113a03ea765",
    turnVersion: 2,
    draftId: "5cb071d6-6d99-46be-85dc-a9bf59ef6ac5",
  } as const;

  const parsed = birthTimeJourneyRequestSchema.parse(base);
  assert.equal(Object.isFrozen(parsed), true);
  assert.equal(birthTimeJourneyRequestSchema.safeParse({
    ...base,
    actionId: "not-a-uuid",
  }).success, false);
  assert.equal(birthTimeJourneyRequestSchema.safeParse({
    ...base,
    turnVersion: -1,
  }).success, false);
  assert.equal(birthTimeJourneyRequestSchema.safeParse({
    ...base,
    turnVersion: 1.5,
  }).success, false);
  assert.equal(birthTimeJourneyRequestSchema.safeParse({
    ...base,
    confidence: "high",
  }).success, false);
  assert.equal(birthTimeJourneyRequestSchema.safeParse({
    ...base,
    score: 99,
  }).success, false);
  assert.equal(birthTimeJourneyRequestSchema.safeParse({
    ...base,
    permissions: { canConfirmCandidate: true },
  }).success, false);
});

test("a lost structured-action response retries the identical serialized receipt", async (context) => {
  const bodies: string[] = [];
  let attempts = 0;
  context.mock.method(globalThis, "fetch", async (_input: string | URL | Request, init?: RequestInit) => {
    attempts += 1;
    bodies.push(String(init?.body));
    if (attempts === 1) throw new TypeError("connection lost after commit");
    return new Response(JSON.stringify(highConfirmationTurn), { status: 200 });
  });

  const result = await confirmBirthTimeEvidenceDraft(
    highConfirmationTurn.caseId,
    "45857b75-4718-4590-aaf5-7113a03ea765",
    2,
    "5cb071d6-6d99-46be-85dc-a9bf59ef6ac5",
  );

  assert.equal(result.turnVersion, highConfirmationTurn.turnVersion);
  assert.equal(attempts, 2);
  assert.equal(bodies[0], bodies[1]);
});

test("HTTP conflicts and aborted requests are never retried", async (context) => {
  let conflictAttempts = 0;
  context.mock.method(globalThis, "fetch", async () => {
    conflictAttempts += 1;
    return new Response(JSON.stringify({ message: "stale" }), { status: 409 });
  });
  await assert.rejects(confirmBirthTimeEvidenceDraft(
    highConfirmationTurn.caseId,
    "45857b75-4718-4590-aaf5-7113a03ea765",
    2,
    "5cb071d6-6d99-46be-85dc-a9bf59ef6ac5",
  ));
  assert.equal(conflictAttempts, 1);

  context.mock.restoreAll();
  let abortAttempts = 0;
  const controller = new AbortController();
  controller.abort();
  context.mock.method(globalThis, "fetch", async () => {
    abortAttempts += 1;
    throw new DOMException("aborted", "AbortError");
  });
  await assert.rejects(pollBirthTimeScoring(
    highConfirmationTurn.caseId,
    "5da741ba-4713-4c27-9cf4-a85e52dc4658",
    controller.signal,
  ));
  assert.equal(abortAttempts, 1);
});

test("client actions submit only their allowed structured fields", async (context) => {
  const payloads: unknown[] = [];
  context.mock.method(
    globalThis,
    "fetch",
    async (_input: string | URL | Request, init?: RequestInit) => {
      payloads.push(JSON.parse(String(init?.body)));
      return new Response(JSON.stringify(highConfirmationTurn), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    },
  );

  await confirmBirthTimeEvidenceDraft(
    highConfirmationTurn.caseId,
    "45857b75-4718-4590-aaf5-7113a03ea765",
    2,
    "5cb071d6-6d99-46be-85dc-a9bf59ef6ac5",
  );
  await skipBirthTimeEvidenceQuestion(
    highConfirmationTurn.caseId,
    "0790866c-ad5e-4a45-b2b4-a5c73f6be6ea",
    3,
  );
  await pauseBirthTimeRectification(
    highConfirmationTurn.caseId,
    "0ef52e51-ab5f-453b-81e5-adb44a929224",
    4,
  );
  await finishBirthTimeRectification(
    highConfirmationTurn.caseId,
    "12dc56f0-1f17-4a2f-86bf-1056ab78def9",
    5,
  );

  assert.deepEqual(payloads, [
    {
      type: "confirm_evidence_draft",
      caseId: highConfirmationTurn.caseId,
      actionId: "45857b75-4718-4590-aaf5-7113a03ea765",
      turnVersion: 2,
      draftId: "5cb071d6-6d99-46be-85dc-a9bf59ef6ac5",
    },
    {
      type: "skip_evidence_question",
      caseId: highConfirmationTurn.caseId,
      actionId: "0790866c-ad5e-4a45-b2b4-a5c73f6be6ea",
      turnVersion: 3,
    },
    {
      type: "pause_rectification",
      caseId: highConfirmationTurn.caseId,
      actionId: "0ef52e51-ab5f-453b-81e5-adb44a929224",
      turnVersion: 4,
    },
    {
      type: "finish_rectification",
      caseId: highConfirmationTurn.caseId,
      actionId: "12dc56f0-1f17-4a2f-86bf-1056ab78def9",
      turnVersion: 5,
    },
  ]);
});
