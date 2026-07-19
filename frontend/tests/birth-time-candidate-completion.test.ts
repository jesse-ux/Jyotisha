import assert from "node:assert/strict";
import test from "node:test";
import { candidateWorkingTime } from "../src/lib/birth-time-candidate-completion.ts";

const terminalCase = {
  id: "5425f9e7-3d45-491d-aab3-24cfd4261d51",
  user_id: "07e583fc-90b9-4fcb-a9d3-8de654eeac9a",
  status: "candidate",
  candidate_result_id: "d9133ba2-afcf-56da-b40b-ace3d7124a7d",
  candidate_result: {
    confidence: "medium",
    winningSegment: { representativeTime: "04:53" },
  },
  turn_state: {
    nextAction: {
      kind: "present_medium_result",
      resultId: "d9133ba2-afcf-56da-b40b-ace3d7124a7d",
    },
  },
};

const lowTerminalCase = {
  ...terminalCase,
  status: "rectifying",
  candidate_result: {
    ...terminalCase.candidate_result,
    confidence: "low",
  },
  turn_state: {
    ...terminalCase.turn_state,
    nextAction: {
      kind: "present_low_result",
      resultId: terminalCase.candidate_result_id,
    },
  },
};

test("candidate completion only accepts the persisted terminal representative time", () => {
  assert.equal(candidateWorkingTime(terminalCase, {
    caseId: terminalCase.id,
    resultId: terminalCase.candidate_result_id,
    time: "04:53",
  }), "04:53");

  assert.equal(candidateWorkingTime(terminalCase, {
    caseId: terminalCase.id,
    resultId: terminalCase.candidate_result_id,
    time: "04:54",
  }), null);
});

test("accepts a matching low-confidence result from the rectifying state", () => {
  assert.equal(candidateWorkingTime(lowTerminalCase, {
    caseId: terminalCase.id,
    resultId: terminalCase.candidate_result_id,
    time: "04:53",
  }), "04:53");
});

test("does not accept a medium terminal action from the rectifying state", () => {
  assert.equal(candidateWorkingTime({
    ...lowTerminalCase,
    turn_state: {
      ...lowTerminalCase.turn_state,
      nextAction: {
        kind: "present_medium_result",
        resultId: terminalCase.candidate_result_id,
      },
    },
  }, {
    caseId: terminalCase.id,
    resultId: terminalCase.candidate_result_id,
    time: "04:53",
  }), null);
});

test("non-terminal cases cannot be adopted for consultation", () => {
  assert.equal(candidateWorkingTime({
    ...terminalCase,
    turn_state: { nextAction: { kind: "ask_dynamic_choice" } },
  }, {
    caseId: terminalCase.id,
    resultId: terminalCase.candidate_result_id,
    time: "04:53",
  }), null);
});
