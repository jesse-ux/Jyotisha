import assert from "node:assert/strict";
import test from "node:test";
import {
  dynamicChoiceScoreInput,
  dynamicDifferenceInput,
} from "../src/lib/birth-time-dynamic-engine-input.ts";
import { dynamicCase } from "./birth-time-dynamic-persistence-fixture.ts";

function matchingCandidateModel(activation = 0) {
  return {
    version: "birth-time-choice-scoring-v2",
    opportunity_model_version: "birth-time-opportunity-model-v4",
    historical_event_fingerprint: "fixture-event-fingerprint",
    range: { start_time: "05:02", end_time: "05:03" },
    windows: [{
      activations: { "05:02": activation, "05:03": 1 },
      fact_selection_priority: 1,
      fact_priority_version: "birth-time-question-fact-priority-v1",
      event_fact_selection_priority: 0,
      event_fact_priority_version: "birth-time-question-event-fact-priority-v1",
    }],
  };
}

function narrowedCase(startTime = "05:02", endTime = "05:03") {
  const stored = dynamicCase();
  return {
    ...stored,
    eventContext: {
      birthDate: "1993-04-17",
      lat: 31.23,
      lon: 121.47,
      tz: 8,
    },
    choiceEvidence: [{
      questionId: "prior-question",
      opportunityId: "prior-opportunity",
      partitionId: "prior-partition",
      dimensionCode: "relocation_change",
      candidateScores: {
        "05:00": 0,
        "05:01": 0.25,
        "05:02": 0.5,
        "05:03": 0.75,
        "05:04": 1,
      },
      informationGain: 0.4,
    }],
    candidateModel: {
      version: "birth-time-choice-scoring-v2",
      range: { start_time: "05:00", end_time: "05:04" },
    },
    dynamicTurnState: {
      ...stored.dynamicTurnState,
      progress: {
        ...stored.dynamicTurnState.progress,
        currentRange: { startTime, endTime },
      },
    },
  };
}

test("narrowed scoring projects prior evidence onto the current candidate range", () => {
  const input = dynamicChoiceScoreInput(narrowedCase());

  assert.deepEqual(input.evidence[0]?.candidateScores, {
    "05:02": 0.5,
    "05:03": 0.75,
  });
});

test("narrowed question generation rebuilds a candidate model for the current range", () => {
  const input = dynamicDifferenceInput(narrowedCase());

  assert.deepEqual(input.evidence[0]?.candidateScores, {
    "05:02": 0.5,
    "05:03": 0.75,
  });
  assert.equal(input.candidateModel, null);
});

test("matching candidate models remain reusable", () => {
  const stored = narrowedCase();
  const matchingModel = matchingCandidateModel();
  const input = dynamicDifferenceInput({ ...stored, candidateModel: matchingModel });

  assert.equal(input.candidateModel, matchingModel);
});

test("legacy v2 candidate models are rebuilt for fact-driven question selection", () => {
  const stored = narrowedCase();
  const matchingModel = {
    ...matchingCandidateModel(),
    opportunity_model_version: "birth-time-opportunity-model-v2",
  };

  const input = dynamicDifferenceInput({ ...stored, candidateModel: matchingModel });

  assert.equal(input.candidateModel, null);
});

test("persisted candidate models with legacy negative activations are rebuilt", () => {
  const stored = narrowedCase();
  const input = dynamicDifferenceInput({
    ...stored,
    candidateModel: matchingCandidateModel(-0.2),
  });

  assert.equal(input.candidateModel, null);
});

test("evidence projection preserves cross-midnight candidate chronology", () => {
  const stored = narrowedCase("23:59", "00:00");
  const input = dynamicChoiceScoreInput({
    ...stored,
    choiceEvidence: [{
      ...stored.choiceEvidence[0],
      candidateScores: { "23:58": 0, "23:59": 0.25, "00:00": 0.5, "00:01": 0.75 },
    }],
  });

  assert.deepEqual(input.evidence[0]?.candidateScores, {
    "23:59": 0.25,
    "00:00": 0.5,
  });
});
