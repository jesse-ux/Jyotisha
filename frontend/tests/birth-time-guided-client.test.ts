import assert from "node:assert/strict";
import test from "node:test";
import {
  confirmGuidedBirthTimeCandidate,
  reviseBirthTimeEvidenceDraft,
  saveGuidedBirthTimeCandidate,
} from "../src/lib/birth-time-guided-client.ts";
import { birthTimeJourneyRequestSchema } from "../src/lib/birth-time-journey-request.ts";
import { highConfirmationTurn } from "./birth-time-journey-client-test-support.ts";

const actionId = "45857b75-4718-4590-aaf5-7113a03ea765";

test("guided draft revision accepts structured date fields but never a domain", () => {
  const request = {
    type: "revise_evidence_draft",
    caseId: highConfirmationTurn.caseId,
    actionId,
    turnVersion: 2,
    precision: "month",
    date: "2019-07",
  } as const;

  assert.equal(birthTimeJourneyRequestSchema.safeParse(request).success, true);
  assert.equal(birthTimeJourneyRequestSchema.safeParse({ ...request, domain: "career" }).success, false);
  assert.equal(birthTimeJourneyRequestSchema.safeParse({ ...request, date: "2019" }).success, false);
  assert.equal(birthTimeJourneyRequestSchema.safeParse({
    ...request,
    precision: "day",
    date: "2026-02-31",
  }).success, false);
});

test("guided candidate requests require receipt, version, matching result, and time for confirm", () => {
  const save = {
    type: "save_guided_candidate",
    caseId: highConfirmationTurn.caseId,
    actionId,
    turnVersion: 2,
    resultId: highConfirmationTurn.candidateResult.resultId,
  } as const;
  const confirm = {
    ...save,
    type: "confirm_guided_candidate",
    time: highConfirmationTurn.candidateResult.winningSegment.representativeTime,
  } as const;

  assert.equal(birthTimeJourneyRequestSchema.safeParse(save).success, true);
  assert.equal(birthTimeJourneyRequestSchema.safeParse(confirm).success, true);
  assert.equal(birthTimeJourneyRequestSchema.safeParse({ ...save, confidence: "high" }).success, false);
  assert.equal(birthTimeJourneyRequestSchema.safeParse({ ...confirm, activeTime: confirm.time }).success, false);
});

test("guided client emits only deterministic mutation fields", async (context) => {
  const payloads: unknown[] = [];
  context.mock.method(globalThis, "fetch", async (_input: string | URL | Request, init?: RequestInit) => {
    payloads.push(JSON.parse(String(init?.body)));
    return new Response(JSON.stringify(highConfirmationTurn), { status: 200 });
  });

  await reviseBirthTimeEvidenceDraft({ caseId: highConfirmationTurn.caseId, actionId, turnVersion: 2, precision: "month", date: "2019-07" });
  await saveGuidedBirthTimeCandidate({ caseId: highConfirmationTurn.caseId, actionId, turnVersion: 2, resultId: highConfirmationTurn.candidateResult.resultId });
  await confirmGuidedBirthTimeCandidate({ caseId: highConfirmationTurn.caseId, actionId, turnVersion: 2, resultId: highConfirmationTurn.candidateResult.resultId, time: "14:24" });

  assert.deepEqual(payloads, [
    { type: "revise_evidence_draft", caseId: highConfirmationTurn.caseId, actionId, turnVersion: 2, precision: "month", date: "2019-07" },
    { type: "save_guided_candidate", caseId: highConfirmationTurn.caseId, actionId, turnVersion: 2, resultId: highConfirmationTurn.candidateResult.resultId },
    { type: "confirm_guided_candidate", caseId: highConfirmationTurn.caseId, actionId, turnVersion: 2, resultId: highConfirmationTurn.candidateResult.resultId, time: "14:24" },
  ]);
});

test("guided revision and candidate clients reuse receipts after lost responses", async (context) => {
  const bodies: string[] = [];
  let attempts = 0;
  context.mock.method(globalThis, "fetch", async (_input: string | URL | Request, init?: RequestInit) => {
    attempts += 1;
    bodies.push(String(init?.body));
    if (attempts % 2 === 1) throw new TypeError("response lost");
    return new Response(JSON.stringify(highConfirmationTurn), { status: 200 });
  });

  await reviseBirthTimeEvidenceDraft({
    caseId: highConfirmationTurn.caseId,
    actionId,
    turnVersion: 2,
    precision: "month",
    date: "2019-07",
  });
  await saveGuidedBirthTimeCandidate({
    caseId: highConfirmationTurn.caseId,
    actionId,
    turnVersion: 2,
    resultId: highConfirmationTurn.candidateResult.resultId,
  });

  assert.equal(attempts, 4);
  assert.equal(bodies[0], bodies[1]);
  assert.equal(bodies[2], bodies[3]);
});
