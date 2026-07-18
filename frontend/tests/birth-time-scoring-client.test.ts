import assert from "node:assert/strict";
import test from "node:test";
import {
  birthTimeJourneyRequestSchema,
  pollBirthTimeScoring,
} from "../src/lib/birth-time-journey-client.ts";
import { highConfirmationTurn } from "./birth-time-journey-client-test-support.ts";

const jobId = "c70ea014-f8b4-41f2-9305-e4ae60c0d4d1";

test("poll scoring accepts only case and job identifiers", () => {
  const request = {
    type: "poll_scoring",
    caseId: highConfirmationTurn.caseId,
    jobId,
  } as const;

  const parsed = birthTimeJourneyRequestSchema.parse(request);
  assert.equal(Object.isFrozen(parsed), true);
  for (const injected of [
    { score: 99 },
    { confidence: "high" },
    { result: highConfirmationTurn.candidateResult },
    { activeTime: "14:24" },
    { evidence: [] },
  ]) {
    assert.equal(birthTimeJourneyRequestSchema.safeParse({ ...request, ...injected }).success, false);
  }
});

test("poll scoring client sends no deterministic result fields", async (context) => {
  let payload: unknown = null;
  context.mock.method(
    globalThis,
    "fetch",
    async (_input: string | URL | Request, init?: RequestInit) => {
      payload = JSON.parse(String(init?.body));
      return new Response(JSON.stringify(highConfirmationTurn), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    },
  );

  await pollBirthTimeScoring(highConfirmationTurn.caseId, jobId);

  assert.deepEqual(payload, {
    type: "poll_scoring",
    caseId: highConfirmationTurn.caseId,
    jobId,
  });
});
