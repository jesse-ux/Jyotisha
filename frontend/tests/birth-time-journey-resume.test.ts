import assert from "node:assert/strict";
import test from "node:test";
import { lifeEventSchema } from "../src/lib/birth-time-journey.ts";
import {
  confirmActionId,
  draftActionId,
  existingCareerEvent,
  existingEducationEvent,
  guidedCase,
  journeyCaseId,
  lowCandidate,
  progressionService,
  secondActionId,
  thirdActionId,
} from "./birth-time-journey-test-support.ts";

const relationshipEvent = lifeEventSchema.parse({
  id: "0ef52e51-ab5f-453b-81e5-adb44a929224",
  domain: "relationship",
  precision: "year",
  date: "2021",
});

test("legacy dead-end resume reconstructs one baseline ask", async () => {
  const legacy = guidedCase({ lifeEvents: [existingEducationEvent] });
  const snapshot = {
    ...legacy.snapshot,
    input: "life_events",
    assistantIntent: "collect_dated_life_events",
  } as const;
  const flow = progressionService({ ...legacy, snapshot, turnState: null });

  const result = await flow.service.resume("user-1", journeyCaseId);

  assert.equal(result.nextAction.kind, "ask_baseline_evidence");
  assert.equal(result.turnVersion, 0);
  assert.equal(flow.scoreEventsCalls(), 0);
});

test("legacy low-score resume displays adaptive round one exactly once", async () => {
  const legacy = guidedCase({
    lifeEvents: [existingEducationEvent, existingCareerEvent],
    candidateResult: lowCandidate,
  });
  const snapshot = { ...legacy.snapshot, input: "life_events" } as const;
  const flow = progressionService({ ...legacy, snapshot, turnState: null });

  const first = await flow.service.resume("user-1", journeyCaseId);
  const second = await flow.service.resume("user-1", journeyCaseId);

  assert.equal(first.nextAction.kind, "ask_adaptive_evidence");
  assert.equal(first.progress.adaptiveRound, 1);
  assert.deepEqual(second.nextAction, first.nextAction);
  assert.equal(second.turnVersion, first.turnVersion);
  assert.equal(flow.scoreEventsCalls(), 0);
});

test("resume restores the deterministic baseline ask after pause", async () => {
  const flow = progressionService(guidedCase({ lifeEvents: [existingEducationEvent] }));
  const paused = await flow.service.pause(
    "user-1", journeyCaseId, draftActionId, 0,
  );

  const first = await flow.service.resume("user-1", journeyCaseId);
  const second = await flow.service.resume("user-1", journeyCaseId);

  assert.equal(paused.nextAction.kind, "paused");
  assert.equal(first.nextAction.kind, "ask_baseline_evidence");
  assert.deepEqual(second.nextAction, first.nextAction);
  assert.equal(second.turnVersion, paused.turnVersion);
  assert.equal(flow.scoreEventsCalls(), 0);
});

test("resume restores the same evidence draft after review is paused", async () => {
  const flow = progressionService(guidedCase());
  const proposed = await flow.service.proposeEvidenceDraft(
    "user-1", journeyCaseId, draftActionId, 0,
    { domain: "career", precision: null, date: null },
  );
  const paused = await flow.service.pause(
    "user-1", journeyCaseId, secondActionId, proposed.turnVersion,
  );

  const resumed = await flow.service.resume("user-1", journeyCaseId);

  assert.equal(paused.nextAction.kind, "paused");
  assert.deepEqual(resumed.nextAction, {
    kind: "review_evidence_draft",
    draftId: proposed.evidenceDraft?.draftId,
  });
  assert.deepEqual(resumed.evidenceDraft, proposed.evidenceDraft);
  assert.equal(resumed.turnVersion, paused.turnVersion);
});

test("pause rejects score pending so its job identity cannot be lost", async () => {
  const flow = progressionService(guidedCase({
    version: 4,
    domain: "relationship",
    askedDomains: ["education", "career"],
    lifeEvents: [existingEducationEvent, existingCareerEvent],
  }));
  const proposed = await flow.service.proposeEvidenceDraft(
    "user-1", journeyCaseId, draftActionId, 4,
    { domain: "relationship", precision: "year", date: "2021" },
  );
  const scoring = await flow.service.confirmEvidenceDraft(
    "user-1", journeyCaseId, confirmActionId, proposed.turnVersion,
    proposed.evidenceDraft?.draftId ?? "",
  );

  await assert.rejects(flow.service.pause(
    "user-1", journeyCaseId, thirdActionId, scoring.turnVersion,
  ));

  assert.equal(flow.memory.savedCase()?.turnVersion, scoring.turnVersion);
  assert.equal(flow.memory.savedCase()?.turnState?.nextAction.kind, "score_pending");
});

test("legacy complete evidence resumes as one deterministic score pending seam", async () => {
  const legacy = guidedCase({
    lifeEvents: [existingEducationEvent, existingCareerEvent, relationshipEvent],
  });
  const snapshot = {
    ...legacy.snapshot,
    input: "life_events",
    assistantIntent: "collect_dated_life_events",
  } as const;
  const flow = progressionService({ ...legacy, snapshot, turnState: null });

  const first = await flow.service.resume("user-1", journeyCaseId);
  const second = await flow.service.resume("user-1", journeyCaseId);

  assert.deepEqual(first.nextAction, { kind: "score_pending", jobId: journeyCaseId });
  assert.deepEqual(second.nextAction, first.nextAction);
  assert.equal(second.turnVersion, 0);
  assert.equal(flow.scoreEventsCalls(), 0);
});
