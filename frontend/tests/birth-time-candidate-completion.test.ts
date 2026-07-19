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

const completionRequest = {
  userId: terminalCase.user_id,
  caseId: terminalCase.id,
  resultId: terminalCase.candidate_result_id,
  time: "04:53",
} as const;

test("candidate completion only accepts the persisted terminal representative time", () => {
  assert.equal(candidateWorkingTime(terminalCase, {
    ...completionRequest,
  }), "04:53");

  assert.equal(candidateWorkingTime(terminalCase, {
    ...completionRequest,
    time: "04:54",
  }), null);
});

test("accepts a matching low-confidence result from the rectifying state", () => {
  assert.equal(candidateWorkingTime(lowTerminalCase, {
    ...completionRequest,
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
    ...completionRequest,
  }), null);
});

test("non-terminal cases cannot be adopted for consultation", () => {
  assert.equal(candidateWorkingTime({
    ...terminalCase,
    turn_state: { nextAction: { kind: "ask_dynamic_choice" } },
  }, {
    ...completionRequest,
  }), null);
});

const rejectedCompletions = [
  {
    name: "case owned by another user",
    stored: { ...terminalCase, user_id: "f6cf99a5-9af7-4980-93ea-0298ee1dc95e" },
    request: completionRequest,
  },
  {
    name: "request from another user",
    stored: terminalCase,
    request: { ...completionRequest, userId: "f6cf99a5-9af7-4980-93ea-0298ee1dc95e" },
  },
  {
    name: "wrong case ID",
    stored: terminalCase,
    request: { ...completionRequest, caseId: "c84052ca-bcea-40a8-a32a-56980bbf7b22" },
  },
  {
    name: "wrong persisted result ID",
    stored: { ...terminalCase, candidate_result_id: "a3e41512-9fa0-4866-a187-e3b3aa07aee0" },
    request: completionRequest,
  },
  {
    name: "wrong action result ID",
    stored: {
      ...terminalCase,
      turn_state: {
        nextAction: {
          ...terminalCase.turn_state.nextAction,
          resultId: "a3e41512-9fa0-4866-a187-e3b3aa07aee0",
        },
      },
    },
    request: completionRequest,
  },
  {
    name: "wrong requested result ID",
    stored: terminalCase,
    request: { ...completionRequest, resultId: "a3e41512-9fa0-4866-a187-e3b3aa07aee0" },
  },
  {
    name: "missing winning segment",
    stored: { ...terminalCase, candidate_result: { confidence: "medium" } },
    request: completionRequest,
  },
  {
    name: "missing representative time",
    stored: {
      ...terminalCase,
      candidate_result: { confidence: "medium", winningSegment: {} },
    },
    request: completionRequest,
  },
  {
    name: "low-result action paired with candidate status",
    stored: {
      ...terminalCase,
      turn_state: {
        nextAction: {
          kind: "present_low_result",
          resultId: terminalCase.candidate_result_id,
        },
      },
    },
    request: completionRequest,
  },
  {
    name: "medium-result action paired with rectifying status",
    stored: {
      ...lowTerminalCase,
      turn_state: {
        nextAction: {
          kind: "present_medium_result",
          resultId: terminalCase.candidate_result_id,
        },
      },
    },
    request: completionRequest,
  },
  {
    name: "candidate-saved action paired with rectifying status",
    stored: {
      ...lowTerminalCase,
      turn_state: {
        nextAction: {
          kind: "candidate_saved",
          resultId: terminalCase.candidate_result_id,
        },
      },
    },
    request: completionRequest,
  },
] as const;

for (const scenario of rejectedCompletions) {
  test(`rejects candidate completion with ${scenario.name}`, () => {
    assert.equal(candidateWorkingTime(scenario.stored, scenario.request), null);
  });
}
