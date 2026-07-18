import assert from "node:assert/strict";
import test from "node:test";
import { StaleJourneyTurnError } from "../src/lib/birth-time-journey-turn-persistence.ts";
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

test("confirmed draft advances baseline to the next planned question", async () => {
  const flow = progressionService(guidedCase());
  const proposed = await flow.service.proposeEvidenceDraft(
    "user-1", journeyCaseId, draftActionId, 0,
    { domain: "career", precision: "month", date: "2019-07" },
  );

  const confirmed = await flow.service.confirmEvidenceDraft(
    "user-1", journeyCaseId, confirmActionId, proposed.turnVersion,
    proposed.evidenceDraft?.draftId ?? "",
  );

  assert.equal(confirmed.progress.confirmedEvidenceCount, 1);
  assert.equal(confirmed.nextAction.kind, "ask_baseline_evidence");
  assert.equal(confirmed.turnVersion, 2);
  assert.equal(flow.scoreEventsCalls(), 0);
});

test("third confirmed baseline event persists score pending without engine work", async () => {
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
  const draftId = proposed.evidenceDraft?.draftId ?? "";

  const confirmed = await flow.service.confirmEvidenceDraft(
    "user-1", journeyCaseId, confirmActionId, proposed.turnVersion, draftId,
  );

  assert.equal(confirmed.nextAction.kind, "score_pending");
  assert.equal(confirmed.lifeEvents[2]?.id, draftId);
  assert.equal(flow.scoreEventsCalls(), 0);
});

test("draft proposal cannot change the server-selected domain", async () => {
  const flow = progressionService(guidedCase());

  await assert.rejects(flow.service.proposeEvidenceDraft(
    "user-1", journeyCaseId, draftActionId, 0,
    { domain: "relationship", precision: "year", date: "2021" },
  ));

  assert.equal(flow.memory.committedTurnWrites(), 0);
});

test("incomplete draft can be replaced for the same question and confirmed", async () => {
  const flow = progressionService(guidedCase());
  const incomplete = await flow.service.proposeEvidenceDraft(
    "user-1", journeyCaseId, draftActionId, 0,
    { domain: "career", precision: null, date: null },
  );

  const replacement = await flow.service.proposeEvidenceDraft(
    "user-1", journeyCaseId, secondActionId, incomplete.turnVersion,
    { domain: "career", precision: "year", date: "2019" },
  );
  const confirmed = await flow.service.confirmEvidenceDraft(
    "user-1", journeyCaseId, confirmActionId, replacement.turnVersion,
    replacement.evidenceDraft?.draftId ?? "",
  );

  assert.equal(replacement.evidenceDraft?.questionId, incomplete.evidenceDraft?.questionId);
  assert.equal(confirmed.lifeEvents[0]?.id, replacement.evidenceDraft?.draftId);
  assert.deepEqual(flow.memory.savedCase()?.persistedProgress?.askedDomains, ["career"]);
});

test("incomplete draft can be skipped and discarded", async () => {
  const flow = progressionService(guidedCase());
  const incomplete = await flow.service.proposeEvidenceDraft(
    "user-1", journeyCaseId, draftActionId, 0,
    { domain: "career", precision: null, date: null },
  );

  const skipped = await flow.service.skipEvidenceQuestion(
    "user-1", journeyCaseId, secondActionId, incomplete.turnVersion,
  );

  assert.equal(skipped.evidenceDraft, null);
  assert.equal(skipped.nextAction.kind, "ask_baseline_evidence");
  assert.deepEqual(flow.memory.savedCase()?.persistedProgress?.askedDomains, ["career"]);
});

test("baseline skip marks its domain without consuming an adaptive round", async () => {
  const flow = progressionService(guidedCase());

  const result = await flow.service.skipEvidenceQuestion(
    "user-1", journeyCaseId, draftActionId, 0,
  );

  assert.equal(result.nextAction.kind, "ask_baseline_evidence");
  assert.equal(result.progress.adaptiveRound, 0);
  assert.deepEqual(flow.memory.savedCase()?.persistedProgress?.askedDomains, ["career"]);
});

test("adaptive skips consume displayed rounds once and terminate at three", async () => {
  const flow = progressionService(guidedCase({
    phase: "adaptive",
    domain: "relationship",
    adaptiveRound: 1,
    askedDomains: ["education", "relocation"],
    lifeEvents: [existingEducationEvent, existingCareerEvent],
    candidateResult: lowCandidate,
  }));

  const second = await flow.service.skipEvidenceQuestion(
    "user-1", journeyCaseId, draftActionId, 0,
  );
  const third = await flow.service.skipEvidenceQuestion(
    "user-1", journeyCaseId, secondActionId, second.turnVersion,
  );
  const terminal = await flow.service.skipEvidenceQuestion(
    "user-1", journeyCaseId, thirdActionId, third.turnVersion,
  );

  assert.equal(second.progress.adaptiveRound, 2);
  assert.equal(third.progress.adaptiveRound, 3);
  assert.equal(terminal.nextAction.kind, "present_low_result");
});

test("finish preserves evidence and exposes terminal low", async () => {
  const flow = progressionService(guidedCase({ lifeEvents: [existingEducationEvent] }));

  const finished = await flow.service.finishWithCurrentRange(
    "user-1", journeyCaseId, draftActionId, 0,
  );

  assert.equal(finished.nextAction.kind, "present_low_result");
  assert.deepEqual(finished.lifeEvents, [existingEducationEvent]);
});

test("duplicate draft action returns persisted turn without a second write", async () => {
  const flow = progressionService(guidedCase());
  const first = await flow.service.proposeEvidenceDraft(
    "user-1", journeyCaseId, draftActionId, 0,
    { domain: "career", precision: "year", date: "2019" },
  );

  const duplicate = await flow.service.proposeEvidenceDraft(
    "user-1", journeyCaseId, draftActionId, 0,
    { domain: "career", precision: "year", date: "2019" },
  );

  assert.deepEqual(duplicate.nextAction, first.nextAction);
  assert.equal(flow.memory.committedTurnWrites(), 1);
});

test("stale structured action cannot overwrite the current turn", async () => {
  const flow = progressionService(guidedCase({ version: 5 }));

  await assert.rejects(
    flow.service.skipEvidenceQuestion("user-1", journeyCaseId, draftActionId, 4),
    StaleJourneyTurnError,
  );

  assert.equal(flow.memory.savedCase()?.turnVersion, 5);
  assert.equal(flow.memory.committedTurnWrites(), 0);
});

test("duplicate structured revision replays even after the draft was confirmed", async () => {
  const flow = progressionService(guidedCase());
  const proposed = await flow.service.proposeEvidenceDraft(
    "user-1", journeyCaseId, draftActionId, 0,
    { domain: "career", precision: null, date: null },
  );
  const revised = await flow.service.reviseEvidenceDraft({
    userId: "user-1",
    caseId: journeyCaseId,
    actionId: secondActionId,
    expectedVersion: proposed.turnVersion,
    precision: "year",
    date: "2019",
  });
  const confirmed = await flow.service.confirmEvidenceDraft(
    "user-1", journeyCaseId, thirdActionId, revised.turnVersion,
    revised.evidenceDraft?.draftId ?? "",
  );

  const replay = await flow.service.reviseEvidenceDraft({
    userId: "user-1",
    caseId: journeyCaseId,
    actionId: secondActionId,
    expectedVersion: proposed.turnVersion,
    precision: "year",
    date: "2019",
  });

  assert.equal(replay.turnVersion, confirmed.turnVersion);
  assert.deepEqual(replay.nextAction, confirmed.nextAction);
  assert.equal(flow.memory.committedTurnWrites(), 3);
});
