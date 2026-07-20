import assert from "node:assert/strict";
import test from "node:test";
import {
  createConversationalRectificationController,
} from "../src/hooks/use-conversational-rectification.ts";
import {
  CONVERSATIONAL_RECTIFICATION_UNAVAILABLE,
  ConversationalRectificationRequestError,
} from "../src/lib/conversational-rectification/client.ts";
import type {
  ConversationalRectificationCommand,
  ConversationalRectificationTurn,
} from "../src/lib/conversational-rectification/contracts.ts";

const caseId = "00000000-0000-4000-8000-000000000811";
const actionIds = [
  "00000000-0000-4000-8000-000000000812",
  "00000000-0000-4000-8000-000000000813",
  "00000000-0000-4000-8000-000000000814",
  "00000000-0000-4000-8000-000000000815",
];

function activeTurn(turnVersion = 2): ConversationalRectificationTurn {
  return {
    caseId,
    journeyProtocol: "conversational-evidence-v3",
    status: "active",
    turnVersion,
    narrative: "候选仍需历史事件验证。",
    candidate: {
      status: "pending_validation",
      representativeTime: "05:18",
      rangeStart: "05:10",
      rangeEnd: "05:26",
    },
    technicalReceipt: {
      calculationVersion: "rectification-technical-v1",
      stableLayers: ["D1"],
      sensitiveLayers: ["D9", "D10"],
      candidateDifferenceRefs: ["consult-d9", "consult-d10"],
    },
    evidenceRequest: {
      domains: ["relationship", "career"],
      datePrecision: "month_preferred",
      freeTextAllowed: true,
    },
    evidenceRecap: [],
    actions: ["answer", "pause", "abandon"],
    pendingConsultationQuestion: null,
  };
}

function idFactory() {
  const ids = [...actionIds];
  return () => ids.shift() ?? assert.fail("unexpected action id allocation");
}

test("controller admits only one in-flight mutation and clears text only after success", async () => {
  const commands: ConversationalRectificationCommand[] = [];
  let resolveRequest: ((turn: ConversationalRectificationTurn) => void) | undefined;
  const request = new Promise<ConversationalRectificationTurn>((resolve) => {
    resolveRequest = resolve;
  });
  const controller = createConversationalRectificationController({
    initialTurn: activeTurn(),
    createActionId: idFactory(),
    send: async (command) => {
      commands.push(command);
      return request;
    },
  });
  controller.setDraft("2021 年 7 月开始第一份工作");

  const answer = controller.answer("career");
  const duplicate = controller.answer("career");
  const pause = controller.pause();

  assert.equal(controller.getSnapshot().pending, true);
  assert.equal(controller.getSnapshot().draft, "2021 年 7 月开始第一份工作");
  assert.equal(commands.length, 1);
  resolveRequest?.(activeTurn(3));
  await Promise.all([answer, duplicate, pause]);

  assert.equal(commands.length, 1);
  assert.equal(controller.getSnapshot().pending, false);
  assert.equal(controller.getSnapshot().draft, "");
  assert.equal(controller.getSnapshot().turn?.turnVersion, 3);
});

test("controller preserves the exact draft and stable action id across failures", async () => {
  const commands: ConversationalRectificationCommand[] = [];
  const controller = createConversationalRectificationController({
    initialTurn: activeTurn(),
    createActionId: idFactory(),
    send: async (command) => {
      commands.push(command);
      throw new ConversationalRectificationRequestError(
        502,
        null,
        CONVERSATIONAL_RECTIFICATION_UNAVAILABLE,
      );
    },
  });
  controller.setDraft("2021 年 7 月毕业，具体日期不确定");

  await assert.rejects(controller.answer("education"));
  await assert.rejects(controller.answer("education"));

  const snapshot = controller.getSnapshot();
  assert.equal(snapshot.draft, "2021 年 7 月毕业，具体日期不确定");
  assert.equal(snapshot.error, CONVERSATIONAL_RECTIFICATION_UNAVAILABLE);
  assert.equal(commands.length, 2);
  assert.equal(commands[0]?.actionId, commands[1]?.actionId);
});

test("a stale answer resumes the latest turn and returns recovered state without clearing text", async () => {
  const commands: ConversationalRectificationCommand[] = [];
  const recovered = activeTurn(5);
  const controller = createConversationalRectificationController({
    initialTurn: activeTurn(2),
    createActionId: idFactory(),
    send: async (command) => {
      commands.push(command);
      if (command.type === "answer") {
        throw new ConversationalRectificationRequestError(409, "stale_turn", "请加载最新进度后再试。");
      }
      assert.equal(command.type, "resume");
      return recovered;
    },
  });
  controller.setDraft("2022 年 3 月搬到另一座城市");

  const result = await controller.answer("relocation");

  assert.deepEqual(result, recovered);
  assert.deepEqual(commands.map((command) => command.type), ["answer", "resume"]);
  assert.equal(controller.getSnapshot().turn?.turnVersion, 5);
  assert.equal(controller.getSnapshot().draft, "2022 年 3 月搬到另一座城市");
  assert.equal(controller.getSnapshot().error, "");
});

test("a changed payload receives a different action id after a failed send", async () => {
  const commands: ConversationalRectificationCommand[] = [];
  const controller = createConversationalRectificationController({
    initialTurn: activeTurn(),
    createActionId: idFactory(),
    send: async (command) => {
      commands.push(command);
      throw new Error("offline");
    },
  });

  controller.setDraft("2021 年 7 月毕业");
  await assert.rejects(controller.answer("education"));
  controller.setDraft("2022 年 3 月搬家");
  await assert.rejects(controller.answer("relocation"));

  assert.notEqual(commands[0]?.actionId, commands[1]?.actionId);
});
